# -*- coding: utf-8 -*-
import re
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
FILES = {
 "FY2023_Q1": "data/dart/FY2023_Q1/raw/KR0104_농협생명보험/20230515002904.xml",
 "FY2023_Q2": "data/dart/FY2023_Q2/raw/KR0104_농협생명보험/20230814001979.xml",
 "FY2023_Q3": "data/dart/FY2023_Q3/raw/KR0104_농협생명보험/20231114001637.xml",
 "FY2023_Q4": "data/dart/FY2023_Q4/raw/KR0104_농협생명보험_20240401002122/20240401002122.xml",
 "FY2024_Q1": "data/dart/FY2024_Q1/raw/KR0104_농협생명보험/20240514001371.xml",
 "FY2024_Q2": "data/dart/FY2024_Q2/raw/KR0104_농협생명보험/20240814002115.xml",
 "FY2024_Q3": "data/dart/FY2024_Q3/raw/KR0104_농협생명보험/20241114000851.xml",
 "FY2024_Q4": "data/dart/FY2024_Q4/raw/KR0104_농협생명보험_20250331003065/20250331003065.xml",
}
L = []
for fy, rel in FILES.items():
    p = ROOT / rel
    L.append(f"== {fy} {rel} exists={p.exists()}")
    with open(p, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if line.startswith("<TITLE") and ("손익계산서" in line or "재무상태표" in line or "재무제표" in line):
                L.append(f"  L{i} {line.strip()[:160]}")
(OUT / "KR0104_titles.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
