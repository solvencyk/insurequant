# -*- coding: utf-8 -*-
"""Companion to mirae_2025q4_item6_nullify.py: keep data/_derived/pl_breakdown_coverage.json
consistent with the master now that KR0079 2025.4Q item6 is None instead of 0.0. Mirrors
build_pl_breakdown.py's own coverage-status logic exactly (missing = [n for n in range(1,25)
if v[n] is None]; status = "ok" if not missing else "partial" since t1 is clearly present for
this row -- item1-3/7 etc are populated). Surgical: only this one (code,quarter) record.
"""
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "data/_derived/pl_breakdown_coverage.json"
BACKUP = PATH.with_name(PATH.name + ".bak_20260829_item6_nullify")

shutil.copy2(PATH, BACKUP)
print(f"backup -> {BACKUP}")

rows = json.loads(PATH.read_text(encoding="utf-8"))
hit = [r for r in rows if r.get("code") == "KR0079" and r.get("quarter") == "2025.4Q"]
assert len(hit) == 1, f"expected exactly 1 coverage row, got {len(hit)} -- ABORT"
r = hit[0]
assert r["status"] == "ok" and r["missing"] == [], f"unexpected pre-state {r} -- ABORT"
r["missing"] = [6]
r["status"] = "partial"
# tier2 intentionally untouched -- that field tracks the Tier-2-vs-Tier-1 RECONCILIATION gate
# (whether the LOB breakdown's own internal math tied out), which item6's self-abstain never
# tripped; it is a different concept from "which numbered item is null".

PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {PATH}  ({len(rows)} rows)")

before = json.loads(BACKUP.read_text(encoding="utf-8"))
after = json.loads(PATH.read_text(encoding="utf-8"))
diffs = [(i, b, a) for i, (b, a) in enumerate(zip(before, after)) if b != a]
print(f"rows total: {len(after)}  rows changed: {len(diffs)}")
for i, b, a in diffs:
    print(f"  idx {i}\n    before: {b}\n    after : {a}")
