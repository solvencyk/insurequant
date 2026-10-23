# -*- coding: utf-8 -*-
"""Custom reader KR0082 (DB생명), 2023.1Q-2023.4Q from the FY2024 filings, notes 22.1-22.4 (separate basis), prior-period column (2nd numeric cell).
Definitions verified on the CURRENT column against the master of quarter+4 (2024.x) before use:
  6  = (예상보험금 + 예상유지비 + 예상손해조사비 + 예상투자관리비) [22.1] - (발생보험금 + 발생직접유지비 + 손해조사비 + 투자관리비) [22.2]
  9  = -|보험계약마진상각| [22.4] ; 10 = -|비금융위험에 대한 위험조정상각| [22.4] ; 11 = 발생출재보험금 [22.3] - 예상출재보험금 [22.4]"""
import json, sys, re
sys.argv = [sys.argv[0], "__lib__"]
from n00_lib import *

REV = ["예상보험금", "예상유지비", "예상손해조사비", "예상투자관리비"]
COST = ["발생보험금", "발생직접유지비", "손해조사비", "투자관리비"]


def tables(path):
    lines, s0, tabs = s2lib.tables_sep2(path)
    out = {}
    for t, rows in tabs:
        cap = E.nl(t["caption"] or "")
        for key, pat in (("rev", "발행한보험계약의보험수익"), ("cost", "발행한보험계약의보험비용"), ("rerev", "보유한재보험계약의재보험수익"), ("recost", "보유한재보험계약의재보험비용")):
            if pat in cap and key not in out and len(rows) >= 4:
                out[key] = (t, rows)
    return out


def val(rows, label, col):
    for r in rows:
        lab, nums = split_row(r)
        if lab == label and len(nums) > col:
            return nums[col]
    return None


cells = []
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    c = "KR0082"
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    mq = f"{int(q[:4]) + 1}.{q[5:]}"
    path = T.main_path(c, fy)
    filing = str(path).replace("\\", "/").split("insurequant/")[-1]
    tb = tables(path)
    miss = [k for k in ("rev", "cost", "rerev", "recost") if k not in tb]
    if miss:
        print(q, "missing tables", miss)
        continue
    n_cols = len(split_row(tb["rev"][1][1])[1])
    cols = (("cur", 0), ("prior", 1)) if n_cols == 2 else (("cur", 1), ("prior", 3))
    print(q, "numeric columns per row", n_cols)
    for role, col in cols:
        a = [val(tb["rev"][1], x, col) for x in REV]
        b = [val(tb["cost"][1], x, col) for x in COST]
        rr = val(tb["rerev"][1], "발생출재보험금", col)
        re_ = val(tb["recost"][1], "예상출재보험금", col)
        cm = val(tb["recost"][1], "보험계약마진상각", col)
        ra = val(tb["recost"][1], "비금융위험에대한위험조정상각", col)
        if None in a or None in b or None in (rr, re_, cm, ra):
            print(q, role, "label missing", a, b, rr, re_, cm, ra)
            continue
        i6 = sum(abs(x[0]) for x in a) - sum(abs(x[0]) for x in b)
        vals = {"6": i6, "9": -abs(cm[0]), "10": -abs(ra[0]), "11": abs(rr[0]) - abs(re_[0])}
        lines_ = {"6": [x[1] for x in a + b], "9": [cm[1]], "10": [ra[1]], "11": [rr[1], re_[1]]}
        if role == "cur":
            print(q, "cur check vs master", mq, {k: (round(v, 1), pl.get((c, k, mq))) for k, v in vals.items()})
        else:
            for k, v in vals.items():
                cells.append(dict(company=c, quarter=q, item=k, master=pl.get((c, k, q)), latest=v, filing=filing, line=",".join(str(x) for x in lines_[k]), source="custom_kr0082",
                                  confidence="high", note=f"notes 22.1-22.4 prior column; cur column reproduces master {mq}: {pl.get((c, k, mq))}"))
json.dump(dict(cells=cells), open(S2 + "x02_kr0082.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in cells:
    print(x["quarter"], x["item"], x["master"], round(x["latest"], 1))
