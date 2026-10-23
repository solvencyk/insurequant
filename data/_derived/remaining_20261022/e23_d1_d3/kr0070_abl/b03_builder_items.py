# -*- coding: utf-8 -*-
"""read-only: builder source (data/dart/viz/pl_breakdown_master.json) vs live master (PL_breakdown.json) for KR0070 FY2023 + 2024.1Q items 1..12,16 -> how items 5/6/7 look."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
src = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))}
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"]:
    print("==", q)
    for i in list(range(1, 13)) + [15, 16]:
        s = src.get(("KR0070", i, q))
        l = live.get(("KR0070", i, q))
        print(f"  i{i:>2} src={None if s is None else s.get('값')!r:>22} live={None if l is None else l.get('값')!r:>22} live_q={None if l is None else l.get('값_당분기')!r:>22}")
