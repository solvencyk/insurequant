#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-adjustment after the extract_tier2_kblife `_jang_rerev = jrr` handler fix (ticket 20261023T0300Z): the KB라이프 2024.1Q items 2 / 8 / 12 are produced correctly by the builder
source (data/dart/viz/pl_breakdown_master.json, rebuilt with the fixed handler: 85,633 -> 84,497 / -832 -> -1,968 / -24 -> -1,160), so the three gold cells loaded by e21_apply.py would be
MASKED gold (gold == builder source) and would need new ledger pins (ticket: no new mask cells / no new pins).  They are therefore REMOVED from data/_gold/user_pl_cells.json; the root master cells
already hold the right values (a fresh build from the new gold reproduces them).

  --check            read-only: simulates the removal, proves the fresh build keeps every cell, lists the provenance block that changes, the census
  --apply            writes data/_gold/user_pl_cells.json, PL_breakdown_provenance.json (changed block + note key), tests/test_rule_coverage_manifest.py (census PL tuple); backups in the scratchpad
  --revert --apply   restores the backups (only while the files still carry the post-apply hashes); run this BEFORE e21_apply.py --revert --apply
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_apply as A  # noqa: E402

ak, ROOT, EV = A.ak, A.ROOT, A.EV
BACKUP = A.BACKUP / "post_klife"
KEYS = [("KR0099", 2, "2024.1Q"), ("KR0099", 8, "2024.1Q"), ("KR0099", 12, "2024.1Q")]
NOTE_KEY = "merge_note_20261023_e21_klife_gold_removed"
NOTE = ("ticket 20261023T0300Z: extract_tier2_kblife `_jang_rerev = abs(jrr)` fixed (scripts/pl_breakdown/companies.py); the rebuilt builder source now carries KR0099 2024.1Q items 2/8/12 = 84,497 / -1,968 / -1,160 "
        "(PL golden manifest updated for exactly these 3 cells), so the 3 gold cells that e21_apply.py had loaded are removed (they would be masked gold needing new ledger pins). Evidence "
        "data/_derived/remaining_20261022/e21_ready25/")
FILES = {"GOLD": A.F["GOLD"], "PROV": A.F["PROV"], "TEST": A.TEST_REL}


def plan():
    live = {k: ak.JsonFile(rel) for k, rel in (("GOLD", A.F["GOLD"]), ("PL", A.F["PL"]), ("PROV", A.F["PROV"]))}
    errs = []
    gold = live["GOLD"].obj
    ent = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    planned = {(e["code"], e["item"], e["quarter"]): e for e in A.C["gold_new"]}
    for k in KEYS:
        e = ent.get(k)
        p = planned.get(k)
        if e is None or p is None or e["값"] != p["value"] or e["note"] != p["note"]:
            errs.append(f"gold entry {k} missing or different from the e21 plan")
    new_gold = copy.deepcopy(gold)
    new_gold["set"] = [e for e in new_gold["set"] if (e["원보험사코드"], e["항목번호"], e["공시분기"]) not in set(KEYS)]
    if len(gold["set"]) - len(new_gold["set"]) != 3:
        errs.append("did not remove exactly 3 gold entries")
    # builder source must carry the right values now
    src = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in A.load_json(A.PL_MASTER_SRC)}
    for k in KEYS:
        if src.get(k) != planned[k]["value"]:
            errs.append(f"builder source {k} = {src.get(k)} != {planned[k]['value']} (rebuild the viz master with the fixed handler first)")
    # fresh builds
    base = A.simulate_rows(gold, "pk_base")
    new = A.simulate_rows(new_gold, "pk_new")
    bb, nb = {A.rkey(r): r for r in base}, {A.rkey(r): r for r in new}
    delta = [k for k in bb if (bb[k]["값"], bb[k].get("값_당분기")) != (nb[k]["값"], nb[k].get("값_당분기"))]
    if delta:
        errs.append(f"removing the 3 gold cells moves {len(delta)} cells of the fresh build: {delta[:5]}")
    lm = {A.rkey(r): r for r in live["PL"].obj}
    for k in KEYS:
        kk = (k[0], k[1], k[2])
        if nb[kk]["값"] != lm[kk]["값"]:
            errs.append(f"fresh build {kk} = {nb[kk]['값']} != live master {lm[kk]['값']}")
    drift_new = A.drift_vs_live(live["PL"].obj, new)
    snap = {tuple(x) for x in json.loads((EV / "drift_before.json").read_text(encoding="utf-8"))["drift_all"]}
    extra = set(drift_new) - snap
    if extra:
        errs.append(f"new live-vs-fresh drift: {sorted(extra)[:5]}")
    # provenance
    sub = [r for r in live["PL"].obj if r["원보험사코드"] in A.CODES]
    emit_new = A.run_emitter(sub, new_gold, "pk_new")
    emit_old = A.run_emitter(sub, gold, "pk_old")
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_new["cells"]}
    eo = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_old["cells"]}
    targets = sorted(k for k in ek if eo.get(k) != ek[k])
    if targets != [("KR0099", "2024.1Q", "income_statement")]:
        errs.append(f"provenance blocks that change: {targets}")
    new_prov = copy.deepcopy(live["PROV"].obj)
    lk = {(c["company_code"], c["quarter"], c["item_block"]): i for i, c in enumerate(new_prov["cells"])}
    for k in targets:
        if live["PROV"].obj["cells"][lk[k]] != eo[k]:
            errs.append(f"live sidecar block {k} != emitter(old gold)")
        new_prov["cells"][lk[k]] = ek[k]
    if NOTE_KEY in new_prov:
        errs.append("note key already present")
    new_prov[NOTE_KEY] = NOTE
    # census
    pin = A.load_json(A.PIN_REL)
    cen_old, un0, dr0, st0 = A.census("PL", gold, pin, A.load_json(A.PL_MASTER_SRC))
    cen_new, un1, dr1, st1 = A.census("PL", new_gold, pin, A.load_json(A.PL_MASTER_SRC))
    cen_keep, un_keep, _d, _s = A.census("PL", gold, pin, A.load_json(A.PL_MASTER_SRC))
    if un1 or dr1 or st1:
        errs.append(f"census after: unpinned {un1} drift {dr1} stale {st1}")
    if cen_old[1] - cen_new[1] != 3 or cen_old[0] - cen_new[0] != 3:
        errs.append(f"census {cen_old} -> {cen_new} (the rebuilt source makes the 3 gold cells masked: masked must drop by 3 too)")
    test_raw = (ROOT / A.TEST_REL).read_bytes()
    s = test_raw.decode("utf-8").replace("\r\n", "\n")
    crlf = b"\r\n" in test_raw
    m = re.search(r'^GOLD_OVERLAY_CENSUS = \{"CSM": \((\d+), (\d+)\), "PL": \((\d+), (\d+)\)\}$', s, re.M)
    if m is None or (int(m.group(3)), int(m.group(4))) != (1174, 22):
        errs.append(f"declared census {m.group(0) if m else None} != the e21-apply declaration (1174, 22)")
    else:
        comment = ("# 2026-10-23 ticket 20261023T0300Z (KB라이프 extract_tier2_kblife abs() fix): the builder source now carries KR0099 2024.1Q items 2/8/12, so their 3 gold cells are removed "
                   "(masked gold would need new pins): PL gold 1174->%d cells, masked 22->%d.\n" % (cen_new[0], cen_new[1]))
        s = s[:m.start()] + comment + 'GOLD_OVERLAY_CENSUS = {"CSM": (%s, %s), "PL": (%d, %d)}' % (m.group(1), m.group(2), cen_new[0], cen_new[1]) + s[m.end():]
    new_test = (s.replace("\n", "\r\n") if crlf else s).encode("utf-8")
    return dict(live=live, new_gold=new_gold, new_prov=new_prov, new_test=new_test, test_raw=test_raw, errs=errs, census=(cen_old, cen_new), targets=targets, drift_new=len(drift_new))


