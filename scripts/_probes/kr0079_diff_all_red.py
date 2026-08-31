# -*- coding: utf-8 -*-
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

baseline = json.load(open(ROOT / "artifacts/kics_validation/report_20260831T062516Z.json", encoding="utf-8"))
patched = json.load(open(ROOT / "artifacts/kics_validation/report_20260831T062448Z.json", encoding="utf-8"))

def red_keys(report):
    out = set()
    for f in report.get("findings", []):
        if f.get("status") == "RED":
            out.add((f.get("원보험사코드"), f.get("공시분기"), f.get("rule")))
    return out

b = red_keys(baseline)
p = red_keys(patched)

only_baseline = b - p  # fixed by patch
only_patched = p - b   # NEW red introduced by patch -- should be EMPTY

print(f"baseline RED (unique co,q,rule) = {len(b)}")
print(f"patched RED (unique co,q,rule)  = {len(p)}")
print()
print(f"RED fixed by patch (baseline only) = {len(only_baseline)}")
for k in sorted(only_baseline):
    print("  fixed:", k)
print()
print(f"NEW RED introduced by patch (patched only, should be 0) = {len(only_patched)}")
for k in sorted(only_patched):
    print("  NEW:", k)
