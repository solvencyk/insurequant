# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BEFORE = "artifacts/kics_validation/report_20260831T073827Z.json"
AFTER = "artifacts/kics_validation/report_20260831T075107Z.json"

def kr0010_2q_findings(path):
    with open(path, "r", encoding="utf-8") as f:
        r = json.load(f)
    fs = [f for f in r["findings"] if f.get("원보험사코드") == "KR0010" and f.get("공시분기") == "2026.2Q"]
    return fs

before = kr0010_2q_findings(BEFORE)
after = kr0010_2q_findings(AFTER)

print(f"BEFORE: {len(before)} findings for KR0010 2026.2Q")
for f in sorted(before, key=lambda f: (f["status"] != "RED", f["rule"])):
    print(f"  [{f['status']:6s}] {f['rule']:35s} expected={f['expected']!r} actual={f['actual']!r} diff={f.get('diff')!r}")
    if f["status"] in ("RED","YELLOW"):
        print(f"           detail: {f['detail'][:200]}")

print(f"\nAFTER: {len(after)} findings for KR0010 2026.2Q")
for f in sorted(after, key=lambda f: (f["status"] != "RED", f["rule"])):
    print(f"  [{f['status']:6s}] {f['rule']:35s} expected={f['expected']!r} actual={f['actual']!r} diff={f.get('diff')!r}")
    if f["status"] in ("RED","YELLOW"):
        print(f"           detail: {f['detail'][:300]}")

before_red = [f["rule"] for f in before if f["status"] == "RED"]
after_red = [f["rule"] for f in after if f["status"] == "RED"]
print(f"\nBEFORE RED rules ({len(before_red)}): {before_red}")
print(f"AFTER  RED rules ({len(after_red)}): {after_red}")

before_status_counts = {}
for f in before: before_status_counts[f["status"]] = before_status_counts.get(f["status"],0)+1
after_status_counts = {}
for f in after: after_status_counts[f["status"]] = after_status_counts.get(f["status"],0)+1
print(f"\nBEFORE status counts: {before_status_counts}")
print(f"AFTER  status counts: {after_status_counts}")
