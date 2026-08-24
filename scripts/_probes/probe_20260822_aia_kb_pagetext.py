# -*- coding: utf-8 -*-
"""특정 (문서, 페이지) 목록의 raw get_text() 를 파일로 덤프 (육안+검색 사전조사)."""
from __future__ import annotations

import json
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "scripts" / "_probes" / "aia_kb_pagetext_out.txt"

JOBS = [
    ("AIA 2024.4Q p171,p330 (기본자본 hit)",
     r"data\disclosure\FY2024_Q4\raw\KR0080_에이아이에이생명보험.pdf", [171, 330]),
    ("AIA 2025.4Q p174,p341 (기본자본 hit)",
     r"data\disclosure\FY2025_Q4\raw\KR0080_에이아이에이생명보험.pdf", [174, 341]),
    ("AIA 2025.1Q p6,7,8 (real text block)",
     r"data\disclosure\FY2025_Q1\raw\KR0080_에이아이에이생명보험.pdf", [6, 7, 8]),
    ("AIA 2025.3Q p1,p23-31 (real text blocks)",
     r"data\disclosure\FY2025_Q3\raw\KR0080_에이아이에이생명보험.pdf", [1, 23, 24, 25, 26, 27, 28, 29, 30]),
    ("AIA 2026.1Q p1,p27-34",
     r"data\disclosure\FY2026_Q1\raw\KR0080_에이아이에이생명보험.pdf", [1, 27, 28, 29, 30, 31, 32, 33]),
    ("AIA 2025.2Q p47-50",
     r"data\disclosure\FY2025_Q2\raw\KR0080_에이아이에이생명보험.pdf", [47, 48, 49, 50]),
]


def main():
    lines = []
    for label, relpath, pages in JOBS:
        pdf = REPO / relpath
        lines.append(f"\n{'='*80}\n{label}  ({pdf.name})\n{'='*80}")
        if not pdf.exists():
            lines.append("  [MISSING FILE]")
            continue
        doc = fitz.open(pdf)
        try:
            for p in pages:
                if p >= doc.page_count:
                    lines.append(f"--- page0={p} OUT OF RANGE (n={doc.page_count}) ---")
                    continue
                t = doc[p].get_text()
                lines.append(f"--- page0={p} (printed~{p+1}) chars={len(t)} ---")
                lines.append(t)
        finally:
            doc.close()

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
