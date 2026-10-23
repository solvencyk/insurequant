# -*- coding: utf-8 -*-
"""read-only exploration of the IR factsheet sheets with the zipfile reader of hd_lib"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import hd_lib as H
sys.stdout.reconfigure(encoding="utf-8")
IR = {
 "Q1": "data/ir/FY2024_Q1/raw/KR0009_현대해상/dd7e547e6e1f9cc171b77dcb4bf67d58.xlsx",
 "Q2": "data/ir/FY2024_Q2/raw/KR0009_현대해상/d33c3d385303361798f75607750ca360.xlsx",
 "Q3": "data/ir/FY2024_Q3/raw/KR0009_현대해상/7a517f00b391c158b282d1412c609776.xlsx",
 "Q4": "data/ir/FY2024_Q4/raw/KR0009_현대해상/2a11f147695dacd4665923059eceed11.xlsx",
}
for k, rel in IR.items():
    S = H.read_xlsx_sheet(rel, "(3) UW Income")
    print("=" * 90)
    print(k, rel)
    for c in ("B1", "L4", "B5", "F5", "K5", "E6", "F6", "I6", "K6", "L6", "M6", "N6"):
        print("  ", c, repr(S.get(c)))
    for r in (8, 11, 12, 26, 27, 30, 31):
        print("  row", r, {c: S.get(f"{c}{r}") for c in "BCDEFGHIJKLMN" if S.get(f"{c}{r}") is not None})
