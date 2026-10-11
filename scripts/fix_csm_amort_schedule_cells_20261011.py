# -*- coding: utf-8 -*-
"""Correct the 2025.4Q cells of CSM_amortization.json whose annual amortisation schedule came from the PRIOR-year-end table.

Ticket : inbox/parser/20261011T1900Z__orchestrator__MULTI_2024.4Q-2025.4Q__csm_amort_schedule_prior_year_table_picked.md
Runlog : data/disclosure/_meta/csm_amort_schedule_fix_runlog_20261011.md
Cause  : scripts/viz_build_ifrs17_panels.py::_pick_amort_block chose the later (전기말) of two identical 당기말/전기말 tables; fixed there
         (_current_period_twin).  The master's 2025.4Q rows were derived from that panel, so they carry the same prior-year schedule.

What it does (cell level, never a rebuild of the master):
  - companies = every entry whose `yearly` differs between the PRE-FIX panel (data/_derived/amort_fix_backup_20261011/
    csm_amort_schedule.json.pre_fix) and the rebuilt panel (data/dart/viz/csm_amort_schedule.json);
  - OLD-VALUE GUARD: for each of the 10 cells the master's current 상각액 must equal round(pre-fix panel yearly[y_k], 1) (how the master
    cell was originally derived: build_tidy_exports.num); a cell that differs (hand edit / other source) aborts the whole run;
  - NEW value = round(rebuilt panel yearly[y_k], 1), except KR0074 Lina: the 2025-12-31 schedule that the Lina backfill agent read from the
    disclosure PDF (proposed_fixes_existing_cells.json, 천원 -> 억원, 5 decimals, y1..y10 complete because the PDF carries the second half of the
    split table); it is accepted only if y1..y8 agree with the rebuilt panel to 4 decimals;
  - the master is re-read right before the write, must round-trip through json.dumps(indent=2)+CRLF, is backed up first, and is re-read
    afterwards: every row except the target cells must be byte-for-byte the same object, row count and key order unchanged.

  default            dry run (prints + writes amort_cells_fix_plan.json, touches nothing else)
  --apply            write the master (+ amort_cells_fix_manifest.json)
  --revert --apply   put the old values back, only for cells that still hold the new value

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_csm_amort_schedule_cells_20261011.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "_derived" / "amort_fix_20261011"
BACKUP = ROOT / "data" / "_derived" / "amort_fix_backup_20261011"
MASTER = ROOT / "CSM_amortization.json"
OLD_PANEL = BACKUP / "csm_amort_schedule.json.pre_fix"
NEW_PANEL = ROOT / "data" / "dart" / "viz" / "csm_amort_schedule.json"
LINA_PROPOSAL = ROOT / "data" / "_derived" / "csm_backfill_lina_20261011" / "proposed_fixes_existing_cells.json"
QUARTER = "2025.4Q"
LINA_CODE = "KR0074"
sys.stdout.reconfigure(encoding="utf-8")

# panel company name (DART corp name) -> master 원수사명, the same 7 aliases viz_build_ifrs17_panels._CSM_NAME_ALIAS carries
ALIAS = {"미래에셋생명": "미래에셋생명보험", "삼성생명": "삼성생명보험", "코리안리": "코리안리재보험", "아이비케이연금보험": "IBK연금보험",
         "케이비라이프생명보험": "KB라이프생명", "에이아이지손해보험": "AIG손해보험", "엠지손해보험": "예별손해보험"}


def dump(obj) -> bytes:
    """the exact serialisation of the masters: json.dumps(indent=2, ensure_ascii=False), CRLF, no trailing newline"""
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def read_guarded(path: Path):
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if dump(obj) != raw:
        raise SystemExit(f"{path.name}: bytes do not round-trip through json.dumps(indent=2)+CRLF -- refusing to write")
    return raw, obj


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def num(v):
    """build_tidy_exports.num: 1-decimal rounding, None stays None"""
    return None if v is None else round(float(v), 1)


def same(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) < 1e-9


def build_plan(rows: list) -> dict:
    old_p = {c["company"]: c for c in json.loads(OLD_PANEL.read_text(encoding="utf-8"))["companies"]}
    new_p = {c["company"]: c for c in json.loads(NEW_PANEL.read_text(encoding="utf-8"))["companies"]}
    assert old_p.keys() == new_p.keys(), "panel company sets differ"
    proof = {r["company"]: r for r in json.loads((WORK / "a10_final_proof.json").read_text(encoding="utf-8"))}
    lina = json.loads(LINA_PROPOSAL.read_text(encoding="utf-8"))["csm_amortization_2025.4Q"]
    cells = {}
    for r in rows:
        if r["공시분기"] == QUARTER:
            cells[(r["원수사명"], r["경과차년"])] = r
    names_2025 = {n for n, _ in cells}
    plan, problems = {}, []
    for co, o in old_p.items():
        n = new_p[co]
        if (o.get("yearly") or {}) == (n.get("yearly") or {}):
            continue
        mname = ALIAS.get(co, co)
        if mname not in names_2025:
            problems.append(f"{co}: no master rows for {mname} {QUARTER}")
            continue
        code = cells[(mname, 1)]["원보험사코드"]
        if sum(1 for (nm, _) in cells if nm == mname) != 10:
            problems.append(f"{co}: master {mname} {QUARTER} does not have exactly 10 rows")
            continue
        new_vals = {k: num((n.get("yearly") or {}).get(f"y{k}")) for k in range(1, 11)}
        source = "rebuilt panel (DART XML), 1 decimal"
        if code == LINA_CODE:
            prop = lina["correct_2025-12-31_1_to_10_억원"]
            panel_new = n.get("yearly") or {}
            for k in range(1, 9):
                if abs(panel_new.get(f"y{k}") - prop[k - 1]) > 6e-5:
                    problems.append(f"{co}: PDF proposal y{k}={prop[k - 1]} differs from the rebuilt panel {panel_new.get(f'y{k}')}")
            new_vals = {k: prop[k - 1] for k in range(1, 11)}
            source = "Lina disclosure PDF p245 (proposed_fixes_existing_cells.json), y1..y8 == rebuilt DART panel to 4 dp, 5 decimals"
            # the proposal's recorded 'current' cells must be what the master holds
            for k in range(1, 11):
                if not same(cells[(mname, k)]["상각액"], lina["current_master_1_to_10"][k - 1]):
                    problems.append(f"{co}: master y{k}={cells[(mname, k)]['상각액']} != proposal's recorded current {lina['current_master_1_to_10'][k - 1]}")
        entry = {"company": co, "master_name": mname, "code": code, "source_of_new_values": source, "cells": []}
        for k in range(1, 11):
            cur = cells[(mname, k)]["상각액"]
            expect_old = num((o.get("yearly") or {}).get(f"y{k}"))
            if not same(cur, expect_old):
                problems.append(f"{co} y{k}: master {cur} != round(pre-fix panel y{k}) {expect_old}  (old-value guard)")
            entry["cells"].append({"경과차년": k, "old": cur, "new": new_vals[k], "changed": not same(cur, new_vals[k])})
        ev = proof.get(co) or {}
        entry["evidence"] = {k: ev.get(k) for k in ("rcept", "old", "new", "total_before", "total_after", "close_FY", "close_FY-1",
                                                    "rel_old_vs_FY-1", "rel_new_vs_FY", "fy24filing_cur_y1_total")}
        plan[co] = entry
    return {"plan": plan, "problems": problems}


def apply_cells(rows: list, plan: dict, revert: bool) -> int:
    n = 0
    for entry in plan.values():
        for c in entry["cells"]:
            if not c["changed"]:
                continue
            for r in rows:
                if r["원수사명"] == entry["master_name"] and r["공시분기"] == QUARTER and r["경과차년"] == c["경과차년"]:
                    frm, to = (c["new"], c["old"]) if revert else (c["old"], c["new"])
                    if not same(r["상각액"], frm):
                        raise SystemExit(f"{entry['company']} y{c['경과차년']}: cell holds {r['상각액']}, expected {frm} -- refusing")
                    r["상각액"] = to
                    n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()
    raw, rows = read_guarded(MASTER)
    res = build_plan(rows)
    plan, problems = res["plan"], res["problems"]
    n_changed = sum(1 for e in plan.values() for c in e["cells"] if c["changed"])
    print(f"master {MASTER.name}: {len(rows)} rows | companies with a changed schedule: {len(plan)} | cells to change: {n_changed} of {len(plan) * 10}")
    for co, e in plan.items():
        ch = [c for c in e["cells"] if c["changed"]]
        print(f"  {co:<14s} ({e['master_name']}, {e['code']}) changed {len(ch)}/10  y1 {e['cells'][0]['old']} -> {e['cells'][0]['new']}  y5 {e['cells'][4]['old']} -> {e['cells'][4]['new']}  y9 {e['cells'][8]['old']} -> {e['cells'][8]['new']}")
    if problems:
        print("PROBLEMS (nothing written):")
        for p in problems:
            print("   ", p)
        return 3
    (WORK / "amort_cells_fix_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    if not a.apply:
        print("(dry run -- nothing written to the master; add --apply)")
        return 0
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MASTER, BACKUP / ("CSM_amortization.json.pre_revert" if a.revert else "CSM_amortization.json.pre_apply"))
    (BACKUP / ("CSM_amortization.json.pre_revert.sha256" if a.revert else "CSM_amortization.json.pre_apply.sha256")).write_text(sha(raw) + "\n", encoding="utf-8", newline="\n")
    before = json.loads(json.dumps(rows))
    wrote = apply_cells(rows, plan, a.revert)
    data = dump(rows)
    if sha(MASTER.read_bytes()) != sha(raw):
        raise SystemExit("master changed while planning -- start over (nothing written)")
    tmp = MASTER.with_suffix(".json.tmp_amortfix")
    tmp.write_bytes(data)
    tmp.replace(MASTER)
    # ---- proof: re-read; only the target cells moved
    raw2, rows2 = read_guarded(MASTER)
    assert len(rows2) == len(before), "row count changed"
    target = {(e["master_name"], QUARTER, c["경과차년"]) for e in plan.values() for c in e["cells"] if c["changed"]}
    moved = 0
    for b, r in zip(before, rows2):
        if (b["원수사명"], b["공시분기"], b["경과차년"]) in target:
            assert {k: v for k, v in b.items() if k != "상각액"} == {k: v for k, v in r.items() if k != "상각액"}, "non-value field changed"
            if not same(b["상각액"], r["상각액"]):
                moved += 1
        else:
            assert b == r, f"non-target row changed: {b}"
    assert moved == wrote == len(target), (moved, wrote, len(target))
    print(f"{'reverted' if a.revert else 'written'}: {moved} cells changed in {len(plan)} companies; every other row identical (row-by-row proof); "
          f"sha256 {sha(raw)[:12]} -> {sha(raw2)[:12]}")
    if not a.revert:
        (WORK / "amort_cells_fix_manifest.json").write_text(json.dumps(
            {"master": MASTER.name, "quarter": QUARTER, "cells_changed": moved, "companies": len(plan),
             "sha256_before": sha(raw), "sha256_after": sha(raw2), "plan": plan}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
