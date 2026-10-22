"""w4_hd_ir_legs: read the prior-year (cumulative) LOB insurance result of 현대해상 from the IR factsheet '(3) UW Income' of the LATER year (FY2024_Q1 -> 2023.1Q, FY2024_Q2 -> 2023.2Q).
Rows: block label in col A/B ('일반','장기','자동차') followed later by the row '보 험 손 익' (the first such row after the block label); the LAST numeric cell of the row = prior-year 누계.
Writes hd_ir_legs.json  {"KR0009|2023.1Q": {"2": 장기, "13": 자동차, "14": 일반, "sum": 합계, "cells": {...}}}  READ-ONLY."""
import json
import sys
import openpyxl
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/data/ir/"
FILES = {"2023.1Q": "FY2024_Q1/raw/KR0009_현대해상/dd7e547e6e1f9cc171b77dcb4bf67d58.xlsx", "2023.2Q": "FY2024_Q2/raw/KR0009_현대해상/d33c3d385303361798f75607750ca360.xlsx"}
out = {}
for q, f in FILES.items():
    wb = openpyxl.load_workbook(ROOT + f, data_only=True)
    ws = wb["(3) UW Income"]
    blk, res = None, {}
    for row in ws.iter_rows():
        labs = [c for c in row if isinstance(c.value, str)]
        txt = [c.value.replace(" ", "") for c in labs]
        for c in labs:
            v = c.value.replace(" ", "")
            if v in ("일반", "장기", "자동차") and c.column <= 2:
                blk = v
        if "보험손익" in txt or "보험손익합계" in txt:
            nums = [c for c in row if isinstance(c.value, (int, float))]
            if not nums:
                continue
            key = "합계" if "보험손익합계" in txt else blk
            if key not in res:
                res[key] = {"value_mn": nums[-1].value, "cell": nums[-1].coordinate, "row": row[0].row}
    out[f"KR0009|{q}"] = {"file": "data/ir/" + f, "sheet": "(3) UW Income", "2": res["장기"]["value_mn"], "13": res["자동차"]["value_mn"], "14": res["일반"]["value_mn"], "sum": res["합계"]["value_mn"], "cells": res}
    s = res["장기"]["value_mn"] + res["자동차"]["value_mn"] + res["일반"]["value_mn"]
    print(q, {k: (v["value_mn"], v["cell"]) for k, v in res.items()}, "legs sum", round(s, 3), "vs 합계", round(res["합계"]["value_mn"], 3))
open("hd_ir_legs.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
