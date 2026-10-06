# -*- coding: utf-8 -*-
"""괄호 값의 의미를 문서 내부 근거로 가르기 위한 census.

가설: 한 문서가 음수 표기를 두 가지로 쓰지는 않는다. 표 안에 세모(△/▲)나 선행 마이너스(-123)가
쓰였다면 그 표의 `(123)` 은 음수 부호가 아니라 '~중' 을 뜻하는 소계 괄호다(경영공시 표준서식은
소계 행 라벨을 `(보험수익)` 처럼 괄호로 적는다). 반대로 세모도 마이너스도 없는 표라면 `(123)` 이
그 표의 유일한 음수 표기다.

이 스크립트는 그 가설이 실제로 배타적인지(= 두 표기가 섞이는 표가 있는지) 전수로 잰다.

산출: data/_derived/_probe_20260918h_paren_markers.json
실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260918h_paren_marker_census.py
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz  # noqa: E402

from extract_pl_backfill_disclosure import (  # noqa: E402
    ROOT, _core_label_hits, _find_idx_cur, find_pdf, target_cells,
)

fitz.TOOLS.mupdf_display_errors(False)
OUT = os.path.join(ROOT, "data", "_derived", "_probe_20260918h_paren_markers.json")

RE_PAREN = re.compile(r"^\(\s*[\d,]+(\.\d+)?\s*\)$")
RE_MINUS = re.compile(r"^-\s*[\d,]+(\.\d+)?$")
RE_SAMO = re.compile(r"^[\u25b3\u25b2]\s*[\d,]+(\.\d+)?$")


def markers_of(pdf_path, max_pages=40):
    doc = fitz.open(pdf_path)
    try:
        for i in range(min(max_pages, doc.page_count)):
            page = doc[i]
            t = page.get_text()
            if "포괄손익계산서" not in t or _core_label_hits(t) < 3:
                continue
            try:
                tabs = page.find_tables()
            except Exception:
                continue
            for tab in tabs.tables:
                rows = tab.extract()
                if not rows or len(rows) < 5:
                    continue
                if _find_idx_cur(rows) is None:
                    continue
                paren = minus = samo = 0
                paren_samples, negparen_samples = [], []
                for row in rows:
                    for v in row:
                        if v is None:
                            continue
                        for piece in str(v).split("\n"):
                            s = piece.strip().replace(" ", "")
                            if RE_PAREN.match(s):
                                paren += 1
                                if len(paren_samples) < 4:
                                    paren_samples.append(s)
                            elif RE_MINUS.match(s):
                                minus += 1
                            elif RE_SAMO.match(s):
                                samo += 1
                return {"paren": paren, "minus": minus, "samo": samo,
                        "paren_samples": paren_samples, "page": i + 1}
    finally:
        doc.close()
    return None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    out = []
    both = mixed_note = 0
    for code, q in target_cells():
        pdf = find_pdf(code, q)
        if pdf is None:
            continue
        m = markers_of(pdf)
        if m is None:
            continue
        m["code"], m["quarter"] = code, q
        m["negative_marker"] = ("samo_or_minus" if (m["samo"] or m["minus"])
                                else ("paren" if m["paren"] else "none"))
        if m["paren"] and (m["samo"] or m["minus"]):
            both += 1
        out.append(m)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"cells": out}, f, ensure_ascii=False, indent=1)

    print(f"표 검출 셀 {len(out)}개")
    print(f"괄호값과 (세모/마이너스)가 **같은 표에 공존** 하는 셀: {both}")
    print()
    print("괄호값이 있는 셀 전건:")
    for m in out:
        if not m["paren"]:
            continue
        print(f"  {m['code']} {m['quarter']:<8} paren={m['paren']:<3} samo={m['samo']:<3} "
              f"minus={m['minus']:<3} -> negative_marker={m['negative_marker']:<14} "
              f"samples={m['paren_samples']}")
    print()
    n_by = {}
    for m in out:
        n_by[m["negative_marker"]] = n_by.get(m["negative_marker"], 0) + 1
    print("negative_marker 분포:", n_by)
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
