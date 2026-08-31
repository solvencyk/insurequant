# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
rep = json.loads((ROOT / "artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))
findings = rep["findings"]
kr0029 = [f for f in findings if f.get("원보험사코드") == "KR0029"]
by_q = {}
for f in kr0029:
    by_q.setdefault(f.get("공시분기"), {"GREEN":0,"YELLOW":0,"RED":0,"SKIP":0})
    by_q[f.get("공시분기")][f.get("status")] = by_q[f.get("공시분기")].get(f.get("status"),0) + 1
for q in sorted(by_q):
    print(q, by_q[q])
print("\nRED details:")
for f in kr0029:
    if f.get("status") == "RED":
        print(" ", f.get("공시분기"), f.get("rule"), "expected=", f.get("expected"), "actual=", f.get("actual"))
