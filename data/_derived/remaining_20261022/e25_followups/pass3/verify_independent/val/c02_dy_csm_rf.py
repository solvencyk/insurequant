# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val")
from vtab import load_tables
R = "C:/Users/sangwook.cho/Desktop/insurequant/data/dart/"
files = {
 "FY2024_Q2": "FY2024_Q2/raw/KR0087_동양생명/20240814002284.xml",
 "FY2025_Q1": "FY2025_Q1/raw/KR0087_동양생명/20250515001025.xml",
}
for q, f in files.items():
    tabs, _ = load_tables(R + f)
    print("=====", q)
    for s, e, rows in tabs:
        j = " ".join(" ".join(r) for r in rows)
        if "출재보험계약" in j and "비금융위험에 대한 위험조정 상각액" in j:
            for r in rows:
                if r and ("당기손익으로 인식한 보험계약마진" in " ".join(r) or "위험조정 상각액" in " ".join(r) or r[0].startswith("구분") or "기초" in r[0] or "기말" in r[0] or "순자산" in r[0]):
                    print(f"  T{s}: " + " | ".join(r)[:230])
