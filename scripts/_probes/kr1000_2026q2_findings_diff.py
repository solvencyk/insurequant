# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import validate_kics_disclosure as v

MASTER = ROOT / "kics_disclosure.json"
SCRATCH = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure_KR1000_2026Q2_scratch.json")

def kr1000_findings(path):
    records = v._load_records(path)
    report = v.run_validation(records,
                               source_has_breakdown=v._scan_breakdown_presence(records),
                               tfi_applicability=v._load_tfi_applicability())
    findings = [f for f in report.get("findings", [])
                if f.get(v.KEY_CODE) == "KR1000" and f.get(v.KEY_QUARTER) == "2026.2Q"]
    return report, findings

print("=== BEFORE (live master) ===")
report_before, f_before = kr1000_findings(MASTER)
for f in sorted(f_before, key=lambda x: str(x.get("rule"))):
    print(f"  rule={f.get('rule')!s:20} status={f.get('status')!s:8} item={f.get(v.KEY_ITEM)} "
          f"expected={f.get('expected')} disclosed={f.get('disclosed')} diff={f.get('diff')}")

print(f"\n=== AFTER (patched scratch) ===")
report_after, f_after = kr1000_findings(SCRATCH)
for f in sorted(f_after, key=lambda x: str(x.get("rule"))):
    print(f"  rule={f.get('rule')!s:20} status={f.get('status')!s:8} item={f.get(v.KEY_ITEM)} "
          f"expected={f.get('expected')} disclosed={f.get('disclosed')} diff={f.get('diff')}")

def status_counts(findings):
    from collections import Counter
    return Counter(f.get("status") for f in findings)

print(f"\nBEFORE status counts: {dict(status_counts(f_before))}")
print(f"AFTER  status counts: {dict(status_counts(f_after))}")
