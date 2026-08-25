# -*- coding: utf-8 -*-
"""lob_sum_gap 5건 -- item1/2/13/14/15/16 (+3/8) 덤프해 기타영업수익/기타사업비용 결측 여부 확인.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_lobsumgap_items.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

ITEM_NM = {1: "보험손익", 2: "생명장기손익", 3: "생명장기원수손익", 8: "생명장기재보험손익",
           13: "자동차손익", 14: "일반손익", 15: "기타영업수익", 16: "기타사업비용"}

TARGETS = [("DB생명보험", "2023.1Q"), ("DB손해보험", "2023.2Q"),
           ("메리츠화재해상보험", "2023.1Q"), ("메리츠화재해상보험", "2023.2Q"),
           ("흥국화재", "2025.1Q")]


def main() -> int:
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    by = defaultdict(dict)
    for r in rows:
        by[(r["원수사명"], r["공시분기"])][r["항목번호"]] = r.get("값")
    for nm, q in TARGETS:
        m = by.get((nm, q), {})
        print(f"\n[{nm} {q}]")
        for i in (1, 2, 3, 8, 13, 14, 15, 16):
            print(f"  item{i:<2d} {ITEM_NM[i]:12s} = {m.get(i)}")
        bo = m.get(1)
        lob = [m.get(2), m.get(13), m.get(14)]
        if bo is not None and None not in lob:
            bare = sum(lob)
            print(f"  bare = item2+13+14 = {bare:,.3f}   보험손익(item1) = {bo:,.3f}   diff(bare-bo) = {bare-bo:,.3f}")
            oi, oe = m.get(15), m.get(16)
            if oi is not None and oe is not None:
                adj = bare + oi - oe
                print(f"  adj = bare+15-16 = {adj:,.3f}   diff(adj-bo) = {adj-bo:,.3f}")
            else:
                print(f"  adj 평가불가 (item15={oi} item16={oe})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
