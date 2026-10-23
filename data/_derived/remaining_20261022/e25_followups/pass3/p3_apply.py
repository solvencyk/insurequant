#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level applier (parser/ifrs17, ticket 20261024T0600Z neighbor stale cells sweep pass 3, 2026-10-24).  Derived from the pass2 applier (pass2/p2_apply.py <- e25_apply.py <- e23 ABL applier <- e21_apply.py);
see make_apply_p3.py for the exact substitutions.  Input = p3_plan.json (apply_contract) produced by p01_build_plan.py and re-read independently by x01_verify_p3.py.

Writes (only these, each guarded + backed up under pass3/backup_before_apply/; the git HEAD copies are the second backup):
  data/_gold/user_pl_cells.json            +new set entries, in-place replaced set entry (stale static derived gold), +null_dangi / -null_dangi seam cells
  PL_breakdown.json                        ONLY the cells where a REAL build_pl() run (temp copy) with the new gold differs from the same run with the live gold (cell level: 값 and 값_당분기)
  PL_breakdown_provenance.json             blocks whose emitter output changes (sandbox copy of scripts/emit_pl_provenance.py; never imported) + one merge note key
  tests/test_rule_coverage_manifest.py     GOLD_OVERLAY_CENSUS (PL tuple)
  (gold_overlay_ledger.json only if a pinned cell vanishes: none planned)  No CSM file is written.

  --snapshot-drift   read-only: live masters vs a fresh build with the LIVE gold (all companies) -> pass3/drift_before.json (run BEFORE --apply)
  --check            read-only plan + post-condition checks (+ identity residuals, headline table -> p3_apply_report.txt)
  --out-dir DIR      write post-apply files under DIR (repo untouched)
  --apply            write the repo files
  --verify           read-only: a fresh build from the LIVE gold == the LIVE masters except the snapshot drift; planned cells equal
  --revert --apply   restore the backups (only while the live files still carry the post-apply hashes)
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OLD_EV = ROOT / "data" / "_derived" / "kyobo_pl_restate_dryrun_20261021"
CSM_EV = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass3"
BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass3" / "backup_before_apply"
TMP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/p3_tmp")
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")
for p in (str(ROOT / "scripts"), str(ROOT), str(OLD_EV), str(EV)):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ak = _load(CSM_EV / "apply_kr0073_fix.py", "ak_helpers")      # JsonFile (exact-format JSON), write_atomic, sha
import sim_pl_builder as S  # noqa: E402  (real build_pl() on a temp copy; repo untouched)

PIN_REL = "data/_gold/gold_overlay_ledger.json"
F = {"PL": "PL_breakdown.json", "GOLD": "data/_gold/user_pl_cells.json", "PROV": "PL_breakdown_provenance.json", "PIN": PIN_REL,
     "CSM": "CSM_waterfall.json", "CGOLD": "data/_gold/user_csm_cells.json", "CPROV": "CSM_waterfall_provenance.json"}
TEST_REL = "tests/test_rule_coverage_manifest.py"
PL_MASTER_SRC = "data/dart/viz/pl_breakdown_master.json"
DIAG_REL = "data/dart/viz/csm_waterfall_master_diag.json"
TOL = 5e-4
PLAN = json.loads((EV / "p3_plan.json").read_text(encoding="utf-8"))
C = PLAN["apply_contract"]
HELD = {(h["code"], h["quarter"]) for h in C["held"]}
ADOPTED = [(b["code"], b["quarter"]) for b in PLAN["buckets"] if b.get("cells") and (b["code"], b["quarter"]) not in HELD]
CODES = sorted({c for c, _q in ADOPTED})
CSM_CODES = sorted({cb["code"] for cb in PLAN["csm_buckets"]})
CPROV_CLEARED = []
STALE_NONE_OK = set()
MERGE_NOTE_KEY = "merge_note_20261024_pass3_neighbor_stale_cells"
_NEW_N, _REP_N = len(C["gold_new"]), len(C["gold_replace"])
MERGE_NOTE = ("ticket 20261024T0600Z (neighbor stale cells sweep pass 3; ABL KR0070 2025.3Q-2026.2Q items 5/7/9/10/12 (current-period column of each quarter's own filing = latest), 동양 KR0087 2024.2Q reinsurance "
              "items 9/10/11/12 (FY2025 half-year prior-period analysis tables), NH농협손보 KR0032 2023.1Q items 20-24 + 2023.2Q items 22-24 / OCI 25-32 (FY2024 Q1 / half-year separate statement prior cumulative column)): "
              "PL cells refreshed to the latest comparative / latest print (separate basis) via data/_gold/user_pl_cells.json (%d new set cells + %d stale static derived-gold cell replaced in place; null_dangi +%d / -%d "
              "single-quarter cells; no ledger pins). Blocks that changed are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. "
              "Evidence data/_derived/remaining_20261022/e25_followups/pass3/" % (_NEW_N, _REP_N, len(C["null_dangi_add"]), len(C["null_dangi_remove"])))
CSM_NOTE_KEY = None
CSM_NOTE = None
SUBS = [
    ('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")'),
    ('PL_SRC = ROOT / "PL_breakdown.json"', 'PL_SRC = Path(os.environ["EMIT_PL_SRC"])'),
    ('PL_OVR = ROOT / "data" / "_gold" / "user_pl_cells.json"', 'PL_OVR = Path(os.environ["EMIT_PL_OVR"])'),
    ('PL_OUT = ROOT / "PL_breakdown_provenance.json"', 'PL_OUT = Path(os.environ["EMIT_PL_OUT"])'),
]


def rkey(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def load_json(rel_or_path):
    p = Path(rel_or_path)
    if not p.is_absolute():
        p = ROOT / rel_or_path
    return json.loads(p.read_text(encoding="utf-8"))


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOL


PLANNED = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}
PLANNED_C = {(e["code"], e["item"], e["quarter"]): e for e in C["csm_gold_new"] + C["csm_gold_replace"] + C["csm_gold_remove"]}


