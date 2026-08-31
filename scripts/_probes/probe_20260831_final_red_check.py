# -*- coding: utf-8 -*-
import sys, io, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

latest = sorted(glob.glob(r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\kics_validation\report_2026*.json"))[-1]
print("using report:", latest)
report = json.loads(Path(latest).read_text(encoding="utf-8"))
CODES = {"KR0069", "KR0070", "KR0082", "KR0001", "KR0073", "KR1011"}

findings = report.get("findings") or report.get("results") or []
if not findings:
    # try nested keys
    print("top-level keys:", list(report.keys()))
else:
    red_mine_2q = [f for f in findings if f.get("code") in CODES and f.get("quarter") == "2026.2Q" and f.get("status") == "RED"]
    print(f"RED findings for my 6 companies at 2026.2Q: {len(red_mine_2q)}")
    for f in red_mine_2q[:30]:
        print(" ", f)
