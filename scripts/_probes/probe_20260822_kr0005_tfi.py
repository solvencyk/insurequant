# -*- coding: utf-8 -*-
"""
Probe: KR0005 (흥국화재) FY2024_Q4 raw PDF - locate "1) 공통적용 경과조치" TFI table
(items 47/48/49/50/51). Read-only investigation, writes only to scratchpad JSON.

Usage (venv python only):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260822_kr0005_tfi.py
"""
import json
import sys
from pathlib import Path

import fitz  # PyMuPDF

PDF = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2024_Q4\raw\KR0005_흥국화재.pdf")
OUT = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\c9c7c053-f96a-4878-bcb0-5ff8567de9fd\scratchpad\kr0005_tfi")
OUT.mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF)
n = doc.page_count

result = {"pdf": str(PDF), "n_pages": n, "page91_0idx_text": None, "per_page_chars": []}

# Step 1: page 91 (0-idx) text dump
if n > 91:
    p91_text = doc[91].get_text()
    result["page91_0idx_text"] = p91_text
    (OUT / "page91_0idx.txt").write_text(p91_text, encoding="utf-8")

# Step 2: per-page char density (corroborate prior finding)
for i in range(n):
    t = doc[i].get_text()
    result["per_page_chars"].append({"page_0idx": i, "page_1idx": i + 1, "chars": len(t)})

(OUT / "probe_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Also print a compact summary to stdout (ascii-safe only, avoid cp949 crash)
dense = [r for r in result["per_page_chars"] if r["chars"] >= 50]
sys.stdout.write(f"n_pages={n}\n")
sys.stdout.write(f"page91_0idx_chars={len(result['page91_0idx_text'] or '')}\n")
sys.stdout.write(f"pages_with_chars>=50: {[r['page_1idx'] for r in dense]}\n")
sys.stdout.write("wrote: " + str(OUT / "probe_result.json") + "\n")
sys.stdout.write("wrote: " + str(OUT / "page91_0idx.txt") + "\n")

doc.close()
