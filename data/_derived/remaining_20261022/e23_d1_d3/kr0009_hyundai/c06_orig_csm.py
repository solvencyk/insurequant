# -*- coding: utf-8 -*-
"""read-only: CSM roll-forward (issued long-term contracts, CURRENT period) of the ORIGINAL FY2023 Q3 / annual filings with the verifier's own table finder"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import kr0009_verify as V
sys.stdout.reconfigure(encoding="utf-8")
for key, q in (("O3", "2023.3Q"), ("O4", "2023.4Q")):
    try:
        T = V.csm_cur_table(key, q)
    except Exception as e:
        print(key, q, "csm_cur_table failed:", repr(e)[:300])
        continue
    print(key, q, T["table"], T["unit"])
    for i in range(1, 7):
        r = T["rows"].get(i)
        print("   item", i, None if r is None else (r["label"], r["printed"], r["line"], round(r["mn"] / 100.0, 5)))
