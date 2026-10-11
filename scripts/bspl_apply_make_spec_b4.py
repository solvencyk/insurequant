#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B4): year-end cells from the DART audit XML that is already on disk.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_make_spec_b4.py [out.json]

* KR0074 라이나생명 2023.4Q item 14 (재보험계약자산): the FY2023 audit balance sheet has no such line; the FY2024 audit report prints the 31 Dec 2023 comparative of
  「Ⅵ. 재보험계약자산」 as a dash (nil) -> 0.0.  (Also checks the asset lines of the FY2023 sheet add up to the total.)
* KR0100 처브라이프 2025.4Q item 20 (보험계약부채): the K-IFRS line family of the year-end anchors (2023.4Q, 2024.4Q, 2026.1Q/2Q) = 「보험계약부채_유배당」 + 「보험계약부채_유배당 외」
  (the prior-year column of this report reproduces the master's 2024.4Q cell 1,300,423.982208 exactly).  The 10 mid-year cells with the 일반계정/특별계정 definition mix are NOT
  touched (owner decision pending, TODO_parser_ifrs17).
KR0075 2023.4Q / KR0097 2023.4Q / KR0074 2025.4Q: no blank cell is provable from the audit sheet (the remaining blanks are items 22/23 without a line) -> nothing to fill.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_apply_xmlbs as X  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "_derived" / "bspl_apply_20261011" / "spec_B4_yearend.json"


def table_at(xml: Path, line: int):
    for t in _iter_tables_with_context(xml):
        if t.line_no == line:
            return t
    raise SystemExit(f"table {line} not found in {xml}")


def row_vals(t, prefix: str):
    """first row whose space-less label starts with prefix -> list of the period cells (as printed, spaces removed, empty cells dropped)."""
    for r in t.rows:
        if X.ns(str(r[0])).startswith(prefix):
            return [X.ns(str(c)) for c in r[1:] if X.ns(str(c)) != ""]
    raise SystemExit(f"row {prefix} not found")


def won(s):
    if s in ("-", "－"):
        return 0.0
    v = X.num(s)
    assert v is not None, s
    return v


def main():
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    cells = []
    # ---- KR0074 2023.4Q item 14 ----
    x23 = X.xml_files("KR0074", "2023.4Q")
    x23 = [f for f in x23 if f.name.endswith("_00760.xml")][0]
    t23 = table_at(x23, 521)
    labs = [X.clean_label(str(r[0])) for r in t23.rows]
    assert not any("재보험계약자산" in l or "재보험자산" in l for l in labs), labs
    a = 0.0
    tot_a = None
    for r in t23.rows:
        lab = X.clean_label(str(r[0]))
        cs = [X.ns(str(c)) for c in r[1:] if X.ns(str(c)) != ""]
        if lab == "자산총계":
            tot_a = won(cs[0])
            break
        if lab and lab not in ("자산",) and cs:
            # note column first ('4,5,6..'), the current amount is the first cell that looks like a number with >= 4 digits
            amt = next((c for c in cs if X.LEGIT.match(c) and abs(X.num(c) or 0) >= 1e6), None)
            if amt:
                a += won(amt)
    assert tot_a is not None and abs(a - tot_a) < 1.0, (a, tot_a)
    x24 = [f for f in X.xml_files("KR0074", "2024.4Q") if f.name.endswith("_00760.xml")][0]
    t24 = table_at(x24, 522)
    vals = row_vals(t24, "Ⅵ.재보험계약자산")
    # cells: [note, 2024 amount, 2023 amount, 2022-01-01 amount]
    assert vals[0] == "17" and vals[2] == "-" , vals
    sha23, sha24 = hashlib.sha256(x23.read_bytes()).hexdigest(), hashlib.sha256(x24.read_bytes()).hexdigest()
    basis = (f"신규 2026-10-11(round 3, B4): 라이나생명 2023.4Q 재보험계약자산 = 0. 근거 2건 — (1) FY2023 감사 재무상태표({x23.relative_to(ROOT).as_posix()}, sha256 {sha23[:12]}..., 원 단위, 표 line 521)의 "
             f"자산 줄 9개(현금, FVPL, FVOCI, 상각후원가측정대출채권및수취채권, 보험계약자산, 투자부동산, 유형자산, 무형자산, 기타자산)의 합 {a:,.0f}원 = 자산총계 {tot_a:,.0f}원으로 닫히고 「재보험계약자산」 줄이 없다"
             f"(재보험은 부채 쪽 「Ⅱ. 재보험계약부채」 44,946,702,495원 뿐). (2) FY2024 감사 재무상태표({x24.relative_to(ROOT).as_posix()}, sha256 {sha24[:12]}..., 표 line 522)가 「Ⅵ. 재보험계약자산」의 "
             f"제21(전) 기말 열(2023-12-31)을 대시(-, 무)로 인쇄한다(제22기 기말은 33,906,085,177원 = 마스터 2024.4Q). 참고: FY2024 보고서는 2023-12-31 비교 재무제표를 소급 재작성했다"
             f"(보험계약자산 214,858 → 1,971,526백만원 등, 주석 34); 마스터 2023.4Q 의 기존 칸은 원 보고서 값이고 이 라운드에서 바꾸지 않았다.")
    cells.append({"key": "KR0074|14|2023.4Q", "item": 14, "quarter": "2023.4Q", "action": "add", "old": None, "new": 0.0, "line": "재보험계약자산",
                  "pdf": x23.relative_to(ROOT).as_posix(), "page": 521, "pdf_sha256": sha23, "basis": basis, "method": "round3_fill:dart_audit_xml_nil_line", "scale": "원 -> 백만원"})
    # ---- KR0100 2025.4Q item 20 ----
    x25 = [f for f in X.xml_files("KR0100", "2025.4Q") if f.name.endswith("_00760.xml")][0]
    t25 = table_at(x25, 496)
    a1 = row_vals(t25, "1.보험계약부채_유배당")
    a2 = row_vals(t25, "2.보험계약부채_유배당외")
    cur = won(a1[1]) + won(a2[1])            # cells: [note, 당기, 전기]
    prv = won(a1[2]) + won(a2[2])
    m24 = mv[("KR0100", 20, "2024.4Q")]
    assert abs(prv / 1e6 - m24) < 0.0015, (prv, m24)
    new = round(cur / 1e6, 6)
    sha25 = hashlib.sha256(x25.read_bytes()).hexdigest()
    basis = (f"신규 2026-10-11(round 3, B4): 처브라이프 2025.4Q 보험계약부채 = K-IFRS 재무상태표 라인 「1. 보험계약부채_유배당」 {won(a1[1]):,.0f}원 + 「2. 보험계약부채_유배당 외」 {won(a2[1]):,.0f}원 = "
             f"{cur:,.0f}원 = {new:,.6f}백만원({x25.relative_to(ROOT).as_posix()}, sha256 {sha25[:12]}..., 표 line 496). 마스터 연말 앵커(2023.4Q 1,222,488.069199 · 2024.4Q 1,300,423.982208 · 2026.1Q/2Q)와 "
             f"같은 K-IFRS 라인 정의이고, 이 보고서의 전기 열 두 줄의 합 {prv:,.0f}원이 마스터 2024.4Q 값을 원 단위까지 재현한다. 일반계정만(D1) 값은 이 감사표에 없다 — 중간분기 10칸의 D1/D2 정의 혼재는 "
             f"owner 결정 대기라 손대지 않았다(TODO_parser_ifrs17).")
    cells.append({"key": "KR0100|20|2025.4Q", "item": 20, "quarter": "2025.4Q", "action": "add", "old": None, "new": new, "line": "보험계약부채(K-IFRS 라인)",
                  "pdf": x25.relative_to(ROOT).as_posix(), "page": 496, "pdf_sha256": sha25, "basis": basis, "method": "round3_fill:dart_audit_xml_kifrs_line", "scale": "원 -> 백만원"})
    cells = [c for c in cells if (c["key"].split("|")[0], int(c["key"].split("|")[1]), c["quarter"]) not in mv]
    OUT.write_text(json.dumps({"_what": "B4 year-end fills from DART audit XML", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for c in cells:
        print(f"{c['key']:<18} (blank) -> {c['new']:>18,.6f}")
    print(f"{len(cells)} cells -> {OUT}")


if __name__ == "__main__":
    main()
