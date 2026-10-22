#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 3: for every (company, FY) pair needed, list the candidate xml files and every <TITLE> that mentions 포괄손익계산서 / 재무제표 with its line number.
Output s3_titles.txt (read-only)."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_xml as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
PAIRS = {
    "KR0082": ["FY2023_Q1", "FY2023_Q2", "FY2024_Q1", "FY2024_Q2"],
    "KR0083": ["FY2024_Q3", "FY2025_Q3"],
    "KR0087": ["FY2024_Q4", "FY2025_Q4", "FY2025_Q1", "FY2026_Q1", "FY2025_Q2", "FY2026_Q2"],
    "KR0032": ["FY2023_Q1", "FY2024_Q1"],
    "KR0104": ["FY2024_Q4", "FY2025_Q4", "FY2025_Q1", "FY2026_Q1", "FY2025_Q2", "FY2026_Q2"],
    "KR0069": ["FY2025_Q1", "FY2026_Q1", "FY2025_Q2", "FY2026_Q2"],
    "KR0094": ["FY2025_Q2", "FY2026_Q2"],
    "KR0070": ["FY2025_Q1", "FY2026_Q1", "FY2025_Q2", "FY2026_Q2"],
    "KR0072": ["FY2024_Q4", "FY2025_Q4"],
    "KR0068": ["FY2024_Q4", "FY2025_Q4", "FY2025_Q1", "FY2026_Q1", "FY2025_Q2", "FY2026_Q2"],
    "KR0071": ["FY2025_Q1", "FY2026_Q1", "FY2025_Q2", "FY2026_Q2"],
}
L = []
for code, fys in PAIRS.items():
    for fy in fys:
        try:
            cands = X.candidates(code, fy)
        except Exception as e:  # noqa: BLE001
            L.append(f"## {code} {fy}: ERROR {e}")
            continue
        L.append(f"## {code} {fy}: {len(cands)} candidate xml: " + "; ".join(f"{X.rel(p)} ({p.stat().st_size})" for p in cands[:5]))
        if not cands:
            continue
        lines = X.load_lines(cands[0])
        for i, l in enumerate(lines, 1):
            if l.startswith("<TITLE") and re.search(r"포괄손익|재무제표|손익계산서", l):
                t = re.sub(r"<[^>]+>", "", l).strip()
                L.append(f"     L{i}: {t[:90]}")
text = "\n".join(L)
(HERE / "s3_titles.txt").write_text(text + "\n", encoding="utf-8", newline="\n")
print(len(text))
