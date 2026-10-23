#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level applier for task 5 (ticket 20261023T1215Z part 2): CSM single-quarter blank mechanism, 롯데손해보험 KR0003 2023.4Q CSM items 3 / 4 / 5.

The mechanism itself is code (scripts/build_root_masters.py::_csm_null_dangi_keys + build_csm), already edited in the working tree; this applier adds the gold section and the three master cells:
  data/_gold/user_csm_cells.json  +"null_dangi": {"_doc": ..., "cells": [[KR0003, 2023.4Q, 3], [.., 4], [.., 5]]} right after "set" (nothing else changes: byte-exact format kept)
  CSM_waterfall.json              ONLY the cells where a REAL build_csm() run (temp copy, NEW builder code) with the new gold differs from the same run with the live gold: 값_당분기 -> None, 값 untouched
Guards: (1) a build with the NEW builder code and the LIVE gold must reproduce the live master on every row (the code change alone is behaviour-neutral);
        (2) the delta must be exactly the three planned cells, 값 equal, 값_당분기 numeric -> None;  (3) live files hash-checked between read and write; (4) backups verified byte-identical.
  --check | --out-dir DIR | --apply | --verify | --revert --apply
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "kr0003_lotte_csm_blank"
BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "backup_before_apply"
TMP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e25_csm_tmp")
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("ak_helpers", str(ROOT / "data/_derived/kyobo_csm_basis_fix_20261021/apply_kr0073_fix.py"))
ak = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ak)

F = {"CGOLD": "data/_gold/user_csm_cells.json", "CSM": "CSM_waterfall.json"}
CELLS = [["KR0003", "2023.4Q", 3], ["KR0003", "2023.4Q", 4], ["KR0003", "2023.4Q", 5]]
DOC = ("2026-10-24 ticket 20261023T1215Z part 2 (parser/ifrs17; mechanism = build_root_masters._csm_null_dangi_keys, the CSM twin of the PL null_dangi): 값_당분기 forced blank (값 = cumulative kept) for "
       "KR0003 롯데손해보험 2023.4Q CSM items 3 (이자 부리) / 4 (가정 및 경험 조정) / 5 (CSM 상각). The 4Q cumulative is the restated annual comparative of the FY2024 annual report "
       "(opening 16,669.0; 2026-10-23 D2 load, owner decision) while the 3Q cumulative is still the original-vintage print (opening 16,774.4; the FY2024 Q3 report's prior 9-month CSM vector equals "
       "the master), so the builder difference (4Q - 3Q) mixes two vintages: the annual flows moved with the restatement (이자 부리 780.5 -> 777.0, 가정 및 경험 조정 2,801.0 -> 2,795.0, CSM 상각 -1,868.5 -> -1,859.0) "
       "but the 9-month flows did not, and the single-quarter roll-forward (opening 22,085.6 + 신계약 1,386.8 + 이자 223.0 + 가정 813.7 + 상각 -542.8 = 23,966.3) misses the restated closing 23,860.8 "
       "by +105.5 (= the opening restatement 16,774.4 - 16,669.0). Item 2 (신계약 CSM) is NOT blanked: its annual value is identical in both vintages (5,478.9), so 5,478.9 - 4,092.1 = 1,386.8 is the fourth-quarter "
       "new business. Items 1 and 6 are stock cells, not differences of cumulatives: the 4Q opening is the 3Q closing as filed, the 4Q closing is the restated annual closing. "
       "Owner rule 2026-10-22: a blank beats a wrong value. The annual report prints no 3-month Q4 column; re-derive when a restated 9M-2023 comparative exists. "
       "Evidence data/_derived/remaining_20261022/e25_followups/kr0003_lotte_csm_blank/ (c01_show_csm.py, c03_vintage_evidence.txt).")


