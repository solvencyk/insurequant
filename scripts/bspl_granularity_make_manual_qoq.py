#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 9 helper: release three HOLD_QOQ cells whose printed value was verified by rendering the page (2026-10-11).

Writes data/_derived/bspl_granularity_20261011/manual_round9.json (candidate schema + explicit `basis`), to be loaded with
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_load_bs.py --status NONE \
      --manual data/_derived/bspl_granularity_20261011/manual_round9.json --round 9 [--apply]
Each cell is copied from the Stage B candidate file (value, page, pdf, sha256, unit...), so nothing is retyped.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
OUT = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "manual_round9.json"
TAIL = " (inbox/parser/20261011T0310Z bspl granularity)"

BASIS = {
    ("KR0051", 10, "2025.1Q"): (
        "정기경영공시 2025.1Q 8-1 재무상태표(단위 원) p20 라인「Ⅰ. 현금 및 예치금」111,538,371,403원(= 1,115.38억)을 렌더링해 육안 확인. "
        "전기말 191.0억(인쇄 19,101,715,054원, 마스터와 동일)에서 약 5.8배로 늘었으나 같은 분기 자본금이 1,062.1억에서 1,911.3억으로 "
        "+849.2억 증가(증자)하고 자산총계도 2,898.7억에서 3,814.1억으로 늘어 현금 급증과 방향·크기가 맞으며, 다음 분기 109.4억으로 "
        "돌아오면서 당기손익-공정가치측정금융자산이 552.8억에서 1,255.6억으로 늘어(투자 집행) 설명된다. 전분기 대비 변동 보류(HOLD_QOQ)를 해제."),
    ("KR1011", 10, "2026.1Q"): (
        "정기경영공시 2026.1Q 8-1 재무상태표(단위 원) p26 라인「Ⅰ.현금및예치금」135,527,750,202원(= 1,355.28억 = 현금및현금성자산 "
        "132,836,882,506원 + 상각후원가예치금 2,690,867,696원)을 렌더링해 육안 확인. 전기말은 인쇄 572,334,069,587원(= 5,723.34억)으로 "
        "마스터와 동일. 이 회사 현금및예치금은 매 4Q 말 급증했다가 1Q 에 크게 줄고(2024.1Q -43%, 2025.1Q -44%) 2023.2Q 1,438.6억 같은 "
        "저점도 있는 변동성 큰 계열이다. 전분기 대비 변동 보류(HOLD_QOQ)를 해제."),
    ("KR0068", 24, "2023.1Q"): (
        "정기경영공시 2023.1Q 8-1 별도재무상태표(단위 원) p19~20 라인「9. 기타부채」66,440,558,532원(= 664.41억)을 렌더링해 육안 확인. "
        "같은 표의 보험계약부채 87,332,957,383,427원·재보험계약부채 30,052,676,338원이 마스터(DART)와 동일. 이 회사 기타부채 계열은 "
        "157.1억(2023.2Q)~995.8억(2024.2Q) 사이에서 크게 오르내린다. 전분기 대비 변동 보류(HOLD_QOQ)를 해제."),
}


def main():
    cells = []
    for (code, item, q), basis in BASIS.items():
        d = json.loads((CAND / f"{code}.json").read_text(encoding="utf-8"))
        hit = [c for c in d["candidates"] if c["item"] == item and c["quarter"] == q]
        if len(hit) != 1:
            raise SystemExit(f"ABORT: candidate {code}|{item}|{q}: {len(hit)} matches")
        c = dict(hit[0])
        if c["status"] != "HOLD_QOQ":
            raise SystemExit(f"ABORT: {code}|{item}|{q} status is {c['status']}, expected HOLD_QOQ")
        c["status"] = "MANUAL"
        c["basis"] = basis + TAIL
        cells.append(c)
        print(code, item, q, round(c["value_mn"] / 100, 2), c["kind"], "p", c["page"], c["calib"])
    OUT.write_text(json.dumps({"_note": "round 9: HOLD_QOQ cells released after rendering the PDF page", "cells": cells},
                              ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
