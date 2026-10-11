#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c: fiscal-year-specific rule census for the held BS cells (read-only).

For every held candidate (HOLD_REJECTED_RULE / HOLD_UNTESTED, any value) of the Stage-B candidate files it collects the calibration evidence of the
SAME fiscal year as the cell (evidence entries whose PDF quarter is in the cell's year; later filings' restated comparatives do not describe the
cell's filing) for the cell's own rule and group, and classifies:

  OWN_OPENING_OK    the cell's own filing prints a prior-year-end column that reproduces the master anchor  (one table = one definition)
  OWN_FAIL          the cell's own filing disagrees with the master anchor (the filing's line is on another definition than the master's)
  SIBLING_OK        the own filing has no usable prior column, a same-year sibling filing reproduces the anchor and no same-year entry fails
  SIBLING_FAIL      ... a same-year entry fails
  NO_FY_EVIDENCE    no informative evidence in the cell's fiscal year (2023: the opening year-end 2022.4Q is IFRS4 and never an anchor)
Also prints, per held group, what the whole-history verdict was (so that a year-specific rule can be told from a hopeless one).
Output: data/_derived/bspl_followup_20261011/yearrule_report.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "yearrule_report.json"


def informative(e, own_q):
    # 'line not found' read from ANOTHER filing's comparative column (0.0 vs non-zero anchor) is not evidence
    return not (abs(e[5]) < 1e-9 and abs(e[6]) > 1e-9 and e[0] != own_q)


def main():
    rep = []
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        code = d["code"]
        for c in d["candidates"]:
            if c["status"] not in ("HOLD_REJECTED_RULE", "HOLD_UNTESTED"):
                continue
            q, item = c["quarter"], c["item"]
            y = int(q[:4])
            ckey = f"{c['rule']}|{'K' if c.get('form') == 'K' else 'S'}"
            ev_all = d["calibration"].get(ckey, {}).get("evidence", [])
            fy = [e for e in ev_all if int(e[0][:4]) == y and informative(e, q)]
            own = [e for e in fy if e[0] == q]
            sib = [e for e in fy if e[0] != q]
            bad_own = [e for e in own if not e[4]]
            bad_sib = [e for e in sib if not e[4]]
            if bad_own:
                v = "OWN_FAIL"
            elif [e for e in own if e[2] == 1 and e[1] == f"{y - 1}.4Q"]:
                v = "OWN_OPENING_OK" if not bad_sib else "OWN_OK_SIB_FAIL"
            elif own and not bad_sib:
                v = "OWN_CURRENT_ONLY_OK"
            elif sib and not bad_sib:
                v = "SIBLING_OK"
            elif sib:
                v = "SIBLING_FAIL"
            else:
                v = "NO_FY_EVIDENCE"
            rep.append({"key": f"{code}|{item}|{q}", "code": code, "item": item, "quarter": q, "status": c["status"], "rule": c["rule"], "kind": c["kind"],
                        "form": c.get("form"), "value_mn": c.get("value_mn"), "verdict": v, "n_own": len(own), "n_sib": len(sib), "bad_own": len(bad_own), "bad_sib": len(bad_sib),
                        "own": own[:3], "sib": sib[:4]})
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(Counter(r["verdict"] for r in rep))
    g = defaultdict(list)
    for r in rep:
        g[(r["code"], r["item"], r["verdict"], "zero" if abs(r["value_mn"] or 0) < 1e-9 else "nz")].append(r)
    for (code, item, v, z), lst in sorted(g.items()):
        qs = ",".join(r["quarter"][2:] for r in sorted(lst, key=lambda r: r["quarter"]))
        print(f"{code}|{item:>2} {v:<18} {z:<4} n={len(lst):>2} {lst[0]['rule']}|{lst[0]['kind']}|{lst[0]['form']}  {qs}")


if __name__ == "__main__":
    main()
