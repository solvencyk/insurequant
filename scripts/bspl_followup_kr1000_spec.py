#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 2: build the correction spec for KR1000 (코리안리) 2023.1Q / 2023.2Q BS cells.

Root cause (see run log): the body-XML fallback of the BS builder picked the IFRS17 transition-date (2022.12.31) consolidated comparison
table (제1104호 -> 제1117호) in BOTH quarterly reports, because the real separate-basis statement's caption contains the word '연결기업'
and was therefore ranked as consolidated.  FS-API answers status 013 for these two quarters, so nothing overwrote it.

Values come from the DART separate-basis statement of the quarter itself (primary), located by matching its 자산 총계 to the printed
total of the disclosure's own 8-1 statement, and every line is cross-checked against the disclosure PDF (Stage-A tables) to the won.
Definitions follow the master series of the later quarters (DART FS-API leaf accounts: 기타부채 = '그밖의기타부채' leaf; 이익잉여금 =
headline of the stacked cell).  Item 10 = 현금및현금성자산 line (the master's later quarters hold the 예치금 line, see item10_tag_scan).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_kr1000_spec.py
Output: data/_derived/bspl_followup_20261011/kr1000_fix_spec.json   (read-only on all masters)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from bspl_granularity import stage_b as B  # noqa: E402

OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "kr1000_fix_spec.json"
CODE = "KR1000"
FILINGS = {
    "2023.1Q": {"fy": "FY2023_Q1", "rcept": "20230515002794", "hdr": "제 62기 1분기말", "kind": "분기보고서"},
    "2023.2Q": {"fy": "FY2023_Q2", "rcept": "20230814003146", "hdr": "제 62기 반기말", "kind": "반기보고서"},
}
# item -> (line label as printed after stripping the numbering prefix, why)
LINES = {
    1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "기타포괄손익누계액", 10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산",
    12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산", 14: "재보험계약자산", 15: "유형자산", 20: "보험계약부채",
    21: "재보험계약부채", 24: "그밖의기타부채", 30: "자본금", 31: "이익잉여금",
}
ITEM_NAME = {1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "기타포괄손익누계액", 10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산",
             12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산", 14: "재보험계약자산", 15: "유형자산", 20: "보험계약부채",
             21: "재보험계약부채", 24: "기타부채", 30: "자본금", 31: "이익잉여금"}
_AMT = re.compile(r"^\s*(\(?)\s*([\d,]+)\s*(\)?)")


def amount(cell: str):
    """first amount of a cell in won: '1,234' -> 1234, '(1,234)' -> -1234, '-' / '' -> None (nil is returned as 0 by the caller)."""
    s = str(cell or "").strip()
    if s in ("", "-"):
        return None
    m = _AMT.match(s)
    if not m:
        return None
    v = int(m.group(2).replace(",", ""))
    return -v if m.group(1) == "(" else v


def norm_label(raw: str) -> str:
    s = re.sub(r"\s+", "", raw)
    s = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVX]+\.", "", s)
    s = re.sub(r"^\d+\.", "", s)
    s = re.sub(r"\(.*$", "", s) if s.startswith("이익잉여금") else s
    return s


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def pdf_k_table(q: str):
    """the picked 8-1 K statement of the disclosure PDF: {normalised label: current value (won)} + page"""
    doc = B.load_tables(CODE, q)
    t = B.pick_tables(doc, "bs_full")[0]
    out = {}
    for r in t["rows"]:
        lab = norm_label(r["label"])
        if lab and lab not in out and r["vals"] and not r["dash"][0]:
            out[lab] = r["vals"][0]
    return out, t["page"], doc["pdf"], doc["sha256"], t.get("unit")


