# -*- coding: utf-8 -*-
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
BEFORE = REPO / "artifacts" / "kics_validation" / "report_20260831T053500Z.json"
AFTER = REPO / "artifacts" / "kics_validation" / "report_20260831T054238Z.json"

CODE = "KR0075"
QUARTER = "2026.2Q"


def load_findings(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    findings = d.get("findings", [])
    return [f for f in findings
            if f.get("원보험사코드") == CODE and f.get("공시분기") == QUARTER]


before = load_findings(BEFORE)
after = load_findings(AFTER)

print(f"BEFORE: {len(before)} findings for {CODE} {QUARTER}")
for f in sorted(before, key=lambda f: str(f.get("rule"))):
    print(f"  [{f.get('status')}] {f.get('rule')}: expected={f.get('expected')} actual={f.get('actual')} diff={f.get('diff')}")
    print(f"      {f.get('detail')}")

print()
print(f"AFTER: {len(after)} findings for {CODE} {QUARTER}")
for f in sorted(after, key=lambda f: str(f.get("rule"))):
    print(f"  [{f.get('status')}] {f.get('rule')}: expected={f.get('expected')} actual={f.get('actual')} diff={f.get('diff')}")
    print(f"      {f.get('detail')}")

# Diff by rule
before_by_rule = {f.get("rule"): f.get("status") for f in before}
after_by_rule = {f.get("rule"): f.get("status") for f in after}
all_rules = sorted(set(before_by_rule) | set(after_by_rule))
print()
print("=== STATUS DIFF (rule: before -> after) ===")
for r in all_rules:
    b = before_by_rule.get(r, "<absent>")
    a = after_by_rule.get(r, "<absent>")
    marker = "  " if b == a else "**"
    print(f"{marker} {r}: {b} -> {a}")
