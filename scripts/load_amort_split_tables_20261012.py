# -*- coding: utf-8 -*-
"""Write the staged split-table / separate-basis cells into CSM_amortization.json (2025.4Q), cell by cell.

Ticket : inbox/parser/20261012T1020Z__orchestrator__MULTI_2023.4Q-2026.2Q__ifrs17_owner_followups_20261012.md item 6.
Spec   : data/_derived/ifrs17_owner_followups_20261012/amort_split_spec.json (written by scripts/extract_amort_split_tables_20261012.py from the raw DART XML;
         evidence + identity table: amort_split_evidence.json / .md next to it).
Cells  : AIA, Chubb, MetLife, BNP Cardif  y9, y10   (blank -> value; the back half of the split table)       = 8 cells
         Hanwha Life                       y1..y10  (consolidated table the panel picked -> separate table)  = 10 cells
         Lina is NOT touched (its 2025.4Q was completed from the disclosure PDF on 2026-10-11; the DART back table agrees to 5 decimals).

Guards  : the master must round-trip through json.dumps(indent=2)+CRLF; every target cell must hold exactly the spec's `old` value (None for the blank cells);
          the master is backed up, re-read right before the write, written to a temp file and replaced atomically, then re-read: every row except the target
          cells must be the very same object, row count / order unchanged.
Panels  : data/dart/viz/csm_amort_schedule.json is NOT touched (publishing/designer own it).  A rebuild of the master from the panel
          (build_tidy_exports.py --only amort) would put the blank/consolidated cells back -- run this loader again afterwards.

  default            dry run
  --apply            write
  --revert --apply   put the old values back (only for cells that still hold the new value)

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_amort_split_tables_20261012.py [--apply] [--revert]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "_derived" / "ifrs17_owner_followups_20261012"
BACKUP = ROOT / "data" / "_derived" / "ifrs17_owner_followups_backup_20261012"
MASTER = ROOT / "CSM_amortization.json"
SPEC = WORK / "amort_split_spec.json"
sys.stdout.reconfigure(encoding="utf-8")


def dump(obj) -> bytes:
    """the exact serialisation of the master: json.dumps(indent=2, ensure_ascii=False), CRLF, no trailing newline"""
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def same(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) < 1e-9


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if spec.get("problems"):
        raise SystemExit(f"ABORT: the spec carries problems: {spec['problems']}")
    quarter = spec["quarter"]
    raw = MASTER.read_bytes()
    rows = json.loads(raw.decode("utf-8"))
    if dump(rows) != raw:
        raise SystemExit("ABORT: CSM_amortization.json does not round-trip through json.dumps(indent=2)+CRLF")
    idx = {}
    for i, r in enumerate(rows):
        k = (r["원보험사코드"], r["공시분기"], r["경과차년"])
        if k in idx:
            raise SystemExit(f"ABORT: duplicate master key {k}")
        idx[k] = i

    plan = []                                   # (row index, code, 경과차년, from, to)
    for comp in spec["companies"]:
        for c in comp["cells"]:
            k = (comp["code"], quarter, c["경과차년"])
            if k not in idx:
                raise SystemExit(f"ABORT: master has no row {k}")
            frm, to = (c["new"], c["old"]) if a.revert else (c["old"], c["new"])
            cur = rows[idx[k]]["상각액"]
            if not same(cur, frm):
                raise SystemExit(f"ABORT: {k} holds {cur}, expected {frm} -- refusing")
            plan.append((idx[k], comp["code"], c["경과차년"], frm, to))
    print(f"master {MASTER.name}: {len(rows)} rows; cells to {'revert' if a.revert else 'write'}: {len(plan)} in {len(spec['companies'])} companies ({quarter})")
    for i, code, y, frm, to in plan:
        print(f"   {code} y{y:>2}: {frm} -> {to}")
    if not a.apply:
        print("(dry run -- nothing written; add --apply)")
        return 0

    BACKUP.mkdir(parents=True, exist_ok=True)
    tag = "pre_revert_amort_split" if a.revert else "pre_amort_split"
    shutil.copyfile(MASTER, BACKUP / f"CSM_amortization.json.{tag}")
    (BACKUP / f"CSM_amortization.json.{tag}.sha256").write_text(sha(raw) + "\n", encoding="utf-8", newline="\n")
    before = json.loads(json.dumps(rows))
    for i, code, y, frm, to in plan:
        rows[i]["상각액"] = to
    data = dump(rows)
    if MASTER.read_bytes() != raw:
        raise SystemExit("ABORT: master changed while planning -- nothing written")
    tmp = MASTER.with_suffix(".json.tmp_amortsplit")
    tmp.write_bytes(data)
    tmp.replace(MASTER)

    raw2 = MASTER.read_bytes()
    rows2 = json.loads(raw2.decode("utf-8"))
    assert dump(rows2) == raw2, "written master does not round-trip"
    assert len(rows2) == len(before), "row count changed"
    target = {i for i, *_ in plan}
    moved = 0
    for i, (b, r) in enumerate(zip(before, rows2)):
        if i in target:
            assert {k: v for k, v in b.items() if k != "상각액"} == {k: v for k, v in r.items() if k != "상각액"}, "non-value field changed"
            if not same(b["상각액"], r["상각액"]):
                moved += 1
        else:
            assert b == r, f"non-target row changed: {b}"
    assert moved == len(plan), (moved, len(plan))
    print(f"{'reverted' if a.revert else 'written'}: {moved} cells; every other row identical (row-by-row proof); sha256 {sha(raw)[:12]} -> {sha(raw2)[:12]}")
    if not a.revert:
        (WORK / "amort_split_manifest.json").write_text(json.dumps(
            {"master": MASTER.name, "quarter": quarter, "cells_changed": moved, "sha256_before": sha(raw), "sha256_after": sha(raw2),
             "companies": spec["companies"]}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
