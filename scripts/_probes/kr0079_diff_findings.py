# -*- coding: utf-8 -*-
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

baseline = json.load(open(ROOT / "artifacts/kics_validation/report_20260831T062516Z.json", encoding="utf-8"))
patched = json.load(open(ROOT / "artifacts/kics_validation/report_20260831T062448Z.json", encoding="utf-8"))

def kr0079_2026q2(report):
    out = []
    for f in report.get("findings", []):
        if f.get("원보험사코드") == "KR0079" and f.get("공시분기") == "2026.2Q":
            out.append(f)
    return out

b = kr0079_2026q2(baseline)
p = kr0079_2026q2(patched)

print(f"baseline KR0079 2026.2Q findings: {len(b)}")
for f in sorted(b, key=lambda x: str(x.get("rule"))):
    print("  BASE", f.get("status"), f.get("rule"), f.get("detail", "")[:160])

print()
print(f"patched KR0079 2026.2Q findings: {len(p)}")
for f in sorted(p, key=lambda x: str(x.get("rule"))):
    print("  PATCH", f.get("status"), f.get("rule"), f.get("detail", "")[:160])

print()
b_red = [f for f in b if f.get("status") == "RED"]
p_red = [f for f in p if f.get("status") == "RED"]
print(f"baseline RED count for KR0079 2026.2Q: {len(b_red)}")
for f in b_red:
    print("  BASE RED", f.get("rule"), f.get("detail", ""))
print(f"patched RED count for KR0079 2026.2Q: {len(p_red)}")
for f in p_red:
    print("  PATCH RED", f.get("rule"), f.get("detail", ""))
