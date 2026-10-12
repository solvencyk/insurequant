"""Dump text of local K-ICS regulation sources (fitz) with page markers.

Read-only: reads research/*.pdf, writes *.txt next to this script.
Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_definition_20261012/dump_regulation_text.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz  # PyMuPDF

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCES = {
    "kics_haeseolseo.txt": REPO / "research" / "新지급여력제도(K-ICS) 해설서.pdf",
    "kr_ratings_report.txt": REPO / "research" / "한국기업평가 송미정 연구원 리포트.pdf",
}


def main() -> int:
    for out_name, pdf in SOURCES.items():
        if not pdf.is_file():
            print(f"missing: {pdf}", file=sys.stderr)
            continue
        doc = fitz.open(pdf)
        parts = []
        empty = 0
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if not text.strip():
                empty += 1
            parts.append(f"\n===== PDF_PAGE {i + 1} =====\n{text}")
        (HERE / out_name).write_text("".join(parts), encoding="utf-8")
        print(f"{out_name}: pages={doc.page_count} empty_text_pages={empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
