#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17, inbox/parser/20261011T1130Z): show PL master cells of one company (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_plcells.py KR0008 2023.1Q 2023.2Q 2023.3Q [--items 1,2,13,14]

Prints one line per item with the YTD value (`값`) and the quarterly value (`값_당분기`) per quarter, in 백만원.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

args = sys.argv[1:]
items = None
if "--items" in args:
    i = args.index("--items")
    items = {int(x) for x in args[i + 1].split(",")}
    args = args[:i] + args[i + 2:]
code, qs = args[0], args[1:]
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
rows = defaultdict(dict)
nm = {}
for r in pl:
    if r["원보험사코드"] == code and r["공시분기"] in qs:
        it = int(r["항목번호"]) if str(r["항목번호"]).isdigit() else r["항목번호"]
        if items and it not in items:
            continue
        rows[it][r["공시분기"]] = (r.get("값"), r.get("값_당분기"))
        nm[it] = r.get("항목명")


def f(v):
    return "-" if v is None else f"{v:,.1f}"


print(f"{'item':>5} {'name':<26}" + "".join(f"{q:>34}" for q in qs))
for it in sorted(rows, key=lambda x: (isinstance(x, str), x)):
    print(f"{str(it):>5} {str(nm[it])[:24]:<26}" + "".join(
        (f"{f(rows[it][q][0]):>17} /{f(rows[it][q][1]):>15}" if q in rows[it] else f"{'':>34}") for q in qs))
