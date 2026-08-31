# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
from pathlib import Path
import fill_period_to_disclosure as fp
import fill_market_subitems_to_disclosure as fm

MASTER = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\kics_disclosure.json")
rows = json.loads(MASTER.read_text(encoding="utf-8"))
F = fp._fields()
fp._process(rows, ["FY2026_Q2"], False, F, target_quarter=None)
item19 = [r for r in rows if r["원보험사코드"] == "KR0069" and r["공시분기"] == "2026.2Q" and r["항목번호"] == 19]
print("item19 after stage A:", item19)

# IRR debug
import fitz
PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2026_Q2\pdf\KR0069_삼성생명.pdf")
doc = fitz.open(PDF)
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "순자산가치" in t and "금리상승" in t and "금리하락" in t:
        print(f"page {i+1}: has 순자산가치+금리상승+금리하락, 평균회귀={'평균회귀' in t}, 금리경사={'금리경사' in t}")
doc.close()
