"""Dump raw fitz text for specific 1-indexed pages of a company's 2026.1Q PDF."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz

REPO = Path(__file__).resolve().parent.parent.parent

if len(sys.argv) < 3:
    print("usage: dump_pdf_pages.py <PDF_NAME> <page1,page2,...>")
    sys.exit(1)

pdf_name = sys.argv[1]
pages = [int(p) for p in sys.argv[2].split(",")]

pdf_path = REPO / "data" / "disclosure" / "FY2026_Q1" / "raw" / pdf_name
doc = fitz.open(pdf_path)
for p in pages:
    print(f"\n{'='*20} PAGE {p} {'='*20}")
    print(doc[p - 1].get_text())
doc.close()
