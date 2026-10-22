# -*- coding: utf-8 -*-
import re
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
FILES = {
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험/20240516002045.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험/20240814004092.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험/20241114002738.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358/20250331001358.xml",
 "FY2025_Q1": "data/dart/FY2025_Q1/raw/KR0070_에이비엘생명보험/20250515002435.xml",
 "FY2025_Q2": "data/dart/FY2025_Q2/raw/KR0070_에이비엘생명보험/20250814004404.xml",
 "FY2025_Q3": "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험/20251114002593.xml",
 "FY2025_Q4": "data/dart/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080/20260331003080.xml",
}
L = []
for fy, rel in FILES.items():
    p = ROOT / rel
    L.append(f"== {fy} {rel} exists={p.exists()}")
    with open(p, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if line.startswith("<TITLE") and ("손익계산서" in line or "재무상태표" in line or "재무제표" in line):
                L.append(f"  L{i} {line.strip()[:160]}")
(OUT / "KR0070_titles.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
