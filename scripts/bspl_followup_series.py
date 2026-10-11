#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print master series (억원) of a company for the given items (read-only).   usage: bspl_followup_series.py KR0095 1 2 3 10 11"""
import json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
code = sys.argv[1]
items = [int(x) for x in sys.argv[2:]]
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
side = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
mv = defaultdict(dict)
name = {}
for r in bs:
    if r["원보험사코드"] == code:
        mv[r["항목번호"]][r["공시분기"]] = r["값"]
        name[r["항목번호"]] = r["항목명"]
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
print(" " * 16 + " ".join(f"{q[2:]:>9}" for q in QS))
for it in items:
    row = []
    for q in QS:
        v = mv[it].get(q)
        tag = "*" if f"{code}|{it}|{q}" in side else " "
        row.append(f"{v/100:>8,.0f}{tag}" if v is not None else f"{'-':>9}")
    print(f"{it:>2} {name.get(it,'')[:12]:<12} " + " ".join(row))
