#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4th round (parser/ifrs17, inbox/parser/20261011T1215Z): closure-proven zero cells from the new full-edition attachments / raw BS."""
import hashlib, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/_derived/bspl_apply_20261011/spec_C4_zero_proofs.json"

def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()

A104 = "data/disclosure/FY2025_Q4/attachments/KR0104_농협생명보험_attachment_full_edition_with_audit_report.pdf"
A005 = "data/disclosure/FY2024_Q4/attachments/KR0005_흥국화재_attachment_full_edition_with_audit_report.pdf"
R029 = "data/disclosure/FY2023_Q4/raw/KR0029_AIG손해보험.pdf"
cells = []
def add(code, item, q, pdf, page, line, basis):
    cells.append({"key": f"{code}|{item}|{q}", "item": item, "quarter": q, "action": "add", "old": None, "new": 0.0,
                  "line": line, "pdf": pdf, "page": page, "pdf_sha256": sha(pdf), "basis": basis,
                  "method": "round4_zero_proof:closure", "scale": "원/천원/백만원 -> 백만원 (0)"})
b104 = ("신규 2026-10-11(round 4): 농협생명 2025년 감사보고서 첨부(별도 재무제표, 단위 원) 재무상태표 p135 에 「{L}」 줄이 없다. 자산 12줄 합 = 자산총계 "
        "52,616,603,460,562원, 부채 9줄(보험계약부채·재보험계약부채·파생상품부채·차입부채·기타금융부채·이연법인세부채·충당부채·순확정급여부채·기타부채) 합 = 부채총계 "
        "47,528,318,236,586원이 원 단위로 정확히 닫히고, 마스터 항목 10/11/12/13/15/20/21/23/24/30/31 이 같은 표 줄과 일치. 줄 없음 + 합 폐합 = 0 증명(전례: 카카오페이·RGA 0.0).")
add("KR0104", 14, "2025.4Q", A104, 135, "재보험계약자산(줄 없음; 재보험계약부채 62,105,039,519원만 있음)", b104.format(L="재보험계약자산"))
add("KR0104", 22, "2025.4Q", A104, 135, "투자계약부채(줄 없음)", b104.format(L="투자계약부채"))
add("KR0005", 22, "2024.4Q", A005, 105, "투자계약부채(줄 없음)",
    "신규 2026-10-11(round 4): 흥국화재 2024년 감사보고서 첨부(별도, 단위 백만원) 재무상태표 p105 에 「투자계약부채」 줄이 없다. 부채 9줄(보험계약부채 11,414,733 · 재보험계약부채 263 · 사채 414,147 · "
    "FVPL금융부채 1,535 · 위험회피파생부채 164,981 · 리스부채 13,504 · 기타금융부채 97,195 · 기타부채 6,551 · 충당부채 9,121) 합 12,122,030 = 부채총계, 자산 15줄 합 12,894,689 = 자산총계로 닫히고 "
    "마스터 항목 1/2/3/4/10/11/12/14/15/20/21/24/30/31 이 같은 표와 일치. 줄 없음 + 합 폐합 = 0 증명.")
b029 = ("신규 2026-10-11(round 4): AIG손해보험 2023.4Q 경영공시 8-2-1 재무상태표(별도, 단위 천원) p63 에 「{L}」 줄이 없다. 부채총계 400,530,573 = 책임준비금 273,927,220 + 기타부채 126,603,353(하위 줄 11개), "
        "자산총계 1,013,529,537 = 운용자산 746,209,240 + 비운용자산 267,320,297 이 닫히고 마스터 항목 1/2/3/4/10/11/12/14/20/21/24/30/31 이 같은 표와 일치. 줄 없음 + 폐합 = 0 증명. "
        "(새 첨부 p76~86 은 지급여력 건전성감독기준 재무상태표 감사보고서 이미지라 K-IFRS 정의와 달라 쓰지 않았다.)")
add("KR0029", 22, "2023.4Q", R029, 63, "투자계약부채(줄 없음)", b029.format(L="투자계약부채"))
add("KR0029", 23, "2023.4Q", R029, 63, "차입부채(줄 없음)", b029.format(L="차입부채"))
OUT.write_text(json.dumps({"_what": "C4 closure-proven zero cells (round 4)", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(len(cells), "cells ->", OUT)
