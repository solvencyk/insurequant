# -*- coding: utf-8 -*-
"""Read-only: census absence verdicts after the 2026-08-22 iter-5 rewire,
run with the SAME sidecar loader the gate uses. Modifies nothing."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from solvency.validation.kics_json_rules import run_validation  # noqa: E402
from validate_kics_disclosure import (  # noqa: E402
    _load_tfi_applicability, _scan_breakdown_presence,
)

records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
tfi = _load_tfi_applicability()
print(f"sidecar entries loaded = {len(tfi)}  "
      f"({Counter(tfi.values())})")
print()

report = run_validation(records, source_has_breakdown=_scan_breakdown_presence(records),
                        tfi_applicability=tfi)
findings = report["findings"]
CENSUS = {"47_tier2_census", "47_tier2_census_post"}

cnt = Counter()
rows = []
for f in findings:
    if f["rule"] not in CENSUS:
        continue
    det = f.get("detail", "")
    if "TIER2_TABLE_ABSENT" not in det:
        continue
    tag = det.split(":")[0]
    cnt[(f["status"], tag)] += 1
    rows.append((f["rule"], f.get("원보험사코드"), f.get("원수사명"),
                 f.get("공시분기"), f["status"], tag))

print("=== absence verdicts (both columns) ===")
for k, v in sorted(cnt.items()):
    print(f"  {k[0]:7s} {k[1]:46s} {v}")
print(f"  TOTAL absence findings = {sum(cnt.values())}")
print()

print("=== every absence bucket, 적용전 column only ===")
for r in sorted(set(x for x in rows if x[0] == "47_tier2_census"),
                key=lambda x: (x[4], x[1], x[3])):
    print(f"  {r[4]:7s} {r[1]} {r[2]:22s} {r[3]}  {r[5]}")
print()

print("=== blocking RED by rule ===")
blocking = Counter()
for f in findings:
    if f.get("status") == "RED":
        blocking[f["rule"]] += 1
for k, v in blocking.most_common():
    print(f"  {k:28s} {v}")
print(f"  TOTAL RED = {sum(blocking.values())}")
