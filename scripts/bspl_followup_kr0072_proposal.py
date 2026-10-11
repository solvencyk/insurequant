#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 3 finding F-1: proposal (NOT applied) for KR0072 PL item 10, 4 cells that hold the 3개월
column instead of the 누적 (YTD) column.  Reads finding_kr0072_item10_3month_vs_cumulative.json (scripts/bspl_followup_kr0072_item10.py).
Output: data/_derived/bspl_followup_20261011/proposed_pl_corrections_kr0072_item10.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
W = ROOT / "data" / "_derived" / "bspl_followup_20261011"


def num(s):
    s = s.strip()
    neg = s.startswith("(")
    v = float(s.strip("()").replace(",", ""))
    return -v if neg else v


def main():
    fin = json.loads((W / "finding_kr0072_item10_3month_vs_cumulative.json").read_text(encoding="utf-8"))
    cells = []
    for r in fin:
        q = r["quarter"]
        if q not in ("2023.2Q", "2023.3Q", "2024.2Q", "2024.3Q"):
            continue
        row = r["ra_release_rows"][1]                    # second occurrence = 재보험 (first = 원수)
        three, cum = num(row["row"][1]), num(row["row"][2])
        old = r["master_item10_ytd_qtr"][0]
        cells.append({"key": f"KR0072|10|{q}", "master_ytd": old, "printed_3month": three, "printed_cumulative": cum,
                      "proposed_ytd": -abs(cum) if old < 0 else abs(cum),
                      "master_equals_3month": abs(abs(old) - abs(three)) < 1e-9,
                      "source": {"xml": r["xml"], "table_line": row["line"], "row": row["row"][:5]}})
    out = {"_what": "KR0072 재보험 위험조정 변동(항목 10): 마스터 값이 3개월 열(머리글 없는 두 번째 표에서 첫 숫자). 제안 = 누적 열. 적용 안 함: 핸들러 수정 + PL 골든 재생성이 필요.",
           "cells": cells, "other_companies_checked": "KR0083·KR0094·KR0104 항목 10 은 전 분기 YTD 가 누적 추세(정상). KR0071 은 아래 별건.",
           "kr0071_unverified_observation": "KR0071 항목 10: 2023.2Q −222 → 2023.3Q −9,895 → 2023.4Q −9,641 → 2024.1Q −150 (급변, 원천 미확인)"}
    (W / "proposed_pl_corrections_kr0072_item10.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for c in cells:
        print(c["key"], "master", c["master_ytd"], "3개월", c["printed_3month"], "누적", c["printed_cumulative"], "-> proposed", c["proposed_ytd"],
              "| master==3개월:", c["master_equals_3month"])


if __name__ == "__main__":
    main()
