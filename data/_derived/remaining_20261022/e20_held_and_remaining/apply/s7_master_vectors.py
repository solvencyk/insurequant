#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 7: live PL_breakdown.json vectors (items 1,16..32; 값 and 값_당분기) of every target company over 2023.1Q-2026.2Q -> s7_master_vectors.txt (read-only)"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/apply/s7_master_vectors.txt"
CODES = ["KR0082", "KR0083", "KR0087", "KR0104", "KR0032", "KR0069", "KR0094", "KR0070", "KR0072", "KR0068", "KR0071"]
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
by = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in live}
qs = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4) if not (y == 2026 and n > 2)]
L = []
for c in CODES:
    L.append(f"===== {c}  (값 = 연누계; [ ] = 값_당분기)")
    for it in [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]:
        cells = []
        for q in qs:
            r = by.get((c, it, q))
            if r is None or r["값"] is None:
                cells.append(f"{q}:-")
            else:
                d = r.get("값_당분기")
                cells.append(f"{q}:{r['값']:.3f}[{'-' if d is None else format(d, '.3f')}]")
        L.append(f" i{it:>2} " + "  ".join(cells))
text = "\n".join(L)
OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
print(len(text))
