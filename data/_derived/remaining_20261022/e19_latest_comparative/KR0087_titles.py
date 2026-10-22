# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
FILES = {
 "FY2023_Q4": "data/dart/FY2023_Q4/raw/KR0087_동양생명_20240320001755/20240320001755.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0087_동양생명_20250319000486/20250319000486.xml",
 "FY2025_Q1": "data/dart/FY2025_Q1/raw/KR0087_동양생명/20250515001025.xml",
 "FY2025_Q2": "data/dart/FY2025_Q2/raw/KR0087_동양생명/xml/20250814002600.xml",
 "FY2025_Q3": "data/dart/FY2025_Q3/raw/KR0087_동양생명/xml/20251114002594.xml",
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0087_동양생명/20240516001580.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0087_동양생명/20240814002284.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0087_동양생명/20241114000876.xml",
}
L = []
for fy, rel in FILES.items():
    p = ROOT / rel
    n = 0
    L.append(f"== {fy} {rel} exists={p.exists()}")
    with open(p, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if line.startswith("<TITLE") and ("손익계산서" in line or "재무상태표" in line):
                L.append(f"  L{i} {line.strip()[:160]}")
(OUT / "KR0087_titles.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
