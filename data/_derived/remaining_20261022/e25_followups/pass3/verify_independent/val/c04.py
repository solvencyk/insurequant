# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val")
from vte import tagged_rows, period_of
R = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/"
for q, f in {"FY2025_Q4":"FY2025_Q4/raw/KR0087_동양생명_20260313001227/20260313001227.xml","FY2025_Q3":"FY2025_Q3/raw/KR0087_동양생명/xml/20251114002594.xml"}.items():
    print("=====", q)
    rows = tagged_rows(R + f, 1, 10**9)
    for r in rows:
        lab = " / ".join(l for l in r["labels"] if l.strip())
        if ("재보험" in lab and "계약마진" in lab and ("비용" in lab or "수익" in lab)) or ("재보험" in lab and "위험조정" in lab and ("비용" in lab or "수익" in lab)):
            print(f"  L{r['line']} {lab[-90:]} || " + " ; ".join(f"{period_of(c)}={t}" for c, _, t in r["cells"]))
