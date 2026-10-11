#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""All master cells of one company at given quarters (read-only).   usage: bspl_followup_cellsof.py KR0070 2023.1Q 2023.2Q"""
import json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
code, qs = sys.argv[1], sys.argv[2:]
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
side = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
rows = defaultdict(dict)
nm = {}
for r in bs:
    if r["원보험사코드"] == code and r["공시분기"] in qs:
        rows[r["항목번호"]][r["공시분기"]] = r["값"]
        nm[r["항목번호"]] = r["항목명"]
print(f"{'item':>4} {'name':<22}" + "".join(f"{q:>16}" for q in qs))
for it in sorted(rows):
    print(f"{it:>4} {nm[it][:20]:<22}" + "".join((f"{rows[it][q]/100:>15,.2f}" + ("*" if f"{code}|{it}|{q}" in side else " ")) if q in rows[it] and rows[it][q] is not None else f"{'-':>16}" for q in qs))
