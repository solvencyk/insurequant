# -*- coding: utf-8 -*-
"""read-only: TITLE lines (statements + notes headers) of the Hyundai filings used by the load"""
import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
FILES = {
 "N1": "data/dart/FY2024_Q1/raw/KR0009_현대해상/20240516002153.xml",
 "N2": "data/dart/FY2024_Q2/raw/KR0009_현대해상/20240814004187.xml",
 "N3": "data/dart/FY2024_Q3/raw/KR0009_현대해상/20241114003026.xml",
 "N4": "data/dart/FY2024_Q4/raw/KR0009_현대해상_20250313001346/20250313001346.xml",
}
TAG = re.compile(r"<[^>]+>")
for k, rel in FILES.items():
    L = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    print("=" * 100)
    print(k, rel, "lines", len(L))
    for i, s in enumerate(L):
        if s.startswith("<TITLE"):
            t = re.sub(r"\s+", " ", TAG.sub("", s)).strip()
            if re.search(r"재무제표|포괄손익|재무상태|주석|보험계약|보험수익|보험서비스", t) and len(t) < 90:
                print(f"  L{i+1}: {t}")