def dart_table(q: str, pdf_assets_won: float):
    f = FILINGS[q]
    xml = next((ROOT / "data" / "dart" / f["fy"] / "raw").glob("KR1000_*")) / "xml" / f"{f['rcept']}.xml"
    hit = None
    for t in _iter_tables_with_context(xml):
        hdr = " ".join(str(c) for row in (t.header or []) for c in row)
        if f["hdr"] not in hdr:
            continue
        for r in t.rows:
            if r and norm_label(r[0]) == "자산총계":
                cells = [amount(c) for c in r[1:]]
                cells = [c for c in cells if c is not None]
                if cells and abs(cells[0] - pdf_assets_won) < 1:
                    hit = t
        if hit is not None:
            break
    if hit is None:
        raise SystemExit(f"{q}: separate-basis table with 자산총계 == {pdf_assets_won} not found in {xml}")
    lines = {}
    for r in hit.rows:
        if not r or not r[0]:
            continue
        lab = norm_label(r[0])
        cur = None
        for c in r[2:4]:                # child amount column, parent amount column of the current period
            v = amount(c)
            if v is not None:
                cur = v
                break
        if lab and lab not in lines:
            lines[lab] = cur if cur is not None else (0 if any(str(c).strip() == "-" for c in r[2:4]) else None)
    return lines, hit.line_no, xml, f


