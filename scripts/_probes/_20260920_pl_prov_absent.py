#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Why does extract_tier1() find nothing in these raw dirs, and where did the master's
income_statement values actually come from?  Checks: XML inventory, gold overlay,
_GOLD_CELL_OVERRIDE, and the master's non-null income_statement items."""
import glob
import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

PL_CONTRACT_NOTES = {4, 5, 6, 9, 10, 11, 13, 14}
CODES = sys.argv[1:] or ["KR0003", "KR0008", "KR0009", "KR0032", "KR0069",
                         "KR0072", "KR0073", "KR0079", "KR0099", "KR0104", "KR1000"]
Q = "2023.1Q"

rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
goldset = {}
for s in gold.get("set", []):
    try:
        goldset[(s.get("원보험사코드"), s.get("공시분기"), int(s["항목번호"]))] = s.get("값")
    except (TypeError, ValueError, KeyError):
        pass

from scripts.build_pl_breakdown import _GOLD_CELL_OVERRIDE  # noqa: E402

vals = {}
for r in rows:
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    vals.setdefault((r.get("원보험사코드"), r.get("공시분기")), {})[it] = r.get("값")

for code in CODES:
    v = vals.get((code, Q), {})
    isv = {k: x for k, x in v.items() if k not in PL_CONTRACT_NOTES and x is not None}
    cnv = {k: x for k, x in v.items() if k in PL_CONTRACT_NOTES and x is not None}
    dirs = sorted(glob.glob(f"data/dart/FY2023_Q1/raw/{code}_*"))
    print(f"\n=== {code} {Q} ===")
    print(f"  master income_statement non-null: {sorted(isv)} -> {dict(list(isv.items())[:6])}")
    print(f"  master contract_notes  non-null: {sorted(cnv)}")
    gk = [k for k in goldset if k[0] == code and k[1] == Q]
    print(f"  user_pl_cells.json entries: {sorted(x[2] for x in gk)}")
    print(f"  _GOLD_CELL_OVERRIDE: {sorted(_GOLD_CELL_OVERRIDE.get((code, Q), {}))}")
    for d in dirs:
        xs = sorted(set(glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml")
                        + glob.glob(d + "/extracted*/*.xml")))
        others = [os.path.basename(p) for p in sorted(glob.glob(d + "/*")) if not p.endswith(".xml")]
        print(f"  dir {os.path.basename(d)}: xml={[(os.path.basename(x), os.path.getsize(x)) for x in xs]} other={others}")
