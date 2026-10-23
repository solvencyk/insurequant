# -*- coding: utf-8 -*-
"""pass2 s03 (read-only): list the raw main filings per company and FY (mlib.main_xmls) for the companies of ticket 20261024T0300Z."""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CODES = sys.argv[1].split(",") if len(sys.argv) > 1 else ["KR0070", "KR0087", "KR0009", "KR0068", "KR0079", "KR0005", "KR0032", "KR0082", "KR0099"]
for c in CODES:
    print("==", c)
    for y in (2023, 2024, 2025, 2026):
        for q in (1, 2, 3, 4):
            fy = f"FY{y}_Q{q}"
            ps = [p for p in M.main_xmls(c, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))]
            print(f"  {fy}: " + (", ".join(f"{M.rel(p)} ({p.stat().st_size // 1024} KB)" for p in ps[:2]) if ps else "-"))
