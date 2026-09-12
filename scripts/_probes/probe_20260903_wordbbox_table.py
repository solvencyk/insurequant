"""Dump word-level bounding boxes for a page, clustered into rows by y-coordinate,
for reconstructing a table whose linear text reading-order is scrambled (multi-row-span
labels docling/fitz sometimes emit out of visual order).

Usage:
    python scripts/_probes/probe_20260903_wordbbox_table.py KR0051 2026.2Q 17
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import fitz  # noqa: E402
from _disclosure_pdf_paths import disclosure_pdfs, period_of  # noqa: E402


def main(argv: list[str]) -> int:
    code, quarter, page_1idx = argv[0], argv[1], int(argv[2])
    period = period_of(quarter)
    pdfs = disclosure_pdfs(period, code)
    if not pdfs:
        print("NO PDF")
        return 1
    doc = fitz.open(pdfs[0])
    page = doc.load_page(page_1idx - 1)
    words = page.get_text("words")  # (x0, y0, x1, y1, text, block, line, word)
    # cluster by rounded y0 (row)
    rows: dict[int, list[tuple[float, str]]] = {}
    for x0, y0, x1, y1, text, *_ in words:
        key = round(y0 / 3) * 3  # 3pt bucket
        rows.setdefault(key, []).append((x0, text))
    for y in sorted(rows):
        cells = sorted(rows[y], key=lambda t: t[0])
        line = "  |  ".join(f"{t}" for _, t in cells)
        print(f"y={y:6.1f}: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
