# -*- coding: utf-8 -*-
"""하나손해(KR0050) 2023.2Q '라벨 매칭 실패' 원인 확인 — 공통적용경과조치 표 원문 전체 덤프."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

raw = REPO / "data" / "disclosure" / "FY2023_Q2" / "raw"
pdf = max(sorted(raw.glob("KR0050_*.pdf")), key=lambda p: p.stat().st_size)
print(pdf)
doc = fitz.open(pdf)
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "공통적용" in t and "보완자본" in t and "한도" in t:
        print(f"--- page {i} ---")
        print(t)
doc.close()
