# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
from pathlib import Path
import fill_period_to_disclosure as fp

MASTER = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json")
rows = json.loads(MASTER.read_text(encoding="utf-8"))
F = fp._fields()
fp._process(rows, ["FY2026_Q2"], False, F, target_quarter=None)
for code in ["KR0082", "KR1011", "KR0070"]:
    items = sorted(set(int(r["항목번호"]) for r in rows if r["원보험사코드"]==code and r["공시분기"]=="2026.2Q" and str(r["항목번호"]).isdigit()))
    missing = [i for i in range(1,29) if i not in items]
    print(f"{code}: items={items}")
    print(f"{code}: missing 1-28={missing}")
