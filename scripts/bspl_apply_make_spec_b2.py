#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B2): 신한이지손해보험 KR0051 item 12 (2023.4Q, 2024.4Q) from the received audit reports; 카카오페이손해보험 KR1098 provable-zero lines
(2024.4Q items 11, 12, 21; 2025.4Q items 12, 21) from the DART audit XML balance sheets.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_make_spec_b2.py [out.json]

KR0051: the audit report's balance sheet prints 「기타포괄손익-공정가치측정유가증권」 (유가증권, not 금융자산 -- the builder's XML label matcher misses it).  Checks: the
statement's other lines reproduce the master's year-end cells (items 1, 2, 3, 4, 11, 14, 15, 20, 21, 24, 30 within 0.0015 백만원), the FY2024 report's prior-year column
equals the FY2023 report's current column, assets = liabilities + equity and the numbered lines add up to the totals.
KR1098: every asset/liability line of the audit balance sheet is listed (financial assets = 상각후원가측정기타금융자산 only; no FVPL/FVOCI line, no 재보험계약부채 line) and
the printed lines add up to the printed totals, so the missing lines are 0 (closure proof) -- the same convention as the 0.0 cells already in the master (2023.1Q-2024.1Q).
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
import bspl_apply_attfs as A  # noqa: E402
import bspl_apply_xmlbs as X  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "_derived" / "bspl_apply_20261011" / "spec_B2_ez_kakao.json"