def guard_live_matches_plan(live):
    cur = {rkey(r): r for r in live["PL"].obj}
    gold_by = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in live["GOLD"].obj["set"]}
    nd = {tuple(x) for x in live["GOLD"].obj["null_dangi"]["cells"]}
    sd = {(x[0], x[1], int(x[2])) for x in live["GOLD"].obj["set_dangi"]["cells"]}
    cgold_by = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in live["CGOLD"].obj["set"]}
    ccur = {rkey(r): r for r in live["CSM"].obj}
    bad = []
    for e in C["gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        r = cur.get(k)
        if r is None:
            bad.append(("PL row missing", k))
        elif not same(r.get("값"), e["was"]):
            bad.append(("PL expected old value", k, e["was"], r.get("값")))
        if k in gold_by:
            bad.append(("PL gold already has", k))
    for e in C["gold_replace"]:
        k = (e["code"], e["item"], e["quarter"])
        ge = gold_by.get(k)
        if ge is None:
            bad.append(("PL gold entry missing", k))
            continue
        if ge != e["old_entry"]:
            bad.append(("PL gold entry moved since the plan", k))
        r = cur.get(k)
        if r is None or not same(r.get("값"), e["was"]):
            bad.append(("PL master cell != old gold value", k, e["was"], None if r is None else r.get("값")))
    for c, q, i in C["null_dangi_add"]:
        if (c, q, i) in nd or (c, q, i) in sd:
            bad.append(("null_dangi_add: dangi list already has", (c, q, i)))
    for c, q, i, v, s in C["set_dangi_add"]:
        if (c, q, i) in nd or (c, q, i) in sd:
            bad.append(("set_dangi_add: dangi list already has", (c, q, i)))
    for c, q, i in C["null_dangi_remove"]:
        if (c, q, i) not in nd:
            bad.append(("null_dangi_remove: pin missing", (c, q, i)))
    for c, q, i in C["set_dangi_remove"]:
        if (c, q, i) not in sd:
            bad.append(("set_dangi_remove: pin missing", (c, q, i)))
    for e in C["csm_gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        r = ccur.get(k)
        if r is None:
            bad.append(("CSM row missing", k))
        elif not same(r.get("값"), e["was"]):
            bad.append(("CSM expected old value", k, e["was"], r.get("값")))
        if k in cgold_by:
            bad.append(("CSM gold already has", k))
    for e in C["csm_gold_replace"] + C["csm_gold_remove"]:
        k = (e["code"], e["item"], e["quarter"])
        ge = cgold_by.get(k)
        if ge is None or ge != e["old_entry"]:
            bad.append(("CSM gold entry missing/moved", k))
    for e in C.get("drift_fix", []):
        k = (e["code"], e["item"], e["quarter"])
        r = cur.get(k)
        if r is None or not same(r.get("값"), e["live_value"]):
            bad.append(("drift_fix: live value != plan", k, e["live_value"], None if r is None else r.get("값")))
        if k in gold_by:
            bad.append(("drift_fix: the cell has a gold entry", k))
    if bad:
        raise SystemExit(f"ABORT: live files moved since the plan was made (concurrent session?) or overlap: {bad[:6]} ... ({len(bad)})")


def build_gold(live_gold):
    g = copy.deepcopy(live_gold)
    idx = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): i for i, e in enumerate(g["set"])}
    for e in C["gold_replace"]:
        ent = g["set"][idx[(e["code"], e["item"], e["quarter"])]]
        ent["값"], ent["was"], ent["note"] = e["value"], e["was"], e["note"]
    for e in C["gold_new"]:
        g["set"].append({"원보험사코드": e["code"], "항목번호": e["item"], "공시분기": e["quarter"], "값": e["value"], "was": e["was"], "note": e["note"]})
    nd, sd = g["null_dangi"], g["set_dangi"]
    rm_n = {(c, q, i) for c, q, i in C["null_dangi_remove"]}
    nd["cells"] = [x for x in nd["cells"] if (x[0], x[1], int(x[2])) not in rm_n]
    for c, q, i in C["null_dangi_add"]:
        nd["cells"].append([c, q, i])
    if C["null_dangi_add"] or C["null_dangi_remove"]:
        assert "_doc_p3_20261024" not in nd
        nd["_doc_p3_20261024"] = ("2026-10-24 ticket 20261024T0600Z (parser/ifrs17, pass 3). REMOVED KR0070 2025.3Q item 5: with the corrected cumulative 7,271 (FY2025_Q3 current column) minus the 2025.2Q cumulative 4,605 the single quarter "
                                  "2,666 equals the 3-month column printed in the FY2025_Q3 report, so the builder derivation is right again. The item 7 blank of the same quarter is KEPT: the corrected derivation (-5,374.023) differs from the "
                                  "value implied by the printed 3-month cells (-5,372.023) by exactly 2.0 = the item 6 rounding noise between the FY2026_Q2 comparative and the FY2025_Q3 report (item 6 single -3,001 against printed -3,003). "
                                  "ADDED KR0087 2024.2Q and 2024.3Q item 11: the cumulatives of 2024.1Q (3,805), 2024.3Q (-479) and 2024.4Q (5,758) are the printed 재보험계약의 보험서비스결과 totals (= item 8), not the 예실차, so "
                                  "the difference of two cumulatives is meaningless (2024.2Q after this load: 14,273 - 3,805; 2024.3Q: -479 - 14,273). Blank beats wrong; the 2024.3Q detail is not printed in any filing.")
    for c, q, i, v, src in C["set_dangi_add"]:
        sd["cells"].append([c, q, i, v, src])
    rm_s = {(c, q, i) for c, q, i in C["set_dangi_remove"]}
    sd["cells"] = [x for x in sd["cells"] if (x[0], x[1], int(x[2])) not in rm_s]
    return g


def build_cgold(live_cgold):
    g = copy.deepcopy(live_cgold)
    idx = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): i for i, e in enumerate(g["set"])}
    for e in C["csm_gold_replace"]:
        ent = g["set"][idx[(e["code"], e["item"], e["quarter"])]]
        ent["값"], ent["was"], ent["why"] = e["value"], e["was"], e["why"]
    rm_c = {(e["code"], e["item"], e["quarter"]) for e in C["csm_gold_remove"]}
    n0 = len(g["set"])
    g["set"] = [x for x in g["set"] if (x["원보험사코드"], x["항목번호"], x["공시분기"]) not in rm_c]
    if n0 - len(g["set"]) != len(rm_c):
        raise SystemExit("ABORT: CSM gold removal did not hit every planned entry")
    for e in C["csm_gold_new"]:
        g["set"].append({"원보험사코드": e["code"], "항목번호": e["item"], "공시분기": e["quarter"], "값": e["value"], "was": e["was"], "why": e["why"]})
    if C["csm_gold_remove"]:
        g["_doc_e23_kr0070_20261023"] = ("2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3, owner 2026-10-23 approval): chain-forced owner-gold entries REMOVED (not replaced) because the approved value equals the CSM builder source "
                                         "value (a replaced entry would be a masked gold cell that needs a ledger pin). Removed entries (code, item, quarter, gold value, was, why verbatim): "
                                         + " || ".join("%s %s %s: gold %s, was %s, why 「%s」 -> builder value %s" % (e["code"], e["item"], e["quarter"], e["old_entry"]["값"], e["old_entry"]["was"], e["old_entry"]["why"], e["value"])
                                                       for e in C["csm_gold_remove"]))
    return g


