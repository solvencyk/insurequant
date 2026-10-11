#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17, inbox/parser/20261011T1130Z): print the master series of BS items for companies (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_series.py KR1000,KR0001 10,11
Prints, per company and item, the value (억원) for each of the 14 quarters; '*' marks a cell with a lineage-sidecar entry
(= loaded from the management disclosure / manual), '-' = blank.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

QS = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
codes = sys.argv[1].split(",")
items = [int(x) for x in sys.argv[2].split(",")]
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
side = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
ov = json.loads((ROOT / "data/dart/viz/bs_manual_overrides.json").read_text(encoding="utf-8"))["cells"]
idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in bs}
nm = {r["원보험사코드"]: r["원수사명"] for r in bs}
print(f"{'':>26}" + "".join(f"{q:>11}" for q in QS))
for c in codes:
    for it in items:
        cells = []
        for q in QS:
            r = idx.get((c, it, q))
            if r is None or r["값"] is None:
                cells.append(f"{'-':>11}")
            else:
                k = f"{c}|{it}|{q}"
                tag = "*" if k in side else ("o" if k in ov else " ")
                cells.append(f"{r['값'] / 100:>10,.1f}{tag}")
        print(f"{c} {nm.get(c, '')[:8]:<8}{it:>3} " + "".join(cells))
