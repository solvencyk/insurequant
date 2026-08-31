# -*- coding: utf-8 -*-
"""Filter a validate_kics_disclosure.py report_*.json to KR0002 2026.2Q findings only."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

report_path = Path(sys.argv[1])
report = json.loads(report_path.read_text(encoding="utf-8"))
findings = report.get("findings", [])

sub = [f for f in findings if f.get("원보험사코드") == "KR0002" and f.get("공시분기") == "2026.2Q"]
sub.sort(key=lambda f: str(f.get("rule")))
print(f"=== {report_path.name}: {len(sub)} findings for KR0002 2026.2Q ===")
for f in sub:
    print(f"  rule={f.get('rule'):30s} status={f.get('status'):6s} expected={f.get('expected')!r:>14} "
          f"actual={f.get('actual')!r:>14} diff={f.get('diff')!r}")
    detail = f.get("detail")
    if detail:
        print(f"      detail: {detail[:200]}")

# also structural gates
print("\n--- coverage_census ---")
cc = report.get("coverage_census", {})
missing_kr0002 = [r for r in cc.get("missing_rows", []) if r.get("code") == "KR0002"]
print(f"missing_rows for KR0002: {missing_kr0002}")
print(f"collapsed_quarters: {cc.get('collapsed_quarters')}")

print("\n--- parent_zero_child_nonzero (KR0002) ---")
for r in report.get("parent_zero_child_nonzero", []):
    if r.get("code") == "KR0002":
        print(r)

print("\n--- parent_present_child_incomplete (KR0002) ---")
ppc = report.get("parent_present_child_incomplete", {})
for k in ("partial_red", "full_absent"):
    for r in ppc.get(k, []):
        if isinstance(r, dict) and r.get("code") == "KR0002":
            print(k, r)
