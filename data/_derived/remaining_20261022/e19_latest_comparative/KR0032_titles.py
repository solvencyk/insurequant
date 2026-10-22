# -*- coding: utf-8 -*-
import re
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
L = []
for q in ("2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4", "2024_Q1", "2024_Q2", "2024_Q3", "2024_Q4", "2025_Q1", "2025_Q2", "2025_Q3", "2025_Q4"):
    fy = "FY" + q
    d = sorted((ROOT / "data/dart" / fy / "raw").glob("KR0032_*"))[0]
    for p in sorted(list(d.glob("*.xml")) + list(d.glob("xml/*.xml"))):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        L.append(f"== {fy} {rel} size={p.stat().st_size}")
        with open(p, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if line.startswith("<TITLE") and ("손익계산서" in line or "재무상태표" in line or "재무제표" in line):
                    L.append(f"  L{i} {line.strip()[:160]}")
(OUT / "KR0032_titles.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