def simulate_rows(gold_obj, tag):
    tmpdir = TMP / "tmp_apply"
    tmpdir.mkdir(parents=True, exist_ok=True)
    gp, mp = tmpdir / f"gold_{tag}.json", tmpdir / f"master_{tag}.json"
    gp.write_text(json.dumps(gold_obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    sim_rows, _n = S.simulate(gp, mp)
    for p in (gp, mp):
        try:
            p.unlink()
        except OSError:
            pass
    return sim_rows


def simulate_csm(cgold_obj, master_raw, tag):
    tmpdir = TMP / "tmp_apply"
    tmpdir.mkdir(parents=True, exist_ok=True)
    gp, mp = tmpdir / f"cgold_{tag}.json", tmpdir / f"cmaster_{tag}.json"
    gp.write_text(json.dumps(cgold_obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    mp.write_bytes(master_raw)
    brm = ak.load_brm()
    brm.CSM_OVR, brm.CSM_OUT = gp, mp
    brm.build_csm()
    rows = json.loads(mp.read_text(encoding="utf-8"))
    for p in (gp, mp):
        try:
            p.unlink()
        except OSError:
            pass
    return rows


def drift_vs_live(live_rows, sim_rows):
    sim_by = {rkey(r): r for r in sim_rows}
    if len(sim_rows) != len(live_rows):
        raise SystemExit(f"ABORT: builder row count {len(sim_rows)} != live {len(live_rows)}")
    out = []
    for r in live_rows:
        s = sim_by.get(rkey(r))
        if s is None:
            raise SystemExit(f"ABORT: {rkey(r)} missing from the builder simulation")
        if (r["값"], r.get("값_당분기")) != (s["값"], s.get("값_당분기")):
            out.append(rkey(r))
    return out


def build_master(live_rows, base_rows, new_rows_sim):
    """Cell-level: delta = cells where the sim with the NEW gold differs from the sim with the LIVE gold; those cells (both 값 and 값_당분기) are taken from the new sim."""
    base_by = {rkey(r): r for r in base_rows}
    new_by = {rkey(r): r for r in new_rows_sim}
    if set(base_by) != set(new_by):
        raise SystemExit("ABORT: base and new builder simulations have different row sets")
    delta = {k for k in base_by if (base_by[k]["값"], base_by[k].get("값_당분기")) != (new_by[k]["값"], new_by[k].get("값_당분기"))}
    out, val_changed, dangi_changed, pre_drift_on_delta = [], [], [], []
    for r in live_rows:
        k = rkey(r)
        if k in delta:
            s, b = new_by[k], base_by[k]
            if (r["값"], r.get("값_당분기")) != (b["값"], b.get("값_당분기")) and (r["값"], r.get("값_당분기")) != (s["값"], s.get("값_당분기")):
                pre_drift_on_delta.append((k, r["값"], r.get("값_당분기"), b["값"], b.get("값_당분기"), s["값"], s.get("값_당분기")))
            nr = dict(r)
            nr["값"], nr["값_당분기"] = s["값"], s["값_당분기"]
            out.append(nr)
            if nr["값"] != r["값"]:
                val_changed.append(k)
            if nr["값_당분기"] != r.get("값_당분기"):
                dangi_changed.append(k)
        else:
            out.append(r)
    return out, delta, val_changed, dangi_changed, pre_drift_on_delta


def emitter_copy_is_current():
    src = (ROOT / "scripts" / "emit_pl_provenance.py").read_text(encoding="utf-8")
    for old, new in SUBS:
        if src.count(old) != 1:
            return False
        src = src.replace(old, new)
    return src == (OLD_EV / "emit_pl_provenance_sandbox_copy.py").read_text(encoding="utf-8")


def run_emitter(rows_sub, gold_obj, tag):
    d = TMP / "tmp_emit"
    d.mkdir(parents=True, exist_ok=True)
    src, gold, out = d / f"src_{tag}.json", d / f"gold_{tag}.json", d / f"prov_{tag}.json"
    src.write_text(json.dumps(rows_sub, ensure_ascii=False), encoding="utf-8", newline="\n")
    gold.write_text(json.dumps(gold_obj, ensure_ascii=False), encoding="utf-8", newline="\n")
    if out.exists():
        out.unlink()
    env = dict(os.environ, EMIT_PL_SRC=str(src), EMIT_PL_OVR=str(gold), EMIT_PL_OUT=str(out), PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, str(OLD_EV / "emit_pl_provenance_sandbox_copy.py")], cwd=str(ROOT), env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    (d / f"emit_{tag}.log").write_text((p.stdout or "") + "\n--- stderr ---\n" + (p.stderr or ""), encoding="utf-8", newline="\n")
    if p.returncode != 0 or not out.exists():
        raise SystemExit(f"ABORT: sandbox emitter failed (rc={p.returncode}), see {d / f'emit_{tag}.log'}")
    return json.loads(out.read_text(encoding="utf-8"))


def build_prov(live_prov, emit_new, emit_live):
    """replace the blocks whose emitter output changes, INSERT the blocks that appear (position = right after their predecessor in the emitter order)"""
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_new["cells"]}
    el = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_live["cells"]}
    new = copy.deepcopy(live_prov)
    lk = {(c["company_code"], c["quarter"], c["item_block"]): i for i, c in enumerate(new["cells"])}
    targets = sorted(k for k in ek if el.get(k) != ek[k])
    live_not_equal_emit, inserted = [], []
    order = [(c["company_code"], c["quarter"], c["item_block"]) for c in emit_new["cells"]]
    for k in targets:
        if k in lk:
            if live_prov["cells"][lk[k]] != el.get(k):
                live_not_equal_emit.append(k)
            new["cells"][lk[k]] = ek[k]
        else:
            if k in el:
                raise SystemExit(f"ABORT: block {k} is in the live emitter output but not in the live sidecar")
            pos = order.index(k)
            pred = next((order[j] for j in range(pos - 1, -1, -1) if order[j] in lk), None)
            ins = (lk[pred] + 1) if pred is not None else len(new["cells"])
            new["cells"].insert(ins, ek[k])
            lk = {(c["company_code"], c["quarter"], c["item_block"]): i for i, c in enumerate(new["cells"])}
            inserted.append((k, ins))
    if MERGE_NOTE_KEY in new:
        raise SystemExit("ABORT: merge note key already present")
    new[MERGE_NOTE_KEY] = MERGE_NOTE
    return new, targets, live_not_equal_emit, inserted


def build_cprov(live_cprov, new_cgold):
    if not (C["csm_gold_new"] or C["csm_gold_replace"] or C["csm_gold_remove"]):
        return copy.deepcopy(live_cprov), [], []          # no CSM cell in this batch: the CSM sidecar stays byte-identical
    new = copy.deepcopy(live_cprov)
    flagged = []
    have = {(e["code"], e["quarter"]) for e in C["csm_gold_new"] + C["csm_gold_replace"]}
    for c in new["cells"]:
        if c["item_block"] == "csm_waterfall" and (c["company_code"], c["quarter"]) in have and not c.get("owner_override"):
            c["owner_override"] = True
            flagged.append((c["company_code"], c["quarter"]))
    # blocks whose last gold entry was removed no longer carry an owner override
    remaining = {(x["원보험사코드"], x["공시분기"]) for x in new_cgold["set"]}
    for e in C["csm_gold_remove"]:
        pair = (e["code"], e["quarter"])
        if pair in remaining:
            continue
        for c in new["cells"]:
            if c["item_block"] == "csm_waterfall" and (c["company_code"], c["quarter"]) == pair and c.get("owner_override"):
                del c["owner_override"]
                CPROV_CLEARED.append(pair)
    if CSM_NOTE_KEY in new:
        raise SystemExit("ABORT: CSM merge note key already present")
    new[CSM_NOTE_KEY] = CSM_NOTE
    # every (company, quarter) with gold must have a csm_waterfall block
    blocks = {(c["company_code"], c["quarter"]) for c in new["cells"] if c["item_block"] == "csm_waterfall"}
    missing = sorted(have - blocks)
    return new, flagged, missing


def census(overlay, gold_obj, pin_obj, rows_src):
    import validate_data_contract as G
    rows = G.gold_overlay_census(overlay, gold_obj["set"], rows_src)
    masked = [r for r in rows if r["verdict"] in G._GOLD_MASKED]
    pins = pin_obj.get("entries", {})
    unpinned = [r["key"] for r in masked if r["key"] not in pins]
    drift = [r["key"] for r in rows if r["key"] in pins and r["verdict"] not in G._GOLD_MASKED]
    seen = {r["key"] for r in rows}
    stale = [k for k in pins if k.startswith(overlay + "|") and k not in seen]
    return (len(rows), len(masked)), unpinned, drift, stale


def tax22_sets(rows):
    import validate_master_tables as V
    _p, fails, _s = V._check_tax22_crosscheck(rows, quiet=True)
    on = {(f[0], f[1]) for f in fails}
    orig = V._tax22_prior_tier1
    V._tax22_prior_tier1 = lambda *a, **k: None
    try:
        _p2, fails2, _s2 = V._check_tax22_crosscheck(rows, quiet=True)
    finally:
        V._tax22_prior_tier1 = orig
    return on, {(f[0], f[1]) for f in fails2}


DECL_RE = re.compile(r'^(GOLD_OVERLAY_CENSUS = \{"CSM": )\((\d+), (\d+)\)(, "PL": )\((\d+), (\d+)\)(\})$', re.M)
def new_test_bytes(raw, census_old, census_new, tax_off_new, tax_off_old, kyobo):
    crlf = b"\r\n" in raw
    s = raw.decode("utf-8").replace("\r\n", "\n")
    ms = list(DECL_RE.finditer(s))
    if len(ms) != 1:
        raise SystemExit(f"ABORT: GOLD_OVERLAY_CENSUS declaration found {len(ms)} times in {TEST_REL}")
    m = ms[0]
    if ((int(m.group(2)), int(m.group(3))), (int(m.group(5)), int(m.group(6)))) != census_old:
        raise SystemExit(f"ABORT: declared census {m.group(0)} != expected old {census_old}")
    comment = ("# 2026-10-24 ticket 20261024T0600Z (parser/ifrs17 neighbor stale cells sweep pass 3: ABL 2025.3Q-2026.2Q items 5/9/10 and derived 7/12, 동양 2024.2Q reinsurance items 9-12, "
               "NH농협손보 2023.1Q/2Q income-statement tail items 20-24 and 2023.2Q OCI 25-32): "
               "CSM gold %d->%d cells, masked %d->%d; PL gold %d->%d cells, masked %d->%d (no new pins).\n" % (census_old[0][0], census_new[0][0], census_old[0][1], census_new[0][1],
                                                                                                           census_old[1][0], census_new[1][0], census_old[1][1], census_new[1][1]))
    s = s[:m.start()] + comment + m.group(1) + "(%d, %d)" % census_new[0] + m.group(4) + "(%d, %d)" % census_new[1] + m.group(7) + s[m.end():]
    if tax_off_new != tax_off_old:
        raise SystemExit("ABORT: the TAX22 latest-comparative-only bucket set moved in this batch (not expected: items 22/23/24 are untouched); regenerate _TAX22_LATEST_COMPARATIVE_ONLY by hand")
    out = s.replace("\n", "\r\n") if crlf else s
    return out.encode("utf-8")


IDENT = [
    ("20-(1+17)", lambda v: _d(v, 20, (1, 17))),
    ("22-(20+21)", lambda v: _d(v, 22, (20, 21))),
    ("|22-24|-|23|", lambda v: None if any(v.get(i) is None for i in (22, 23, 24)) else abs(abs(v[22] - v[24]) - abs(v[23]))),
    ("31-(24+25)", lambda v: _d(v, 31, (24, 25))),
    ("25-(26+27+28+29+30+32)", lambda v: None if v.get(25) is None or v.get(27) is None else v[25] - sum((v.get(i) or 0) for i in (26, 27, 28, 29, 30, 32))),
    ("17-(18+19)", lambda v: _d(v, 17, (18, 19))),
    ("3-(4+5+6+7)", lambda v: _d(v, 3, (4, 5, 6, 7))),
    ("8-(9+10+11+12)", lambda v: _d(v, 8, (9, 10, 11, 12))),
]


def _d(v, a, bs):
    if v.get(a) is None or any(v.get(b) is None for b in bs):
        return None
    return v[a] - sum(v[b] for b in bs)


def vec(rows_by, code, q):
    return {i: rows_by[(code, i, q)]["값"] for i in range(1, 33) if (code, i, q) in rows_by}


def identity_report(live_rows, new_rows):
    lb = {rkey(r): r for r in live_rows}
    nb = {rkey(r): r for r in new_rows}
    lines, worst = [], 0.0
    for code, q in ADOPTED:
        vo, vn = vec(lb, code, q), vec(nb, code, q)
        parts = []
        for name, f in IDENT:
            a, b = f(vo), f(vn)
            parts.append(f"{name}: {('-' if a is None else f'{a:+.3f}')} -> {('-' if b is None else f'{b:+.3f}')}")
            if b is not None:
                worst = max(worst, abs(b))
        lines.append(f"  {code} {q}: " + "; ".join(parts))
    return lines, worst


def headline_report(live_rows, new_rows, live_csm, new_csm, names):
    lb = {rkey(r): r for r in live_rows}
    nb = {rkey(r): r for r in new_rows}
    nm = {1: "보험손익", 17: "투자손익", 24: "당기순이익", 25: "기타포괄손익", 31: "총포괄손익"}
    f = lambda v: "blank" if v is None else f"{v / 100:,.2f}"  # noqa: E731
    lines = ["PL adopted buckets, 억원 (1억 = 100백만). 누계(값) before -> after | 단일분기(값_당분기) before -> after"]
    for code, q in ADOPTED:
        for it, name in nm.items():
            a, b = lb.get((code, it, q)), nb.get((code, it, q))
            if a is None or b is None:
                continue
            if a["값"] == b["값"] and a.get("값_당분기") == b.get("값_당분기"):
                continue
            lines.append(f"  {names.get(code, code)} {code} {q} {name:6s}: 누계 {f(a['값']):>12s} -> {f(b['값']):>12s} | 단일분기 {f(a.get('값_당분기')):>12s} -> {f(b.get('값_당분기')):>12s}")
    cl = {rkey(r): r for r in live_csm}
    cn = {rkey(r): r for r in new_csm}
    lines.append("CSM 기말(항목 6) / 상각(항목 5), 억원: before -> after")
    for cb in PLAN["csm_buckets"]:
        code, q = cb["code"], cb["quarter"]
        for it, name in ((6, "기말 CSM"), (5, "CSM 상각"), (1, "기초 CSM")):
            a, b = cl.get((code, it, q)), cn.get((code, it, q))
            if a is None or b is None or a["값"] == b["값"]:
                continue
            lines.append(f"  {names.get(code, code)} {code} {q} {name}: {a['값']:,.2f} -> {b['값']:,.2f} ({b['값'] - a['값']:+,.2f})")
    return lines


def plan_all():
    live = {k: ak.JsonFile(rel) for k, rel in F.items()}
    guard_live_matches_plan(live)
    new_gold = build_gold(live["GOLD"].obj)
    new_cgold = build_cgold(live["CGOLD"].obj)
    base_rows = simulate_rows(live["GOLD"].obj, "base")
    new_sim = simulate_rows(new_gold, "new")
    new_rows, delta, val_changed, dangi_changed, pre_drift_on_delta = build_master(live["PL"].obj, base_rows, new_sim)
    errs = []
    # drift_fix: hand-loaded live cells (not gold) -> the value a fresh build writes; guarded against the fresh build itself
    fix_keys = {(e["code"], e["item"], e["quarter"]): e for e in C.get("drift_fix", [])}
    base_by_fix = {rkey(r): r for r in base_rows}
    for k, e in fix_keys.items():
        if k in {(x["code"], x["item"], x["quarter"]) for x in C["gold_new"] + C["gold_replace"]}:
            errs.append(f"drift_fix {k} is also a planned gold cell")
        if not same(base_by_fix[k]["값"], e["fresh_value"]):
            errs.append(f"drift_fix {k}: fresh build value {base_by_fix[k]['값']} != plan {e['fresh_value']}")
        if base_by_fix[k].get("값_당분기") != next(r for r in live["PL"].obj if rkey(r) == k).get("값_당분기"):
            errs.append(f"drift_fix {k}: fresh 값_당분기 != live 값_당분기")
        if k in delta:
            errs.append(f"drift_fix {k} is inside the gold delta")
    if fix_keys:
        new_rows = [dict(r, **{"값": base_by_fix[rkey(r)]["값"], "값_당분기": base_by_fix[rkey(r)].get("값_당분기")}) if rkey(r) in fix_keys else r for r in new_rows]
    want = {k: e["value"] for k, e in PLANNED.items()}
    base_by = {rkey(r): r for r in base_rows}
    new_by = {rkey(r): r for r in new_sim}
    if set(val_changed) != set(want):
        errs.append(f"PL 값 changed set != plan set: only-in-sim {sorted(set(val_changed) - set(want))[:6]} only-in-plan {sorted(set(want) - set(val_changed))[:6]}")
    for k, e in PLANNED.items():
        if not same(base_by[k]["값"], e["was"]):
            errs.append(f"PL baseline build value {k}: {base_by[k]['값']} != was {e['was']}")
        if abs(new_by[k]["값"] - e["value"]) > 1e-9:
            errs.append(f"PL new build value {k}: {new_by[k]['값']} != plan {e['value']}")
    bad_codes = sorted({k[0] for k in delta} - set(CODES))
    if bad_codes:
        errs.append(f"PL delta touches other companies: {bad_codes}")
    # single quarters: every 값_당분기 that changes must be explained by the seam table
    exp = expected_dangi()
    unexpected = sorted(k for k in dangi_changed if k not in want and (k[0], k[1], k[2]) not in exp and not is_derived_follow(k, want))
    if unexpected:
        errs.append(f"PL 값_당분기 changed outside the seam plan: {unexpected[:10]} ({len(unexpected)})")
    mism = []
    for (c, i, q), ev in exp.items():
        got = new_by[(c, i, q)]["값_당분기"]
        if ev is None:
            if got is not None:
                mism.append(((c, i, q), ev, got))
        elif got is None or abs(got - ev) > 1e-6:
            mism.append(((c, i, q), ev, got))
    if mism:
        errs.append(f"PL new build 값_당분기 != planned on {len(mism)} cells: {mism[:8]}")
    for c, q, i in C["set_dangi_remove"]:
        pinned = next(float(x[3]) for x in live["GOLD"].obj["set_dangi"]["cells"] if x[0] == c and x[1] == q and int(x[2]) == i)
        got = new_by[(c, i, q)]["값_당분기"]
        if got is None or abs(got - pinned) > 1e-6:
            errs.append(f"removed set pin {(c, q, i)}: derived {got} != pinned {pinned}")
    for c, q, i in C["null_dangi_remove"]:
        if new_by[(c, i, q)]["값_당분기"] is None:
            errs.append(f"removed null pin {(c, q, i)}: the builder derives no single quarter")
    allowed_pre = []
    p3m = {(s_["code"], s_["item"], s_["quarter"]): s_["printed_3m"]["value"] for s_ in PLAN["seams"] if s_.get("printed_3m")}
    for x in pre_drift_on_delta:
        k = x[0]
        # live differs from the fresh baseline build (pre-existing hand blank) and the apply would write the NEW derivation: accepted only when it equals the printed 3-month column
        if k in p3m and x[6] is not None and abs(x[6] - p3m[k]) <= 1e-6 and x[5] == x[3]:
            allowed_pre.append((k, x[2], x[6], p3m[k]))
        elif k in STALE_NONE_OK and x[2] is None and x[1] == x[3] and x[4] is not None and x[6] is not None and _stale_none_ok(k, new_by):
            allowed_pre.append((k, x[2], x[6], "stale None filled by the derivation new cumulative - new previous-quarter cumulative"))
        else:
            errs.append(f"PL pre-existing live-vs-fresh-build drift on delta cell {x} (the apply would overwrite it)")
    # --- CSM
    cbase = simulate_csm(live["CGOLD"].obj, live["CSM"].raw, "base")
    cnew = simulate_csm(new_cgold, live["CSM"].raw, "new")
    cnew_rows, cdelta, cval, cdangi, cpre = build_master(live["CSM"].obj, cbase, cnew)
    cwant = {k: e["value"] for k, e in PLANNED_C.items()}
    cbase_by = {rkey(r): r for r in cbase}
    cnew_by = {rkey(r): r for r in cnew}
    if set(cval) != set(cwant):
        errs.append(f"CSM 값 changed set != plan set: only-in-sim {sorted(set(cval) - set(cwant))[:6]} only-in-plan {sorted(set(cwant) - set(cval))[:6]}")
    for k, e in PLANNED_C.items():
        if not same(cbase_by[k]["값"], e["was"]):
            errs.append(f"CSM baseline build value {k}: {cbase_by[k]['값']} != was {e['was']}")
        if abs(cnew_by[k]["값"] - e["value"]) > 1e-9:
            errs.append(f"CSM new build value {k}: {cnew_by[k]['값']} != plan {e['value']}")
    bad_c = sorted({k[0] for k in cdelta} - set(CSM_CODES))
    if bad_c:
        errs.append(f"CSM delta touches other companies: {bad_c}")
    if cpre:
        errs.append(f"CSM pre-existing drift on {len(cpre)} delta cells: {cpre[:4]}")
    # --- provenance
    if not emitter_copy_is_current():
        errs.append("the sandbox emitter copy no longer matches scripts/emit_pl_provenance.py")
    sub_new = [r for r in new_rows if r["원보험사코드"] in CODES]
    sub_live = [r for r in live["PL"].obj if r["원보험사코드"] in CODES]
    emit_new = run_emitter(sub_new, new_gold, "apply_new")
    emit_live = run_emitter(sub_live, live["GOLD"].obj, "apply_live")
    new_prov, prov_targets, prov_live_ne, prov_inserted = build_prov(live["PROV"].obj, emit_new, emit_live)
    new_cprov, cprov_flagged, cprov_missing = build_cprov(live["CPROV"].obj, new_cgold)
    if cprov_missing:
        errs.append(f"CSM provenance: gold (company, quarter) without a csm_waterfall block: {cprov_missing}")
    # --- ledger pins / census
    pin_obj = live["PIN"].obj
    cen_pl_old, un0, dr0, st0 = census("PL", live["GOLD"].obj, pin_obj, load_json(PL_MASTER_SRC))
    cen_pl_mid, un1, dr1, st1 = census("PL", new_gold, pin_obj, load_json(PL_MASTER_SRC))
    diag_rows = load_json(DIAG_REL)
    cen_c_old, cun0, cdr0, cst0 = census("CSM", live["CGOLD"].obj, pin_obj, diag_rows)
    cen_c_mid, cun1, cdr1, cst1 = census("CSM", new_cgold, pin_obj, diag_rows)
    replaced_keys = {f"PL|{e['code']}|{e['quarter']}|{e['item']}" for e in C["gold_replace"]} | {f"CSM|{e['code']}|{e['quarter']}|{e['item']}" for e in C["csm_gold_replace"] + C["csm_gold_remove"]}
    drop = sorted(set(dr1) | set(cdr1))
    if un1 or cun1 or st1 or cst1 or not set(drop) <= replaced_keys:
        errs.append(f"ledger: unpinned masked cells PL {un1} CSM {cun1} / stale pins {st1 + cst1} / drifting pins {drop} not all replaced cells")
    new_pin = copy.deepcopy(pin_obj)
    for k in drop:
        new_pin["entries"].pop(k)
    cen_pl_new, un2, dr2, st2 = census("PL", new_gold, new_pin, load_json(PL_MASTER_SRC))
    cen_c_new, cun2, cdr2, cst2 = census("CSM", new_cgold, new_pin, diag_rows)
    if un2 or dr2 or st2 or cun2 or cdr2 or cst2:
        errs.append(f"census after: unpinned PL {un2} CSM {cun2} drift {dr2 + cdr2} stale {st2 + cst2}")
    exp_pl = (cen_pl_old[0] + len(C["gold_new"]), None)
    if cen_pl_new[0] != exp_pl[0]:
        errs.append(f"PL census gold cells {cen_pl_new[0]} != expected {exp_pl[0]}")
    if cen_c_new[0] != cen_c_old[0] + len(C["csm_gold_new"]) - len(C["csm_gold_remove"]):
        errs.append(f"CSM census gold cells {cen_c_new[0]} != expected {cen_c_old[0] + len(C['csm_gold_new']) - len(C['csm_gold_remove'])}")
    # --- tests
    tax_on, tax_off = tax22_sets(new_rows)
    tax_on0, tax_off0 = tax22_sets(live["PL"].obj)
    if tax_on:
        errs.append(f"TAX22 FAIL with the vintage branch on the candidate master: {sorted(tax_on)[:6]}")
    kyobo = [("교보생명보험", q) for q in ("2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q")]
    test_raw = (ROOT / TEST_REL).read_bytes()
    new_test = new_test_bytes(test_raw, (cen_c_old, cen_pl_old), (cen_c_new, cen_pl_new), tax_off, tax_off0, kyobo)
    snap_path = EV / "drift_before.json"
    other_drift_now = drift_vs_live(live["PL"].obj, base_rows)
    cdrift_now = drift_vs_live(live["CSM"].obj, cbase)
    if not snap_path.exists():
        errs.append("drift_before.json missing: run --snapshot-drift before the apply")
    else:
        sj = json.loads(snap_path.read_text(encoding="utf-8"))
        before = {tuple(x) for x in sj["drift_all"]}
        cbefore = {tuple(x) for x in sj["csm_drift_all"]}
        if before != set(other_drift_now):
            errs.append(f"PL live-vs-baseline drift changed vs snapshot: {len(before)} -> {len(other_drift_now)}")
        if cbefore != set(cdrift_now):
            errs.append(f"CSM live-vs-baseline drift changed vs snapshot: {len(cbefore)} -> {len(cdrift_now)}")
    by_co = {}
    for k in dangi_changed:
        by_co[k[0]] = by_co.get(k[0], 0) + 1
    return dict(live=live, new_gold=new_gold, new_cgold=new_cgold, new_rows=new_rows, new_csm=cnew_rows, delta=delta, val_changed=val_changed, dangi_changed=dangi_changed,
                cval=cval, cdangi=cdangi, new_prov=new_prov, prov_targets=prov_targets, prov_live_ne=prov_live_ne, prov_inserted=prov_inserted, new_cprov=new_cprov, cprov_flagged=cprov_flagged,
                census=dict(pl=(cen_pl_old, cen_pl_new), csm=(cen_c_old, cen_c_new)), test_raw=test_raw, new_test=new_test, new_pin=new_pin, pins_dropped=drop, errs=errs, by_co=by_co,
                drift_now=other_drift_now, tax=(len(tax_off0), len(tax_off)), tax_off=tax_off, tax_off0=tax_off0, pre=pre_drift_on_delta, allowed_pre=allowed_pre)


def _stale_none_ok(k, new_by):
    """the new 값_당분기 of k equals (new 값 of k) - (new 값 of the previous quarter of the same item): the cell is derived from two cumulatives that are both adopted/consistent in this load"""
    c, i, q = k
    pq = None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"
    if pq is None or (c, i, pq) not in new_by or new_by[(c, i, pq)]["값"] is None:
        return False
    return abs(new_by[k]["값_당분기"] - (new_by[k]["값"] - new_by[(c, i, pq)]["값"])) <= 1e-6


def expected_dangi():
    """{(code, item, quarter): expected 값_당분기 after the apply} for the cells the seam plan names"""
    exp = {}
    for c, q, i in C["null_dangi_add"]:
        exp[(c, i, q)] = None
    for c, q, i, v, s in C["set_dangi_add"]:
        exp[(c, i, q)] = float(v)
    return exp


def is_derived_follow(k, want):
    """a 값_당분기 that changes because the builder re-derives it from a changed cumulative (this quarter or the previous one of the same item)"""
    c, i, q = k
    if (c, i, q) in want:
        return True
    pq = None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"
    return pq is not None and (c, i, pq) in want


def report(P):
    out = []
    pr = out.append
    g0, g1 = P["live"]["GOLD"].obj, P["new_gold"]
    pr(f"PL gold: set {len(g0['set'])} -> {len(g1['set'])} (+{len(g1['set']) - len(g0['set'])}, {len(C['gold_replace'])} replaced in place); null_dangi cells {len(g0['null_dangi']['cells'])} -> {len(g1['null_dangi']['cells'])}; "
       f"set_dangi cells {len(g0['set_dangi']['cells'])} -> {len(g1['set_dangi']['cells'])}")
    c0, c1 = P["live"]["CGOLD"].obj, P["new_cgold"]
    pr(f"CSM gold: set {len(c0['set'])} -> {len(c1['set'])} ({len(C['csm_gold_new'])} new, {len(C['csm_gold_replace'])} replaced in place, {len(C['csm_gold_remove'])} removed)")
    pr(f"PL master: 값 changed {len(P['val_changed'])}, 값_당분기 changed {len(P['dangi_changed'])} (dangi-only {len(set(P['dangi_changed']) - set(P['val_changed']))}); delta cells {len(P['delta'])}")
    pr(f"  dangi changed per company: {dict(sorted(P['by_co'].items()))}")
    pr(f"CSM master: 값 changed {len(P['cval'])}, 값_당분기 changed {len(P['cdangi'])}")
    pr(f"pre-existing live blanks overwritten by a derivation that equals the printed 3-month column: {P['allowed_pre']}")
    pr(f"PL provenance: {len(P['prov_targets'])} blocks replaced/inserted (live sidecar != emitter(live) on {len(P['prov_live_ne'])} of them; inserted {P['prov_inserted']}) + merge note")
    pr(f"CSM provenance: owner_override flagged on {len(P['cprov_flagged'])} blocks: {P['cprov_flagged']}; owner_override cleared (last gold entry removed) on {CPROV_CLEARED}")
    pr(f"census PL (gold cells, masked): {P['census']['pl'][0]} -> {P['census']['pl'][1]}; CSM: {P['census']['csm'][0]} -> {P['census']['csm'][1]}; ledger pins dropped: {P['pins_dropped']}")
    pr(f"tax22 branch-off failing buckets: {P['tax'][0]} -> {P['tax'][1]}; new: {sorted(P['tax_off'] - P['tax_off0'])}")
    il, worst = identity_report(P["live"]["PL"].obj, P["new_rows"])
    pr(f"identity residuals before -> after per adopted bucket (백만원); worst |after| = {worst:.4f}")
    out += il
    names = {r["원보험사코드"]: r["원수사명"] for r in P["live"]["PL"].obj}
    out += headline_report(P["live"]["PL"].obj, P["new_rows"], P["live"]["CSM"].obj, P["new_csm"], names)
    pr("errors: " + (str(P["errs"]) if P["errs"] else "none"))
    txt = "\n".join(out)
    print(txt)
    return txt


def outputs(P):
    L = P["live"]
    outs = {F["GOLD"]: ak.JsonFile._dump(P["new_gold"], *L["GOLD"].fmt), F["PL"]: ak.JsonFile._dump(P["new_rows"], *L["PL"].fmt),
            F["PROV"]: ak.JsonFile._dump(P["new_prov"], *L["PROV"].fmt), TEST_REL: P["new_test"]}
    if P["pins_dropped"]:
        outs[F["PIN"]] = ak.JsonFile._dump(P["new_pin"], *L["PIN"].fmt)
    return outs


def snapshot_drift():
    live_rows = load_json(F["PL"])
    gold = load_json(F["GOLD"])
    base = simulate_rows(gold, "snapshot")
    drift = drift_vs_live(live_rows, base)
    csm_raw = (ROOT / F["CSM"]).read_bytes()
    cbase = simulate_csm(load_json(F["CGOLD"]), csm_raw, "snapshot")
    cdrift = drift_vs_live(json.loads(csm_raw.decode("utf-8")), cbase)
    by = {}
    for k in drift:
        by[k[0]] = by.get(k[0], 0) + 1
    out = {"made_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "drift_all": [list(k) for k in drift], "csm_drift_all": [list(k) for k in cdrift], "by_company": by,
           "drift_in_target_companies": sorted([list(k) for k in drift if k[0] in CODES], key=lambda x: (x[0], x[2], x[1]))}
    (EV / "drift_before.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"snapshot: cells where a fresh build_pl() with the live gold differs from the live PL master: {len(drift)} (target companies {sum(v for c, v in by.items() if c in CODES)}); "
          f"CSM: fresh build_csm() vs live CSM master: {len(cdrift)}")
    print("  by company:", dict(sorted(by.items())))
    for k in out["drift_in_target_companies"]:
        print("   target-company drift", k)
    for k in cdrift[:10]:
        print("   CSM drift", k)


def verify():
    live_rows = load_json(F["PL"])
    gold = load_json(F["GOLD"])
    base = simulate_rows(gold, "verify")
    drift_now = set(drift_vs_live(live_rows, base))
    sj = json.loads((EV / "drift_before.json").read_text(encoding="utf-8"))
    snap = {tuple(x) for x in sj["drift_all"]}
    by = {rkey(r): r for r in live_rows}
    bs = {rkey(r): r for r in base}
    ok1 = all(by[k]["값"] == bs[k]["값"] for k in PLANNED)
    exp = expected_dangi()
    ok1b = all((by[k]["값_당분기"] is None) if v is None else (by[k]["값_당분기"] is not None and abs(by[k]["값_당분기"] - v) <= 1e-6) for k, v in exp.items())
    fixk = [(e["code"], e["item"], e["quarter"]) for e in C.get("drift_fix", [])]
    ok1b = ok1b and all(by[k]["값"] == bs[k]["값"] and by[k]["값_당분기"] == bs[k]["값_당분기"] for k in fixk)
    print(f"verify PL: drift-fix cells {fixk} equal a fresh build -> {'OK' if all(by[k]['값'] == bs[k]['값'] for k in fixk) else 'FAIL'}")
    ok1c = all(by[k]["값_당분기"] == bs[k]["값_당분기"] for k in exp)
    new_drift = drift_now - snap
    ok2 = not new_drift
    fixed = snap - drift_now
    print(f"verify PL: planned 값 cells equal to a fresh build ({len(PLANNED)}) -> {'OK' if ok1 else 'FAIL'}; planned single-quarter cells equal the plan ({len(exp)}) -> {'OK' if ok1b else 'FAIL'}; equal to a fresh build -> {'OK' if ok1c else 'FAIL'}")
    print(f"verify PL: drift now {len(drift_now)} vs snapshot {len(snap)}; new drift {len(new_drift)} -> {'OK' if ok2 else 'FAIL ' + str(sorted(new_drift)[:6])}; drift cells that the apply fixed {len(fixed)}")
    other = sorted(k for k in drift_now if k[0] not in CODES)
    snap_other = sum(1 for k in snap if k[0] not in CODES)
    ok3 = len(other) == snap_other
    print(f"verify PL: non-target-company drift now {len(other)} (must equal the snapshot's {snap_other})")
    csm_raw = (ROOT / F["CSM"]).read_bytes()
    cbase = simulate_csm(load_json(F["CGOLD"]), csm_raw, "verify")
    cdrift = set(drift_vs_live(json.loads(csm_raw.decode("utf-8")), cbase))
    csnap = {tuple(x) for x in sj["csm_drift_all"]}
    cby = {rkey(r): r for r in json.loads(csm_raw.decode("utf-8"))}
    cbs = {rkey(r): r for r in cbase}
    ok4 = all(cby[k]["값"] == cbs[k]["값"] for k in PLANNED_C)
    ok5 = not (cdrift - csnap)
    print(f"verify CSM: planned 값 cells equal to a fresh build ({len(PLANNED_C)}) -> {'OK' if ok4 else 'FAIL'}; drift now {len(cdrift)} vs snapshot {len(csnap)}; new drift {len(cdrift - csnap)} -> {'OK' if ok5 else 'FAIL'}")
    sub = [r for r in live_rows if r["원보험사코드"] in CODES]
    emit_doc = run_emitter(sub, gold, "verify")
    live_prov = load_json(F["PROV"])
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live_prov["cells"] if c["company_code"] in CODES}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_doc["cells"] if c["company_code"] in CODES}
    bad = [k for k in set(lk) | set(ek) if lk.get(k) != ek.get(k)]
    print(f"verify PL provenance: emitter reproduces {len(ek) - len(bad)}/{len(ek)} target-company blocks (sidecar has {len(lk)})")
    for k in sorted(bad)[:10]:
        print("   provenance block differs from emitter:", k)
    return ok1 and ok1b and ok1c and ok2 and ok3 and ok4 and ok5 and not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-drift", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--out-dir")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    backup = BACKUP
    manifest_path = EV / "apply_manifest_p3.json"
    if a.snapshot_drift:
        snapshot_drift()
        return
    if a.verify:
        raise SystemExit(0 if verify() else 2)
    if a.revert:
        if not a.apply:
            raise SystemExit("--revert needs --apply")
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rel, h in man["after_sha256"].items():
            if ak.sha((ROOT / rel).read_bytes()) != h:
                raise SystemExit(f"ABORT revert: {rel} changed since apply (post-apply hash mismatch)")
        for rel in man["before_sha256"]:
            ak.write_atomic(ROOT / rel, (backup / rel).read_bytes())
        print("reverted", list(man["before_sha256"]))
        return
    P = plan_all()
    txt = report(P)
    (EV / "p3_apply_report.txt").write_text(txt + "\n", encoding="utf-8", newline="\n")
    if P["errs"]:
        raise SystemExit("ABORT: " + " | ".join(P["errs"]))
    outs = outputs(P)
    if a.out_dir:
        od = Path(a.out_dir)
        for rel, b in outs.items():
            ak.write_atomic(od / rel, b)
        print("simulated post-apply files under", od)
        return
    if not a.apply:
        print("(--check only; nothing written)")
        return
    before = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    L = P["live"]
    expect = {F["GOLD"]: L["GOLD"].sha0, F["PL"]: L["PL"].sha0, F["PROV"]: L["PROV"].sha0, F["PIN"]: L["PIN"].sha0, F["CGOLD"]: L["CGOLD"].sha0, F["CSM"]: L["CSM"].sha0, F["CPROV"]: L["CPROV"].sha0,
              TEST_REL: ak.sha(P["test_raw"])}
    for rel, h in before.items():
        if expect[rel] != h:
            raise SystemExit(f"ABORT: {rel} changed between read and write (concurrent session?)")
    backup.mkdir(parents=True, exist_ok=True)
    for rel in outs:
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    written = []
    try:
        for rel, b in outs.items():
            ak.write_atomic(ROOT / rel, b)
            written.append(rel)
    except BaseException:
        for rel in written:
            ak.write_atomic(ROOT / rel, (backup / rel).read_bytes())
        raise
    after = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    manifest_path.write_text(json.dumps({"before_sha256": before, "after_sha256": after, "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, indent=2),
                             encoding="utf-8", newline="\n")
    print("APPLIED:", list(outs))


if __name__ == "__main__":
    main()
