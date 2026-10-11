#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c: per (company, item) evidence table for the HOLD_REJECTED_RULE cells.

For each group of held cells it lists the rejected concepts of the item with their calibration evidence (observed disclosure value vs the master's
DART / audit anchor at year-ends, current and comparative columns) so that the cause of the definition break can be named (separate-account
inclusion, supervisory vs K-IFRS line, aggregation, restated comparative, zero line) and a year-specific rule can be looked for.
Output: data/_derived/bspl_followup_20261011/rejected_groups.json (+ printed compact table).  Read-only.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "rejected_groups.json"


def main():
    groups = {}
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        held = defaultdict(list)
        for c in d["candidates"]:
            if c["status"] == "HOLD_REJECTED_RULE":
                held[c["item"]].append(c)
        for item, cells in held.items():
            conc = {}
            for ck, cv in d["calibration"].items():
                if not ck.startswith(f"{item}:"):
                    continue
                ev = cv["evidence"]
                bad = [e for e in ev if not e[4]]
                conc[ck] = {"status": cv["status"], "n": len(ev), "bad": len(bad),
                            "pairs": [(e[0], e[1], e[2], e[3], round(e[5], 1), round(e[6], 1)) for e in ev[:12]]}
            groups[f"{d['code']}|{item}"] = {
                "code": d["code"], "name": d.get("name"), "item": item,
                "held_quarters": sorted(c["quarter"] for c in cells),
                "held_values": {c["quarter"]: round(c["value_mn"], 1) for c in cells}, "held_rules": sorted({f"{c['rule']}|{c['kind']}|{c['form']}" for c in cells}),
                "concepts": conc}
    OUT.write_text(json.dumps(groups, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(len(groups), "groups")
    for k, g in sorted(groups.items()):
        print(f"\n{k} {g['name']}  held {len(g['held_quarters'])}: {g['held_quarters'][0]}..{g['held_quarters'][-1]}  rules {g['held_rules']}")
        for ck, cv in g["concepts"].items():
            if cv["n"] == 0:
                continue
            yo = [(p[1], p[2], p[3][0], p[4], p[5]) for p in cv["pairs"] if p[1].endswith("4Q")][:4]
            print(f"    {ck:<36} {cv['status']:<9} n={cv['n']:>3} bad={cv['bad']:>3}  year-end (period,col,kind,obs,anchor): {yo}")


if __name__ == "__main__":
    main()
