# -*- coding: utf-8 -*-
import sys, glob, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val")
from vte import tagged_rows, period_of
R = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/"
files = {
 "FY2024_Q1": "FY2024_Q1/raw/KR0087_동양생명/20240516001580.xml",
 "FY2024_Q2": "FY2024_Q2/raw/KR0087_동양생명/20240814002284.xml",
 "FY2024_Q4": "FY2024_Q4/raw/KR0087_동양생명_20250319000486/20250319000486.xml",
 "FY2025_Q1": "FY2025_Q1/raw/KR0087_동양생명/20250515001025.xml",
 "FY2025_Q2": "FY2025_Q2/raw/KR0087_동양생명/xml/20250814002600.xml",
 "FY2025_Q3": "FY2025_Q3/raw/KR0087_동양생명/xml/20251114002594.xml",
 "FY2025_Q4": "FY2025_Q4/raw/KR0087_동양생명_20260313001227/20260313001227.xml",
 "FY2026_Q1": "FY2026_Q1/raw/KR0087_동양생명/20260529002292.xml",
 "FY2026_Q2": "FY2026_Q2/raw/KR0087_동양생명/20260814003397.xml",
}
KEYS = ["서비스의 이전으로 당기손익에 인식한 보험계약마진", "비금융위험에 대한 위험조정의 변동분", "재보험수익, 발생한 보험금", "재보험비용, 예상 보험금"]
for q, f in files.items():
    print("=====", q, f)
    try:
        rows = tagged_rows(R + f, 1, 10**9)
    except Exception as e:
        print("ERR", e); continue
    for r in rows:
        lab = " / ".join(l for l in r["labels"] if l.strip())
        if "재보험" in lab and any(k in lab for k in KEYS[:2]):
            print(f"L{r['line']} {lab[-70:]} || " + " ; ".join(f"{period_of(c)}={t}" for c, _, t in r["cells"]))
