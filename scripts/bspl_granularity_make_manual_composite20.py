#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 10 helper (2026-10-11): release the KR0095 (메트라이프생명) item 20 cells that Stage B held as HOLD_TRIO.

The master's item 20 for KR0095 is the DART line 「보험계약부채」, which includes the separate account: at the three year-end
anchors it equals 8-1 「보험계약부채」(general account) + 「특별계정부채」 exactly (177,569.8 / 204,552.5 / 240,230.8억, reproduced from
the prior-year-end column of seven later filings, rule `20:보험계약부채+특별계정부채`, calibration `accepted`).  The reserve-trio gate
compares with the summary 「책임준비금」, which is the general account only, so it cannot apply to this definition.  Every cell is copied
from the Stage B candidate file; the two statement lines are re-read from the Stage A table for the basis text.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_make_manual_composite20.py
  ... scripts/bspl_granularity_load_bs.py --status NONE --manual data/_derived/bspl_granularity_20261011/manual_round10.json --round 10 [--apply]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates" / "KR0095.json"
TABLES = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "tables"
OUT = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "manual_round10.json"
TAIL = " (inbox/parser/20261011T0310Z bspl granularity)"
RULE = "20:보험계약부채+특별계정부채"


def main():
    d = json.loads(CAND.read_text(encoding="utf-8"))
    cells = []
    for c in d["candidates"]:
        if c["item"] != 20 or c.get("rule") != RULE or c["status"] != "HOLD_TRIO":
            continue
        tb = json.loads((TABLES / f"KR0095_{c['quarter']}.json").read_text(encoding="utf-8"))
        t = next(t for t in tb["tables"] if t["kind"] == "bs_full" and t["page"] == c["page"])
        rows = {r["label"]: r["vals"] for r in t["rows"]}
        a, b = rows["보험계약부채"][0], rows["특별계정부채"][0]
        tot_mn = (a + b) * 1e-6
        if abs(tot_mn - c["value_mn"]) > 0.05:
            raise SystemExit(f"ABORT: {c['quarter']} components {tot_mn} != candidate {c['value_mn']}")
        c = dict(c)
        c["status"] = "MANUAL"
        c["basis"] = (
            f"정기경영공시 {c['quarter']} 8-1 재무상태표(별도, 단위 원) p{c['page']} 「보험계약부채」 {a:,.0f}원 + 「특별계정부채」 {b:,.0f}원 "
            f"= {tot_mn / 100:,.1f}억. 마스터(DART) 항목 20 의 정의 = 일반계정 보험계약부채 + 특별계정부채: 같은 합이 마스터 연말 앵커 "
            f"2023.4Q 177,569.8 · 2024.4Q 204,552.5 · 2025.4Q 240,230.8억을 7개 공시의 전기말 열에서 0.1억 이내로 재현한다(보정 통과, "
            f"일반계정만의 값은 3개 앵커 모두 불일치). 요약 재무상태표 「책임준비금」은 일반계정만이라 책임준비금 3종 게이트는 이 정의에 적용 제외. "
            f"분기 흐름이 앵커 사이에서 연속이다." + TAIL)
        cells.append(c)
        print(c["quarter"], f"{tot_mn / 100:,.1f}억", "= %.1f + %.1f" % (a * 1e-8, b * 1e-8), "p", c["page"])
    if not cells:
        raise SystemExit("ABORT: no HOLD_TRIO composite cells found (candidates already refreshed?)")
    OUT.write_text(json.dumps({"_note": "round 10: KR0095 item 20 = 일반계정 보험계약부채 + 특별계정부채 (HOLD_TRIO released)", "cells": cells},
                              ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("wrote", OUT, len(cells), "cells")


if __name__ == "__main__":
    main()
