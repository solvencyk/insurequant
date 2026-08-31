# -*- coding: utf-8 -*-
import sys, io, json, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
from pathlib import Path
import fill_period_to_disclosure as fp

MASTER = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json")
rows = json.loads(MASTER.read_text(encoding="utf-8"))
F = fp._fields()
fp._process(rows, ["FY2026_Q2"], False, F, target_quarter=None)

items = sorted(set(int(r["항목번호"]) for r in rows if r["원보험사코드"]=="KR0001" and r["공시분기"]=="2026.2Q" and str(r["항목번호"]).isdigit()))
print("KR0001 2026.2Q items after stage A:", items)
for it in [17, 18, 19]:
    v = [r for r in rows if r["원보험사코드"]=="KR0001" and r["공시분기"]=="2026.2Q" and r["항목번호"]==it]
    print(f"  item{it}:", v)
