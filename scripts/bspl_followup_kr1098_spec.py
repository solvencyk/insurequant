#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 1: correction spec for KR1098 (카카오페이손해보험) 자본금 2026.2Q.

The master / overlay / sidecar / vision part file hold 200,000 백만원; the disclosure prints 300,000,000,000원 (8-1 p44 = printed page 42,
verified on the rendered page) and the equity table (4-1) prints 3,000억 in every column of 2025.4Q..2026.2Q.  The balance sheet only closes
with 300,000 백만원.  Read-only; writes the spec JSON the applier consumes.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_kr1098_spec.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import fitz  # noqa: E402

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.pdfrows import rows_from_page  # noqa: E402
from bspl_granularity.tables import _rows_to_dict, comp  # noqa: E402
from bspl_granularity.views import view_all, cur, col  # noqa: E402

fitz.TOOLS.mupdf_display_errors(False)

OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "kr1098_fix_spec.json"
KEY = "KR1098|30|2026.2Q"


def main():
    all_v, anchor, disc, meta = B.load_master()
    old = all_v["KR1098"][(30, "2026.2Q")]
    doc = B.load_tables("KR1098", "2026.2Q")
    # Stage A did not classify this page (the heading prints '8-1. 재무상태' without '표', see bspl_followup_missed_bs_full.py):
    # read the statement page directly with the same row reader
    pdf = fitz.open(ROOT / doc["pdf"])
    pno = next(i for i in range(len(pdf)) if all(x in comp(pdf[i].get_text()) for x in ("8-1.", "재무상태", "자산총계", "자본총계"))) + 1
    rows, _free = rows_from_page(pdf[pno - 1], pageno=pno)
    t8 = {"kind": "bs_full", "page": pno, "unit": "원", "rows": _rows_to_dict(rows, pno)}
    assert pno == 44, pno
    va = view_all(t8)
    won = {k: cur(va[k][0]) for k in ("자본금", "자본조정", "AOCI", "자본총계", "자산총계", "부채총계")}
    # the retained-earnings label prints as '이익잉여금(결손금)' -> '이익잉여금결손금' (no canonical view): read the raw row
    re_row = next(r for r in t8["rows"] if r["label"].startswith("이익잉여금") and r["vals"])
    won["이익잉여금"] = re_row["vals"][0]
    prior = {k: col(va[k][0], 1) for k in ("자본금", "자본총계")}
    resid = won["자본총계"] - (won["자본금"] + won["자본조정"] + won["AOCI"] + won["이익잉여금"])
    tq = [t for t in doc["tables"] if t["kind"] == "equity"][0]
    vq = view_all(tq)
    eq_cols = [col(vq["자본금"][0], c) for c in range(3)]
    assert abs(won["자본금"] - 300_000_000_000) < 1 and resid == 0, (won, resid)
    assert eq_cols == [3000.0, 3000.0, 3000.0], eq_cols
    # what 200,000 백만원 would do to the identity
    resid_old = won["자본총계"] - (old * 1e6 + won["자본조정"] + won["AOCI"] + won["이익잉여금"])
    new_mn = round(won["자본금"] / 1e6, 6)
    side = json.loads((ROOT / "data" / "_derived" / "bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
    old_basis = side[KEY]["근거"]
    basis = ("정정 2026-10-11(inbox/parser/20261011T0900Z 단계 1): 이전 값 200,000백만원은 오독이었다. 2026.2Q 정기경영공시 재무제표 8-1 재무상태 "
             f"p{t8['page']}(인쇄 쪽 42, 렌더링으로 확인)의 「Ⅰ. 자본금」은 2026년 2/4분기 300,000,000,000원 · 2025년도 300,000,000,000원 · 증감 '-' 이고, "
             f"4-1 B/S상 자기자본(p{tq['page']})은 당분기·당분기-1·당분기-2 열이 모두 자본금 3,000억원이다. 자본총계 {won['자본총계']:,.0f}원 = "
             f"자본금 {won['자본금']:,.0f} + 자본조정 ({-won['자본조정']:,.0f}) + 기타포괄손익누계액 ({-won['AOCI']:,.0f}) + 이익잉여금(결손금) ({-won['이익잉여금']:,.0f}) 이 "
             f"원 단위로 폐합(잔차 {resid:.0f}원)하고, 200,000백만원이면 {resid_old / 1e6:,.1f}백만원이 남는다. 같은 분기의 다른 열·다른 분기의 자기자본 표·8-1 전기 열은 "
             "마스터와 전부 일치(KR1098 158칸 비교 중 불일치는 이 1칸뿐, scripts/bspl_followup_equity_scan.py). "
             f"[이전 근거(자본금 판독이 틀렸음)] {old_basis}")
    spec = {"cells": [{"key": KEY, "item": 30, "quarter": "2026.2Q", "action": "replace", "old": old, "new": new_mn,
                       "line": "자본금", "pdf": doc["pdf"], "page": t8["page"], "pdf_sha256": doc["sha256"], "basis": basis,
                       "part_file": "KR1098_agent_vision.json", "method": "followup_fix:disclosure_8-1_rendered+equity_table"}],
            "evidence": {"won_8-1_current": won, "won_8-1_prior_year_end": prior, "equity_table_자본금_억원_cols": eq_cols,
                         "closure_residual_won_at_300000": resid, "closure_residual_mn_at_200000": resid_old / 1e6}}
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("old", old, "-> new", new_mn, "residual at 300,000:", resid, "won; at 200,000:", resid_old / 1e6, "백만원")
    print("equity table 자본금 columns (억원):", eq_cols, "8-1 prior year-end 자본금(원):", prior["자본금"])


if __name__ == "__main__":
    main()
