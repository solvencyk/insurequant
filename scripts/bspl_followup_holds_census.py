#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5: census of the Stage-B BS holds (HOLD_UNTESTED / HOLD_REJECTED_RULE) on the CURRENT candidate files.

Output: data/_derived/bspl_followup_20261011/holds_census.json  +  printed breakdown (company x status, item x zero/non-zero, form/kind).
Read-only.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "holds_census.json"


def main():
    rows = []
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d["candidates"]:
            if c["status"] in ("HOLD_UNTESTED", "HOLD_REJECTED_RULE", "HOLD_TRIO", "HOLD_PARTIAL_GROUP", "HOLD_QOQ", "HOLD_ALT_DISAGREE", "HOLD_KPI_DIFF"):
                rows.append({**{k: c.get(k) for k in ("code", "item", "quarter", "status", "value_mn", "rule", "kind", "form", "page", "unit", "prec_mn")},
                             "zero": abs(c.get("value_mn") or 0.0) < 1e-9})
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("holds:", dict(Counter(r["status"] for r in rows)))
    for st in ("HOLD_UNTESTED", "HOLD_REJECTED_RULE"):
        sub = [r for r in rows if r["status"] == st]
        print(f"\n=== {st}: {len(sub)}  zero {sum(1 for r in sub if r['zero'])}  non-zero {sum(1 for r in sub if not r['zero'])}")
        by_co = Counter((r["code"], r["zero"]) for r in sub)
        print(" by company (zero/nonzero):", {c: f"{by_co[(c, True)]}/{by_co[(c, False)]}" for c in sorted({r['code'] for r in sub})})
        by_it = Counter((r["item"], r["zero"]) for r in sub)
        print(" by item (zero/nonzero):", {i: f"{by_it[(i, True)]}/{by_it[(i, False)]}" for i in sorted({r['item'] for r in sub})})
        print(" by form/kind:", dict(Counter((r["form"], r["kind"]) for r in sub)))


if __name__ == "__main__":
    main()
