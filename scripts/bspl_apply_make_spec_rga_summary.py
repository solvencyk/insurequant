#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B3 follow-up): RGA (KR1105) cells whose 요약 재무상태표(총괄) row label is garbled in the text layer, so the granularity matcher missed them.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_make_spec_rga_summary.py [out.json]

* 2023.2Q 현금및예치금 (item 10): the 2024.2Q filing's summary BS (p7, 전년동기 열) row prints 「현금및예치금」 487 | 396 억원 with the label missing in the text layer; 396억 = the own 2023.2Q
  filing's p6 value, so no restatement conflict (R1: latest filing's prior-year column) -> 39,600 백만원 (+-50).
* 2025.1Q / 2026.1Q 당기손익-공정가치측정유가증권 (item 11 = 0, printed dash) and 기타포괄손익-공정가치측정유가증권 (item 12): the rows print as 「측정유가증권」 (label split across lines in the text layer).
  Row order in the fixed supervisory form = 현금및예치금, 당기손익-공정가치측정유가증권, 기타포괄손익-공정가치측정유가증권, 상각후원가측정유가증권, ...; the nonzero 측정유가증권 row = FVOCI.
  Cross-checks: FVOCI 2,396억 / 2,562억 = the image 8-1 lines (239,575,138 / 256,160,047천원) rounded to 억원; the row amounts + 현금및예치금 + 비운용자산 add up to 자산총계 (3,900 / 3,595).
All numbers are asserted against the PDF rows before a cell is emitted.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from bspl_granularity.pdfrows import rows_from_page  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "_derived" / "bspl_apply_20261011" / "spec_B7_rga_summary.json"


def pdf_of(fy):
    return sorted((ROOT / "data/disclosure" / fy / "raw").glob("KR1105_*.pdf"))[0]


def rows(fy, page):
    doc = fitz.open(str(pdf_of(fy)))
    r, _free = rows_from_page(doc[page - 1], pageno=page)
    return [(x.label, list(x.vals)) for x in r]


