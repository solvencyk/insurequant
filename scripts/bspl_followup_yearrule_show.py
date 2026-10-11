#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show the OK-ish year-rule verdict cells with master neighbours (read-only)."""
import json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
rep = json.loads((ROOT / "data/_derived/bspl_followup_20261011/yearrule_report.json").read_text(encoding="utf-8"))
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
mv = defaultdict(dict)
for r in bs:
    mv[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
want = set(sys.argv[1:]) or {"SIBLING_OK", "OWN_OPENING_OK", "OWN_OK_SIB_FAIL", "OWN_CURRENT_ONLY_OK"}
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
for r in rep:
    if r["verdict"] not in want:
        continue
    ser = mv[(r["code"], r["item"])]
    s = " ".join(f"{q[2:]}={ser[q]/100:,.0f}" if q in ser and ser[q] is not None else f"{q[2:]}=-" for q in QS)
    print(f"{r['key']} {r['verdict']} {r['status']} val={r['value_mn']/100:,.1f}억 rule={r['rule']}|{r['kind']}|{r['form']}")
    print("    master(억):", s)
    for e in r["own"][:3]:
        print("    own:", e)
    for e in r["sib"][:4]:
        print("    sib:", e)
