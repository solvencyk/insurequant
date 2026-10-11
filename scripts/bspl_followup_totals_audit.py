#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), steps 1+2: master TOTALS (items 1/2/3) vs the disclosure, every company x quarter.

Totals have no definition ambiguity (separate-basis assets / liabilities / equity), so a gross disagreement between a master total
and the same filing's printed total is a master error unless the master is a restated comparative.  Source = the Stage-B candidate
files of the 2026-10-11 granularity run (current-column `EXISTS_*` records for items 1/2/3 incl. the `EXISTS_BASIS` class that the
first run treated as informational) -> nothing is re-read from the PDFs here.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_totals_audit.py
Output: data/_derived/bspl_followup_20261011/totals_audit.json  (+ printed table of disagreements > 0.5 %)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "totals_audit.json"


def main():
    rows = []
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d["candidates"]:
            if c["item"] not in (1, 2, 3) or not str(c["status"]).startswith("EXISTS"):
                continue
            m, v = c.get("master"), c.get("value_mn")
            if m in (None, 0) or v is None:
                continue
            rel = (v - m) / abs(m)
            rows.append({"code": c["code"], "quarter": c["quarter"], "item": c["item"], "status": c["status"],
                         "master": m, "disclosure": v, "rel_diff": rel, "kind": c.get("kind"), "rule": c.get("rule"),
                         "page": c.get("page")})
    rows.sort(key=lambda r: -abs(r["rel_diff"]))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    big = [r for r in rows if abs(r["rel_diff"]) > 0.005]
    print(f"records {len(rows)}; > 0.5 % : {len(big)}")
    for r in big:
        print(f"{r['code']} {r['quarter']} item{r['item']} {r['status']:<12} master {r['master']:>16,.2f} disclosure {r['disclosure']:>16,.2f} "
              f"rel {r['rel_diff']:+.3%} ({r['kind']} p{r['page']})")


if __name__ == "__main__":
    main()