def cell(key, item, q, val, line, fy, page, basis):
    pdf = pdf_of(fy)
    return {"key": key, "item": item, "quarter": q, "action": "add", "old": None, "new": val, "line": line, "pdf": pdf.relative_to(ROOT).as_posix(), "page": page,
            "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(), "basis": " ".join(basis.split()), "method": "round3_fill:sum_bs_garbled_label", "scale": "억원 -> 백만원"}


def main():
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    cells = []
    # ---- 2023.2Q item 10 from the 2024.2Q filing (prior-year column) ----
    r = rows("FY2024_Q2", 7)
    first = [v for lab, v in r if v and len(v) == 3 and v[0] == 487.0]
    assert first and first[0][2] == 396.0, r[:3]
    tot = [v for lab, v in r if lab == "자산총계"][0]
    foci = [v for lab, v in r if lab.startswith("기타포괄손익-공정가치측정유가증권")][0]
    nonop = [v for lab, v in r if lab == "비운용자산"][0]
    assert tot[2] == 2356.0 and foci[2] == 1876.0 and nonop[2] == 85.0 and 396.0 + 1876.0 + 85.0 in (2357.0, 2356.0), (tot, foci, nonop)
    own = rows("FY2023_Q2", 6)
    own_cash = [v for lab, v in own if lab.startswith("현금및예치금")][0]
    assert own_cash[0] == 396.0
    cells.append(cell("KR1105|10|2023.2Q", 10, "2023.2Q", 39600.0, "현금및예치금(= 마스터 항목 10 계열의 RGA 요약표 라벨)", "FY2024_Q2", 7,
                      "신규 2026-10-11(round 3, B3 후속): 정기경영공시 2024.2Q 요약 재무상태표(총괄) p7 의 전년동기(23.2Q) 열 「현금및예치금」 396억원(텍스트층에서 이 행의 라벨이 빠져 있어 granularity 매처가 놓침) = "
                      "39,600백만원, 정밀도 ±50백만원(인쇄 단위 억원). R1(owner 2026-10-09 재보사 최신 공시 전년동기 칸 채택): 같은 열의 자산총계 2,356 · 기타포괄손익-공정가치측정유가증권 1,876 · 비운용자산 85 와 "
                      "줄 합 2,357 = 2,356(±1)로 닫히고(이 칸의 이웃 항목 12 · 1 · 2 · 3 은 이미 같은 열 값으로 마스터에 있음), 이 분기 자체 공시(2023.2Q p6)의 현금및예치금도 396억원이라 재작성 충돌 없음. (inbox/parser/20261011T1130Z B3)"))
    # ---- 2025.1Q / 2026.1Q items 11, 12 ----
    for q, fy, page, nx_fy, nx_page, foci_mn, cash, nonop_v, total_v, foci_8_1 in (("2025.1Q", "FY2025_Q1", 7, "FY2026_Q1", 7, 239600.0, 264.0, 1240.0, 3900.0, 239575138),
                                                                         ("2026.1Q", "FY2026_Q1", 7, None, None, 256200.0, 227.0, 807.0, 3595.0, 256160047)):
        r = rows(fy, page)
        cash_row = [v for lab, v in r if lab.startswith("현금및예치금")][0]
        assert cash_row[0] == cash
        tm = [(i, lab, v) for i, (lab, v) in enumerate(r) if "측정유가증권" in lab]
        assert len(tm) in (2, 3), tm                                         # FVPL row, FVOCI row (+ the 상각후원가 securities row, zero)
        fvpl_row, fvoci_row = tm[0][2], tm[1][2]
        assert all(x == 0.0 for x in fvpl_row), fvpl_row
        assert fvoci_row[0] == foci_mn / 100.0, fvoci_row
        total = [v for lab, v in r if lab == "자산총계"][0][0]
        nonop = [v for lab, v in r if lab == "비운용자산"][0][0]
        assert total == total_v and nonop == nonop_v and abs(cash + 0 + foci_mn / 100.0 + nonop - total) <= 2, (total, nonop)
        assert abs(foci_8_1 / 100000.0 - foci_mn / 100.0) <= 0.5                                   # 8-1 image line (천원) rounds to the summary 억원
        nx = ""
        if nx_fy:
            rn = rows(nx_fy, nx_page)
            tn = [v for lab, v in rn if "측정유가증권" in lab]
            assert tn[1][1] == foci_mn / 100.0 if len(tn[1]) == 2 else tn[1][2] == foci_mn / 100.0, tn
            nx = f" 다음 해 2026.1Q 요약표 p7 의 전년동기 열도 같은 값({foci_mn / 100.0:,.0f}억원)이라 재작성 충돌 없음."
        common = (f"정기경영공시 {q} 요약 재무상태표(총괄) p{page}(단위 억원, 텍스트층에서 「당기손익-공정가치측정유가증권」·「기타포괄손익-공정가치측정유가증권」 행의 라벨이 「측정유가증권」으로 잘려 granularity 매처가 놓침; "
                  f"양식 행 순서 = 현금및예치금, 당기손익-공정가치, 기타포괄손익-공정가치, 상각후원가 …)")
        cells.append(cell(f"KR1105|12|{q}", 12, q, foci_mn, "기타포괄손익-공정가치측정유가증권", fy, page,
                          f"신규 2026-10-11(round 3, B3 후속): {common}의 두 번째 「측정유가증권」 행 {foci_mn / 100.0:,.0f}억원 = {foci_mn:,.0f}백만원, 정밀도 ±50백만원. 보정: 현금및예치금 {cash:,.0f} + 이 행 + 비운용자산 {nonop_v:,.0f} = 자산총계 {total_v:,.0f}(±2) "
                          f"닫힘, 같은 {q} 이미지 8-1 의 기타포괄손익-공정가치측정금융자산 줄 {foci_8_1:,}천원이 억원 반올림으로 같은 값.{nx} (inbox/parser/20261011T1130Z B3)"))
        cells.append(cell(f"KR1105|11|{q}", 11, q, 0.0, "당기손익-공정가치측정금융자산", fy, page,
                          f"신규 2026-10-11(round 3, B3 후속): {common}의 첫 번째 「측정유가증권」 행 = 0(대시), 정밀도 ±50백만원. 0 증명: 현금및예치금 {cash:,.0f} + 기타포괄손익-공정가치측정유가증권 {foci_mn / 100.0:,.0f} + 비운용자산 "
                          f"{nonop_v:,.0f} = 자산총계 {total_v:,.0f}(±2)로 모든 줄이 닫힌다(같은 이웃 칸 2024.1Q·3Q·2025.2Q·3Q·4Q·2026.2Q 의 0.0 과 같은 관례). (inbox/parser/20261011T1130Z B3)"))
    cells = [c for c in cells if ("KR1105", c["item"], c["quarter"]) not in mv]
    OUT.write_text(json.dumps({"_what": "RGA summary-BS cells missed because of garbled row labels", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for c in cells:
        print(f"{c['key']:<18} (blank) -> {c['new']:>12,.1f}")
    print(f"{len(cells)} cells -> {OUT}")


if __name__ == "__main__":
    main()
