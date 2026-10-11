#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only both-direction simulation for the item-4 note-lineage allowance (validation, 2026-10-11).

(a) validate_data_contract 3d  CONCEPT_MIXED_DISCLOSURE_INTO_DART : current rule vs proposed rule over the
    whole PL_breakdown_provenance sidecar x PL_breakdown published items.
(b) validate_master_tables 2b  ZERO_LEGS : current all-None test vs proposed (item 4 not counted as a leg).

Prints closed / newly broken / unchanged sets.  Writes nothing except the --out text file.
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/validation_item4_20261011/sim_item4_lineage.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as G  # noqa: E402
import validate_master_tables as V  # noqa: E402

HOW_ALLOW = {"fs_note_csm_amort": frozenset({4})}


def published_items():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    vals = {}
    for r in rows:
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        code, q = r.get("원보험사코드"), r.get("공시분기")
        if not (code and q):
            continue
        blk = "contract_notes" if it in G._PL_CONTRACT_NOTE_ITEMS else "income_statement"
        vals.setdefault((code, q, blk), {})[it] = r.get("값")
    return {k: sorted(i for i, v in d.items() if v is not None) for k, d in vals.items()
            if any(v is not None for v in d.values())}


def exempt_items(c):
    out = set()
    how_cell = c.get("resolution")
    if c.get("item_block") != "contract_notes":
        return out
    for sf in c.get("source_files") or []:
        how = sf.get("how")
        allow = HOW_ALLOW.get(how)
        if allow is None or how != how_cell:
            continue
        if not (sf.get("page") or sf.get("pages")) or sf.get("printed") in (None, ""):
            continue
        out |= {int(i) for i in sf.get("items") or [] if str(i).isdigit()} & allow
    return out


def sec3d(side, pub_items, proposed):
    allowed = set(G.PL_DISCLOSURE_ITEM_NOS)
    red = {}
    for c in side.get("cells") or []:
        key = (c.get("company_code"), c.get("quarter"), c.get("item_block"))
        pub = set(pub_items.get(key) or ())
        if not pub:
            continue
        disc = set()
        if (c.get("source_id") == G.PL_DISCLOSURE_SOURCE_ID
                or G.source_id_for_lineage(c.get("source_file")) == G.PL_DISCLOSURE_SOURCE_ID):
            disc |= pub
        for sf in c.get("source_files") or []:
            if G.source_id_for_lineage(sf.get("file")) == G.PL_DISCLOSURE_SOURCE_ID:
                disc |= {int(i) for i in (sf.get("items") or []) if str(i).isdigit()}
        if proposed:
            disc -= exempt_items(c)
        disc &= pub
        bad = sorted(disc - allowed)
        if bad:
            red[key] = bad
    return red


def zleg_run(pl_idx, src):
    import contextlib, io
    na = {}
    with contextlib.redirect_stdout(io.StringIO()):
        _p, _f, _s, zrows, _z0 = V._check_pl_bridge(pl_idx, *V.load_pl_extra_lob(V.PL_PATH), source_ids=src, src_na_out=na)
    return {(c, q) for c, q, *_r in zrows}, na


def zleg_sim():
    """current code on live data  vs  current code on data where item 4 is hidden in DISCLOSURE-lineage buckets whose
    other 9 legs are all None  ==  proposed rule on live data (the proposed rule only changes that all-None test)."""
    import copy
    pl = V.load_long(V.PL_PATH)
    src = V.pl_cell_source_ids()
    cur_flag, cur_na = zleg_run(pl, src)
    other = [k for k in ["생명장기원수손익", "원수위험조정변동", "원수예실차", "기타생명장기원수손익", "생명장기재보험손익",
                         "재보험CSM상각", "재보험위험조정변동", "재보험예실차", "기타생명장기재보험손익"]]
    pl2 = copy.deepcopy(pl)
    hidden = []
    for key, m in pl2.items():
        if src.get(key) == "DISCLOSURE" and m.get("원수CSM상각") is not None and all(m.get(k) is None for k in other):
            m["원수CSM상각"] = None
            hidden.append(key)
    new_flag, new_na = zleg_run(pl2, src)
    return cur_flag, cur_na, new_flag, new_na, hidden


def main():
    side = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
    pub = published_items()
    cur = sec3d(side, pub, proposed=False)
    new = sec3d(side, pub, proposed=True)
    print(f"(a) 3d CONCEPT_MIXED_DISCLOSURE_INTO_DART  current RED cells={len(cur)}  proposed RED cells={len(new)}")
    closed = sorted(set(cur) - set(new))
    broken = sorted(set(new) - set(cur))
    print(f"    closed ({len(closed)}): items {sorted({tuple(cur[k]) for k in closed})}")
    for k in closed:
        print("      -", k, cur[k])
    print(f"    newly broken ({len(broken)}): {broken}")
    print(f"    still RED ({len(new)}): {sorted(new.items())}")

    cf, cn, nf, nn, hidden = zleg_sim()
    print(f"(b) 2b ZERO_LEGS  current flag={len(cf)} src_na zleg={cn.get('zleg')} legcov={cn.get('legcov')}  "
          f"proposed flag={len(nf)} src_na zleg={nn.get('zleg')} legcov={nn.get('legcov')}  (item-4-hidden buckets={len(hidden)})")
    print(f"    closed ({len(cf - nf)}): {sorted(cf - nf)}")
    print(f"    newly broken ({len(nf - cf)}): {sorted(nf - cf)}")
    print(f"    still flagged ({len(nf)}): {sorted(nf)}")
    # sidecar blocks carrying the how, and every other cell with 'how' not in the allow-list but item 4
    hows = {}
    for c in side.get("cells") or []:
        for sf in c.get("source_files") or []:
            hows[sf.get("how")] = hows.get(sf.get("how"), 0) + 1
    print("    sidecar how histogram:", hows)
    print("    published item-4 rows in contract_notes with DISCLOSURE lineage but NOT fs_note:")
    n = 0
    for k, items in pub.items():
        if 4 in items and k[2] == "contract_notes":
            c = [x for x in side["cells"] if (x["company_code"], x["quarter"], x["item_block"]) == k]
            if c and not exempt_items(c[0]) and (c[0].get("source_id") == "DISCLOSURE"):
                n += 1
                print("      ", k, c[0].get("resolution"))
    print("      count", n)


if __name__ == "__main__":
    main()
