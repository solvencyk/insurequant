# -*- coding: utf-8 -*-
import sys, glob
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val")
from vtab import load_tables
from vte import tagged_rows, period_of
R = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/"
files = {
 "FY2024_Q4": "FY2024_Q4/raw/KR0087_동양생명_20250319000486/20250319000486.xml",
 "FY2025_Q3": "FY2025_Q3/raw/KR0087_동양생명/xml/20251114002594.xml",
 "FY2025_Q4": "FY2025_Q4/raw/KR0087_동양생명_20260313001227/20260313001227.xml",
}
for q, f in files.items():
    print("=====", q)
    tabs, _ = load_tables(R + f)
    n = 0
    for s, e, rows in tabs:
        j = " ".join(" ".join(r) for r in rows)
        if "출재보험계약" in j and "위험조정 상각액" in j:
            for r in rows:
                t = " ".join(r)
                if "당기손익으로 인식한 보험계약마진" in t or "위험조정 상각액" in t:
                    print(f"  T{s}: " + " | ".join(r)[:200]); n += 1
    if n == 0:
        rows = tagged_rows(R + f, 1, 10**9)
        for r in rows:
            lab = " / ".join(l for l in r["labels"] if l.strip())
            if "재보험" in lab and ("계약마진" in lab and ("당기손익" in lab or "서비스의 이전" in lab)) or ("재보험" in lab and "위험조정" in lab and "변동분" in lab):
                print(f"  L{r['line']} {lab[-80:]} || " + " ; ".join(f"{period_of(c)}={t}" for c, _, t in r["cells"]))