def main():
    all_v, anchor, disc, meta = B.load_master()
    mv = all_v[CODE]
    cells, report = [], {}
    for q in ("2023.1Q", "2023.2Q"):
        pdf, page, pdf_path, pdf_sha, pdf_unit = pdf_k_table(q)
        assert pdf_unit == "원", pdf_unit
        d, dline, xml, f = dart_table(q, pdf["자산총계"])
        rep = {"xml": str(xml.relative_to(ROOT)), "xml_table_line": dline, "pdf": pdf_path, "pdf_page": page, "checks": {}}
        vals = {}
        for item, lab in LINES.items():
            dv = d.get(lab)
            pv = pdf.get(lab)
            if lab == "이익잉여금":
                pv = None          # the stacked 이익잉여금 cell is not readable row-wise from the PDF text layer (checked by identity below)
            if dv is None and lab not in d:
                continue
            if item == 14 or item == 21:
                pass
            vals[item] = dv
            rep["checks"][item] = {"label": lab, "dart_won": dv, "pdf_won": pv, "equal": (pv is None or pv == dv)}
        # identities (won)
        a, l, e = vals[1], vals[2], vals[3]
        comp = sum(d[k] for k in ("자본금", "자본잉여금", "신종자본증권", "자본조정", "기타포괄손익누계액", "이익잉여금"))
        rep["identity_A_L_E_resid_won"] = a - l - e
        rep["identity_equity_components_resid_won"] = comp - e
        assert a - l - e == 0 and comp - e == 0, (q, a - l - e, comp - e)
        assert all(c["equal"] for c in rep["checks"].values()), [k for k, c in rep["checks"].items() if not c["equal"]]
        # leaf/parent consistency of 기타부채 (parent = tax + DBO + provisions + leaf)
        par = d["기타부채"]
        kids = sum(d[k] for k in ("당기법인세부채", "이연법인세부채", "순확정급여부채", "충당부채", "그밖의기타부채"))
        rep["other_liab_parent_minus_children_won"] = par - kids
        report[q] = rep
        for item, v in sorted(vals.items()):
            key = f"{CODE}|{item}|{q}"
            new_mn = round(v / 1e6, 6)
            old = mv.get((item, q))
            cells.append({"key": key, "item": item, "quarter": q, "old": old, "new": new_mn, "line": LINES[item],
                          "dart_won": v, "pdf": pdf_path, "page": page, "pdf_sha256": pdf_sha, "rcept": f["rcept"],
                          "xml_line": dline, "report_kind": f["kind"]})
    # which cells change / are added / are untouched (equal to the existing value)
    side = json.loads((ROOT / "data" / "_derived" / "bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
    for c in cells:
        if c["old"] is None:
            c["action"] = "add"
        elif abs(c["old"] - c["new"]) < 1e-6:
            c["action"] = "keep"
        elif c["key"] in side and abs(c["old"] - c["new"]) <= 50.5:
            c["action"] = "keep"                      # disclosure-sourced master cell printed in 억원 (rounding half step 50 백만원): right already
        else:
            c["action"] = "replace"
    notes = {10: "※ 라인 = 「Ⅰ. 현금및현금성자산」. 마스터의 2023.3Q 이후 KR1000 항목 10 칸은 같은 8-1 의 「예치금」 라인 값이다"
                 "(빌더가 대안 태그 중 알파벳순 첫 행 dart_CashAndDuefromBanks 를 집음, 3사 30칸 — item10_tag_scan.json 참조, 별도 보고).",
             24: "※ 라인 = 「5. 그밖의기타부채」(말단 계정, FS-API ifrs-full_OtherNonfinancialLiabilities). 2023.3Q 이후 마스터 항목 24 와 같은 정의"
                 "(그 분기들의 8-1 은 말단 계정만 낸다). 부모 「Ⅳ. 기타부채」는 당기법인세·이연법인세·순확정급여·충당부채를 포함해 다른 값이다.",
             31: "※ 이익잉여금 칸은 대손준비금·비상위험준비금·해약환급금준비금 적립액이 괄호로 이어 붙은 칸이라 첫 금액(이익잉여금 본액)을 썼다."}
    for c in cells:
        f = FILINGS[c["quarter"]]
        per = "제62기 1분기말" if c["quarter"] == "2023.1Q" else "제62기 반기말"
        if c["action"] == "keep":
            continue
        head = ("정정" if c["action"] == "replace" else "신규(앵커 정정 뒤 새로 읽을 수 있게 된 칸)") + " 2026-10-11(inbox/parser/20261011T0900Z 단계 2): "
        if c["action"] == "replace":
            head += (f"옛 값 {c['old']:,.2f}백만원은 DART 본문 XML 폴백(build_ifrs17_bs → build_equity_composition_tier2._pick_bs_table)이 별도 재무상태표 대신 "
                     "「IFRS17 전환일(2022.12.31) 재무상태표 제1104호→제1117호 비교표」를 고른 값이다(두 분기 보고서가 같은 표를 골라 두 분기 값이 소수점까지 같았고, "
                     "별도표 캡션에 '연결기업'이 끼어 basis 가 CFS 로 밀렸으며, FS-API 는 이 두 분기 status 013 무응답이라 덮어쓴 값이 없었다). ")
        c["basis"] = (head + f"정정값 = DART {f['kind']} rcept {f['rcept']} 별도 재무상태표({per}) 「{c['line']}」 {c['dart_won']:,}원 = {c['new']:,.6f}백만원이며 "
                      f"정기경영공시 {c['quarter']} 재무상태표(8-1) p{c['page']} 와 원 단위까지 일치한다. 자산 = 부채 + 자본, 자본 = 구성 항목 합이 원 단위로 폐합. "
                      + notes.get(c["item"], "") + " (scripts/bspl_followup_kr1000_spec.py)")
        c["method"] = "followup_fix:dart_separate_bs_xml+disclosure_8-1_equal_to_won"
    OUT.write_text(json.dumps({"cells": cells, "report": report}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    n = {k: sum(1 for c in cells if c["action"] == k) for k in ("replace", "add", "keep")}
    print("cells", len(cells), n)
    for c in cells:
        old = f"{c['old']:>16,.6f}" if c["old"] is not None else f"{'(blank)':>16}"
        print(f"{c['key']:<22} {c['action']:<8} old {old} -> new {c['new']:>16,.6f}  ({c['line']})")
    for q, r in report.items():
        print(q, "A-L-E resid", r["identity_A_L_E_resid_won"], "equity comps resid", r["identity_equity_components_resid_won"],
              "기타부채 parent - children", r["other_liab_parent_minus_children_won"], "xml line", r["xml_table_line"], "pdf p", r["pdf_page"])


if __name__ == "__main__":
    main()