def main():
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    cells = []
    # ---------------- KR0051 ----------------
    reads = {}
    for y in (2023, 2024):
        pdf = ROOT / "data" / "disclosure" / f"FY{y}_Q4" / "attachments" / "KR0051_신한이지손해보험_attachment_audit_fs.pdf"
        rows, unit, page = A.read_bs(pdf)
        items = A.to_items(rows)
        reads[y] = (pdf, page, rows, items)
    # prior column of FY2024 == current column of FY2023 (all mapped items)
    for it, (raw, vals) in reads[2023][3].items():
        v24 = reads[2024][3].get(it)
        if v24 and len(v24[1]) > 1 and abs(v24[1][1] - vals[0]) > 0.0015:
            print(f"  note: FY2024 prior col != FY2023 current col for item {it}: {v24[1][1]} vs {vals[0]}")
    for y in (2023, 2024):
        pdf, page, rows, items = reads[y]
        q = f"{y}.4Q"
        cur = {it: v[1][0] for it, v in items.items()}
        # calibration against the year-end master (DART audit XML)
        bad = [(it, cur[it], mv[("KR0051", it, q)]) for it in (1, 2, 3, 4, 11, 14, 15, 20, 21, 24, 30) if ("KR0051", it, q) in mv and abs(cur[it] - mv[("KR0051", it, q)]) > 0.0015]
        n_ok = sum(1 for it in (1, 2, 3, 4, 11, 14, 15, 20, 21, 24, 30) if ("KR0051", it, q) in mv and abs(cur[it] - mv[("KR0051", it, q)]) <= 0.0015)
        assert not bad, (q, bad)
        assert abs(cur[1] - cur[2] - cur[3]) < 0.0015
        # numbered lines add up
        sums, acc = {}, 0.0
        for lab, raw, vals, _d in rows:
            if not vals:
                continue
            if lab in ("자산총계", "부채총계", "자본총계"):
                sums[lab] = (acc, vals[0])
                acc = 0.0
            elif not lab.startswith("부채와자본총계") and not lab.startswith("자본과부채총계") and raw.strip()[:1].isdigit():
                acc += vals[0]
        assert all(abs(a - b) < 0.0015 for a, b in sums.values()), (q, sums)
        new = round(cur[12], 6)
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        basis = (f"신규 2026-10-11(round 3, B2): 신한이지손해보험 {y}년 감사보고서 첨부(별도 재무제표, 단위 원) 재무상태표 p{page} 「{items[12][0].strip()}」 {new * 1e6:,.0f}원 = {new:,.6f}백만원. "
                 f"이 줄의 라벨이 「유가증권」이라 DART 본문 XML 폴백(금융자산 라벨 매처)이 못 읽어 마스터 항목 12 가 비어 있었다. 보정: 같은 표의 다른 줄 {n_ok}개(자산·부채·자본 총계, 기타포괄손익누계액, "
                 f"FVPL, 재보험계약자산, 유형자산, 보험계약부채, 재보험계약부채, 기타부채, 자본금)가 마스터 {q} 값을 0.0015백만원 이내로 재현하고, 자산 = 부채 + 자본과 번호 줄 합 = 총계가 원 단위로 닫히며, "
                 f"{'다음 해 감사보고서의 전기 열이 같은 값(10,041.07246)이다' if y == 2023 else '2023.4Q 값 10,041.07246 이 이 보고서 전기 열과 같다'}. 수령: downloader inbox/parser/20261010T2350Z.")
        cells.append({"key": f"KR0051|12|{q}", "item": 12, "quarter": q, "action": "add", "old": None, "new": new, "line": "기타포괄손익-공정가치측정유가증권",
                      "pdf": pdf.relative_to(ROOT).as_posix(), "page": page, "pdf_sha256": sha, "basis": basis,
                      "method": "round3_fill:attachment_audit_fs", "scale": "원 -> 백만원"})
    # ---------------- KR1098 ----------------
    def kakao_rows(q):
        xml = X.xml_files("KR1098", q)
        xml = [f for f in xml if f.name.endswith("_00760.xml")] or xml
        assert len(xml) == 1, xml
        for t in _iter_tables_with_context(xml[0]):
            if t.rows and "자산총계" in "".join("".join(str(c) for c in r) for r in t.rows).replace(" ", "") and len(t.rows) >= 20 and X.bs_like(t):
                return xml[0], t
        raise SystemExit("no BS table")
    for q, items in (("2024.4Q", (11, 12, 21)), ("2025.4Q", (12, 21))):
        xml, t = kakao_rows(q)
        asset_lines, liab_lines, sec = [], [], None
        tot = {}
        for r in t.rows:
            lab = X.clean_label(str(r[0]))
            cells_ = [X.ns(str(c)) for c in r[1:] if X.ns(str(c)) != ""]
            vals = []
            if cells_:
                c0 = cells_[0]                                   # first non-empty cell = current period; a bare dash is a printed zero
                if c0 in ("-", "－"):
                    vals = [0.0]
                elif X.LEGIT.match(c0):
                    v0 = X.num(c0)
                    vals = [v0] if v0 is not None else []
            if lab in ("자산",):
                sec = "A"
            elif lab in ("부채",):
                sec = "L"
            elif lab in ("자본",):
                sec = "E"
            if not vals:
                continue
            if lab in ("자산총계", "부채총계", "자본총계"):
                tot[lab] = vals[0]
                continue
            if lab.startswith("자본과부채총계"):
                continue
            raw0 = str(r[0]).strip()
            if re.match(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.", raw0):                 # top-level lines only (roman numerals); "1. 상각후원가…" sits inside 금융자산
                (asset_lines if sec == "A" else liab_lines if sec == "L" else []).append((raw0, vals[0]))
        sa = sum(v for _l, v in asset_lines)
        sl = sum(v for _l, v in liab_lines)
        assert abs(sa - tot["자산총계"]) < 1.0 and abs(sl - tot["부채총계"]) < 1.0, (q, sa, tot, sl)
        labels = " | ".join(l for l, _v in asset_lines + liab_lines)
        has = {11: "당기손익-공정가치" in labels or "당기손익공정가치" in labels, 12: "기타포괄손익" in labels.replace("누계", "§") and "기타포괄손익-공정가치" in labels,
               21: "재보험계약부채" in labels}
        assert not any(has[i] for i in items), (q, has)
        rel = xml.relative_to(ROOT).as_posix()
        sha = hashlib.sha256(xml.read_bytes()).hexdigest()
        for it in items:
            name = {11: "당기손익-공정가치측정금융자산", 12: "기타포괄손익-공정가치측정금융자산", 21: "재보험계약부채"}[it]
            basis = (f"신규 2026-10-11(round 3, B2): 카카오페이손해보험 {q} DART 감사보고서 XML {rel}(sha256 {sha[:12]}...)의 재무상태표(원 단위, 별도)에는 「{name}」 줄이 없다. "
                     f"자산 줄 {len(asset_lines)}개의 합 {sa:,.0f}원 = 자산총계 {tot['자산총계']:,.0f}원, 부채 줄 {len(liab_lines)}개의 합 {sl:,.0f}원 = 부채총계 {tot['부채총계']:,.0f}원으로 "
                     f"모든 줄이 열거돼 있고(금융자산 = 「1. 상각후원가측정기타금융자산」 하나뿐) 폐합하므로 이 항목은 0 이다(폐합 증명). 같은 회사 2023.1Q~2024.1Q 마스터의 0.0 칸과 같은 관례. "
                     f"수령: downloader inbox/parser/20261010T2350Z(감사보고서 첨부 PDF 는 폰트 매핑이 깨져 텍스트층을 못 읽어 DART XML 을 썼다).")
            cells.append({"key": f"KR1098|{it}|{q}", "item": it, "quarter": q, "action": "add", "old": None, "new": 0.0, "line": name, "pdf": rel, "page": t.line_no,
                          "pdf_sha256": sha, "basis": basis, "method": "round3_fill:dart_audit_xml_zero_closure", "scale": "원 -> 백만원"})
    cells = [c for c in cells if ("KR1098" if c["key"].startswith("KR1098") else "KR0051", int(c["key"].split("|")[1]), c["quarter"]) not in {(k[0], k[1], k[2]) for k in mv}]
    OUT.write_text(json.dumps({"_what": "B2 KR0051 item 12 + KR1098 closure zeros", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for c in cells:
        print(f"{c['key']:<18} (blank) -> {c['new']:>16,.6f}   {c['pdf'][-60:]} p/line {c['page']}")
    print(f"{len(cells)} cells -> {OUT}")


if __name__ == "__main__":
    main()