def outputs(P):
    L = P["live"]
    return {A.F["GOLD"]: ak.JsonFile._dump(P["new_gold"], *L["GOLD"].fmt), A.F["PROV"]: ak.JsonFile._dump(P["new_prov"], *L["PROV"].fmt), A.TEST_REL: P["new_test"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()
    manifest = EV / "post_klife_manifest.json"
    if a.revert:
        if not a.apply:
            raise SystemExit("--revert needs --apply")
        man = json.loads(manifest.read_text(encoding="utf-8"))
        for rel, h in man["after_sha256"].items():
            if ak.sha((ROOT / rel).read_bytes()) != h:
                raise SystemExit(f"ABORT revert: {rel} changed since the post-adjust")
        for rel in man["before_sha256"]:
            ak.write_atomic(ROOT / rel, (BACKUP / rel).read_bytes())
        print("reverted", list(man["before_sha256"]))
        return
    P = plan()
    print(f"census PL (gold cells, masked): {P['census'][0]} -> {P['census'][1]}; provenance blocks changed: {P['targets']}; live-vs-fresh drift cells after: {P['drift_new']}")
    print("errors: " + (str(P["errs"]) if P["errs"] else "none"))
    if P["errs"]:
        raise SystemExit("ABORT: " + " | ".join(P["errs"]))
    if not a.apply:
        print("(--check only; nothing written)")
        return
    outs = outputs(P)
    L = P["live"]
    before = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    expect = {A.F["GOLD"]: L["GOLD"].sha0, A.F["PROV"]: L["PROV"].sha0, A.TEST_REL: ak.sha(P["test_raw"])}
    for rel, h in before.items():
        if expect[rel] != h:
            raise SystemExit(f"ABORT: {rel} changed between read and write")
    BACKUP.mkdir(parents=True, exist_ok=True)
    for rel in outs:
        dst = BACKUP / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    written = []
    try:
        for rel, b in outs.items():
            ak.write_atomic(ROOT / rel, b)
            written.append(rel)
    except BaseException:
        for rel in written:
            ak.write_atomic(ROOT / rel, (BACKUP / rel).read_bytes())
        raise
    after = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    manifest.write_text(json.dumps({"before_sha256": before, "after_sha256": after, "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("APPLIED:", list(outs))


if __name__ == "__main__":
    main()
