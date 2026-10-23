# -*- coding: utf-8 -*-
"""READ-ONLY control test: the SAME reader applied to the CURRENT-period cumulative column of the FY2024 filings must reproduce the live master items 6 / 11 / 4 / 5 / 9 / 10 for 2024.1Q-2024.4Q
(items the production builder already extracts from these notes).  Mismatches show where the live master itself is on a different leg (reported, not changed here)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/kr0070_abl"
d = json.load(open(f"{EV}/a01_read_abl_fy2023.json", encoding="utf-8"))
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
gold = {(e["공시분기"], e["항목번호"]): e for e in json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))["set"] if e["원보험사코드"] == "KR0070"}
MAP = {"2023.1Q": "2024.1Q", "2023.2Q": "2024.2Q", "2023.3Q": "2024.3Q", "2023.4Q": "2024.4Q"}
def v(x):
    return x if isinstance(x, (int, float)) else x[0]
for q0, q1 in MAP.items():
    cc = d[q0]["cur_cum"]
    row = []
    for it in (4, 5, 6, 9, 10, 11):
        val = v(cc[str(it)])
        if it in (9, 10):
            val = -abs(val)
        lv = live.get((q1, it), {}).get("값")
        flag = "OK" if lv is not None and abs(lv - val) <= 0.5 else ("DIFF" if lv is not None else "live blank")
        row.append(f"item{it}: reader {val:>9.0f} vs live {lv!s:>10} [{flag}]{' gold' if (q1, it) in gold else ''}")
    print(q1, " | ".join(row))
