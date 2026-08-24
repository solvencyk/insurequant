# -*- coding: utf-8 -*-
"""AIA 나머지 4분기 + KB 5분기의 TOC 페이지(0,1,2 인덱스) 텍스트 덤프."""
from __future__ import annotations

from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "scripts" / "_probes" / "toc_dump_out.txt"

JOBS = [
    ("AIA 2024.4Q", r"data\disclosure\FY2024_Q4\raw\KR0080_에이아이에이생명보험.pdf"),
    ("AIA 2025.2Q", r"data\disclosure\FY2025_Q2\raw\KR0080_에이아이에이생명보험.pdf"),
    ("AIA 2025.4Q", r"data\disclosure\FY2025_Q4\raw\KR0080_에이아이에이생명보험.pdf"),
    ("KB 2024.1Q", r"data\disclosure\FY2024_Q1\raw\KR0010_KB손해보험_amended.pdf"),
    ("KB 2024.3Q", r"data\disclosure\FY2024_Q3\raw\KR0010_KB손해보험_amended.pdf"),
    ("KB 2025.3Q", r"data\disclosure\FY2025_Q3\raw\KR0010_KB손해보험.pdf"),
    ("KB 2025.4Q", r"data\disclosure\FY2025_Q4\raw\KR0010_KB손해보험.pdf"),
    ("KB 2026.1Q", r"data\disclosure\FY2026_Q1\raw\KR0010_KB손해보험.pdf"),
]


def main():
    lines = []
    for label, relpath in JOBS:
        pdf = REPO / relpath
        lines.append(f"\n{'='*80}\n{label} ({pdf.name}, exists={pdf.exists()})\n{'='*80}")
        if not pdf.exists():
            continue
        doc = fitz.open(pdf)
        try:
            for p in range(min(4, doc.page_count)):
                t = doc[p].get_text()
                lines.append(f"--- page0={p} chars={len(t)} ---")
                lines.append(t)
        finally:
            doc.close()
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