def rkey(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def build_gold(live_gold):
    if "null_dangi" in live_gold:
        raise SystemExit("ABORT: user_csm_cells.json already has a null_dangi section")
    out = {}
    for k, v in live_gold.items():
        out[k] = copy.deepcopy(v)
        if k == "set":
            out["null_dangi"] = {"_doc": DOC, "cells": copy.deepcopy(CELLS)}
    if "null_dangi" not in out:
        raise SystemExit("ABORT: no 'set' key to anchor the null_dangi section")
    return out


def simulate_csm(gold_obj, master_raw: bytes, tag: str):
    TMP.mkdir(parents=True, exist_ok=True)
    gp, mp = TMP / f"cgold_{tag}.json", TMP / f"cmaster_{tag}.json"
    gp.write_text(json.dumps(gold_obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    mp.write_bytes(master_raw)
    brm = ak.load_brm()                 # imports the CURRENT scripts/build_root_masters.py (new code)
    brm.CSM_OVR, brm.CSM_OUT = gp, mp
    brm.build_csm()
    rows = json.loads(mp.read_text(encoding="utf-8"))
    for p in (gp, mp):
        try:
            p.unlink()
        except OSError:
            pass
    return rows


def plan():
    live = {k: ak.JsonFile(rel) for k, rel in F.items()}
    new_gold = build_gold(live["CGOLD"].obj)
    base = simulate_csm(live["CGOLD"].obj, live["CSM"].raw, "base")
    new = simulate_csm(new_gold, live["CSM"].raw, "new")
    errs = []
    if len(base) != len(live["CSM"].obj) or len(new) != len(base):
        errs.append(f"row counts differ: live {len(live['CSM'].obj)} base {len(base)} new {len(new)}")
    lb, bb, nb = ({rkey(r): r for r in x} for x in (live["CSM"].obj, base, new))
    drift = [k for k in lb if (lb[k]["값"], lb[k].get("값_당분기")) != (bb[k]["값"], bb[k].get("값_당분기"))]
    if drift:
        errs.append(f"the NEW builder code with the LIVE gold does not reproduce the live master on {len(drift)} cells: {drift[:5]}")
    delta = sorted(k for k in bb if (bb[k]["값"], bb[k].get("값_당분기")) != (nb[k]["값"], nb[k].get("값_당분기")))
    want = sorted((c, i, q) for c, q, i in CELLS)
    if delta != want:
        errs.append(f"delta {delta} != planned {want}")
    for k in want:
        if bb[k]["값"] != nb[k]["값"] or nb[k].get("값_당분기") is not None or bb[k].get("값_당분기") is None:
            errs.append(f"{k}: 값 {bb[k]['값']}->{nb[k]['값']} 값_당분기 {bb[k].get('값_당분기')}->{nb[k].get('값_당분기')} (expected 값 equal, numeric -> None)")
    new_rows = []
    for r in live["CSM"].obj:
        k = rkey(r)
        if k in want:
            nr = dict(r)
            nr["값_당분기"] = None
            new_rows.append(nr)
        else:
            new_rows.append(r)
    return dict(live=live, new_gold=new_gold, new_rows=new_rows, delta=delta, errs=errs, base=bb, new=nb)


def report(P):
    L = []
    pr = L.append
    pr(f"CSM gold: top-level keys {list(P['live']['CGOLD'].obj.keys())} -> {list(P['new_gold'].keys())}; set {len(P['live']['CGOLD'].obj['set'])} -> {len(P['new_gold']['set'])} (unchanged)")
    pr(f"CSM master: cells changed {len(P['delta'])}: " + "; ".join(f"{k[0]} {k[2]} item {k[1]}: 값 {P['base'][k]['값']} kept, 값_당분기 {P['base'][k].get('값_당분기')} -> {P['new'][k].get('값_당분기')}" for k in P["delta"]))
    for it in range(1, 7):
        r = P["base"][("KR0003", it, "2023.4Q")]
        n = P["new"][("KR0003", it, "2023.4Q")]
        pr(f"  KR0003 2023.4Q item {it}: 값 {r['값']} | 값_당분기 {r.get('값_당분기')} -> {n.get('값_당분기')}")
    pr("errors: " + (str(P["errs"]) if P["errs"] else "none"))
    txt = "\n".join(L)
    print(txt)
    return txt


def outputs(P):
    L = P["live"]
    return {F["CGOLD"]: ak.JsonFile._dump(P["new_gold"], *L["CGOLD"].fmt), F["CSM"]: ak.JsonFile._dump(P["new_rows"], *L["CSM"].fmt)}


def verify():
    gold = json.loads((ROOT / F["CGOLD"]).read_text(encoding="utf-8"))
    raw = (ROOT / F["CSM"]).read_bytes()
    fresh = simulate_csm(gold, raw, "verify")
    live = json.loads(raw.decode("utf-8"))
    fb, lb = {rkey(r): r for r in fresh}, {rkey(r): r for r in live}
    drift = [k for k in lb if (lb[k]["값"], lb[k].get("값_당분기")) != (fb[k]["값"], fb[k].get("값_당분기"))]
    cells = [tuple(c) for c in gold.get("null_dangi", {}).get("cells", [])]
    ok_cells = all(lb[(c, i, q)]["값_당분기"] is None and lb[(c, i, q)]["값"] is not None for c, q, i in cells)
    print(f"verify CSM: a fresh build_csm() from the LIVE gold reproduces the live master on every row: drift {len(drift)} -> {'OK' if not drift else 'FAIL ' + str(drift[:5])}; "
          f"{len(cells)} null_dangi cells blank with 값 kept -> {'OK' if ok_cells else 'FAIL'}")
    return not drift and ok_cells and len(cells) == len(CELLS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--out-dir")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    manifest = EV / "apply_manifest_e25_csm.json"
    if a.verify:
        raise SystemExit(0 if verify() else 2)
    if a.revert:
        if not a.apply:
            raise SystemExit("--revert needs --apply")
        man = json.loads(manifest.read_text(encoding="utf-8"))
        for rel, h in man["after_sha256"].items():
            if ak.sha((ROOT / rel).read_bytes()) != h:
                raise SystemExit(f"ABORT revert: {rel} changed since apply")
        for rel in man["before_sha256"]:
            ak.write_atomic(ROOT / rel, (BACKUP / rel).read_bytes())
        print("reverted", list(man["before_sha256"]))
        return
    P = plan()
    txt = report(P)
    (EV / "c02_apply_report.txt").write_text(txt + "\n", encoding="utf-8", newline="\n")
    if P["errs"]:
        raise SystemExit("ABORT: " + " | ".join(P["errs"]))
    outs = outputs(P)
    if a.out_dir:
        for rel, b in outs.items():
            ak.write_atomic(Path(a.out_dir) / rel, b)
        print("simulated post-apply files under", a.out_dir)
        return
    if not a.apply:
        print("(--check only; nothing written)")
        return
    before = {rel: ak.sha((ROOT / rel).read_bytes()) for rel in outs}
    L = P["live"]
    expect = {F["CGOLD"]: L["CGOLD"].sha0, F["CSM"]: L["CSM"].sha0}
    for rel, h in before.items():
        if expect[rel] != h:
            raise SystemExit(f"ABORT: {rel} changed between read and write (concurrent session?)")
    for rel in outs:
        dst = BACKUP / rel
        if dst.exists() and ak.sha(dst.read_bytes()) != before[rel]:
            raise SystemExit(f"ABORT: backup {dst} exists with different bytes than the live file")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copyfile(ROOT / rel, dst)
        if ak.sha(dst.read_bytes()) != before[rel]:
            raise SystemExit(f"ABORT: backup of {rel} is not byte-identical")
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
