#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B1 follow-up): KR0050 BS item 15 (유형자산) for 2023.1Q-3Q must exclude 사용권자산.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_kr0050_ppe.py [--spec out.json]

The 2023 quarterly statements print 사용권자산 INSIDE the 유형자산 line (note 14: 「사용권자산은 유형자산에 포함되어 재무제표에 표시됩니다」); from 2023.12.31 the
audited statements (the master's year-end anchor 103.4억) and every 2024+ statement print 유형자산 and 사용권자산 as two lines.  The master definition (the anchor
series 2023.4Q 103.40억 -> 2024.1Q 95.9억 ...) is the owned 유형자산, so for 2023.1Q-3Q: item 15 = BS 유형자산 - 사용권자산 장부금액 (note 14, 천원).
Cross-check: the note's own lines 토지 + 건물 + 비품 + 임차점포시설물 must equal the same difference.  Spec = `replace` of the 3 cells loaded by round B1.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_apply_attfs as A  # noqa: E402
from bspl_granularity.pdfrows import rows_from_page  # noqa: E402

CODE = "KR0050"


def note14(pdf: Path):
    """returns (page, {label: [취득원가, 감가상각누계액, 장부금액] in 천원}) of the FIRST 유형자산 내역 block (당기말); the table may continue on the next page."""
    doc = fitz.open(str(pdf))
    for i in range(25, min(len(doc) - 1, 45)):
        flat = "".join(doc[i].get_text().split())
        if "14.유형자산" in flat and "취득원가" in flat:
            rows = []
            for j in (i, i + 1):
                rr, free = rows_from_page(doc[j], pageno=j + 1)
                if j == i:                              # keep only the rows BELOW the 「14. 유형자산」 title (the page may start with note 13)
                    ty = [y for y, _x, t in free if "14." in t.replace(" ", "") and "유형자산" in t.replace(" ", "")]
                    if ty:
                        rr = [r for r in rr if r.y > min(ty)]
                rows += rr
            cur = {}
            for r in rows:
                lab = r.label
                if lab == "합계":
                    cur["합계"] = list(r.vals[-3:])
                    break
                if lab and len(r.vals) >= 3:
                    cur[lab] = list(r.vals[-3:])
            if "사용권자산" in cur and "합계" in cur:
                return i + 1, cur
    raise SystemExit(f"note 14 not found in {pdf}")


def main():
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    cells = []
    for q in ("2023.1Q", "2023.2Q", "2023.3Q"):
        y, n = q.split(".")
        pdf = ROOT / "data" / "disclosure" / f"FY{y}_Q{n[0]}" / "attachments" / "KR0050_하나손해보험_attachment_separate_fs.pdf"
        rows, unit, page = A.read_bs(pdf)
        items = A.to_items(rows)
        ppe_line = items[15][1][0]
        npage, tab = note14(pdf)
        rou = tab["사용권자산"][2] / 1000.0
        owned_lines = sum(tab[k][2] for k in tab if k not in ("사용권자산", "합계")) / 1000.0
        total_note = tab["합계"][2] / 1000.0
        derived = ppe_line - rou
        print(f"{q}: BS 유형자산 {ppe_line:,.6f}  note 합계 {total_note:,.3f}  사용권자산 {rou:,.3f}  -> owned {derived:,.6f}; note owned lines {owned_lines:,.3f}"
              f" (diff {derived - owned_lines:+.4f})")
        assert abs(derived - owned_lines) < 0.0025 and abs(ppe_line - total_note) < 0.0025, (q, derived, owned_lines)
        old = mv[(CODE, 15, q)]
        assert abs(old - ppe_line) < 1e-6, (q, old, ppe_line)
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        basis = (f"정정 2026-10-11(round 3, B1 후속): 같은 라운드에서 적재한 값 {old:,.6f}백만원은 {q} 분기재무제표 첨부(별도) 재무상태표 「유형자산」 줄 그대로인데, 2023 분기 재무제표는 "
                 f"사용권자산을 유형자산 줄 안에 표시한다(주석 14 p{npage}: 「사용권자산은 유형자산에 포함되어 재무제표에 표시됩니다」, 사용권자산 장부금액 {rou * 1000:,.0f}천원). "
                 f"마스터 항목 15 의 정의는 자기 소유 유형자산이다(연말 DART 감사 앵커 2023.4Q 103.40억 = 유형자산 줄이고 사용권자산은 별도 줄 11,700.245백만원; 2024.1Q 첨부 전기말 열이 "
                 f"이를 재현). 그래서 {q} 값 = 유형자산 줄 {ppe_line:,.6f} − 사용권자산 {rou:,.3f}(주석 14, 천원 정밀도 ±0.0005) = {derived:,.6f}백만원. 같은 주석의 토지·건물·비품·"
                 f"임차점포시설물 장부금액 합 {owned_lines:,.3f}백만원과 일치. 계열: 2022-12 11,432.754 → {q} {derived:,.1f} → 2023.4Q 10,340.348 → 2024.1Q 9,591.349.")
        cells.append({"key": f"{CODE}|15|{q}", "item": 15, "quarter": q, "action": "replace", "old": old, "new": round(derived, 6), "line": "유형자산(사용권자산 제외)",
                      "pdf": pdf.relative_to(ROOT).as_posix(), "page": npage, "pdf_sha256": sha, "basis": basis,
                      "method": "round3_fix:attachment_separate_fs_ppe_ex_rou", "scale": "원 -> 백만원"})
    if "--spec" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--spec") + 1])
        out.write_text(json.dumps({"_what": "B1 follow-up KR0050 item 15 excluding right-of-use assets", "cells": cells}, ensure_ascii=False, indent=1),
                       encoding="utf-8", newline="\n")
        print("spec ->", out)


if __name__ == "__main__":
    main()
