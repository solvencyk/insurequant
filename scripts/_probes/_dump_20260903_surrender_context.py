# -*- coding: utf-8 -*-
"""해약환급금준비금 절 문맥 덤프 — 2026.2Q raw/ 대상, 일회성 진단."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "raw"

CODES = sys.argv[1:] if len(sys.argv) > 1 else [
    "KR0049", "KR0051", "KR0072", "KR0075", "KR0097",
]

GENERIC_RE = re.compile(r"해약환급금\s*준비금")

all_pdfs = sorted(RAW_DIR.glob("*.pdf"))
for code in CODES:
    matches = [p for p in all_pdfs if p.name.startswith(code + "_")]
    if not matches:
        print(f"=== {code}: FILE NOT FOUND ===")
        continue
    path = matches[0]
    doc = fitz.open(str(path))
    print(f"=== {code} ({path.name}, {doc.page_count}p) ===")
    for pno in range(doc.page_count):
        text = doc[pno].get_text()
        for m in GENERIC_RE.finditer(text):
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 300)
            snippet = text[start:end].replace("\n", " | ")
            print(f"  p{pno + 1}: ...{snippet}...")
    doc.close()
    print()
