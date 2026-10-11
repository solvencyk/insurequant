#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), steps 1+2: isolated mismatches in otherwise reproduced mappings.

Stage B calibration evidence = for every (concept, form-group) the list of (pdf quarter, period, column, kind, ok, observed, anchor)
against the DART/owner master.  A mapping that reproduces the master in nearly every quarter but fails in 1-2 of them points at a
single master cell (or a comparative restatement) rather than at a wrong mapping.  Read-only.

Output: data/_derived/bspl_followup_20261011/isolated_mismatch.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "isolated_mismatch.json"


def main():
    res = []
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for k, v in d["calibration"].items():
            ev = v["evidence"]
            bad = [e for e in ev if not e[4]]
            if not bad or len(ev) < 6:
                continue
            ok_n = len(ev) - len(bad)
            if len(bad) <= 2 and ok_n >= 5:
                res.append({"code": d["code"], "concept": k, "status": v["status"], "n": len(ev), "bad": [
                    {"pdf_quarter": e[0], "period": e[1], "col": e[2], "kind": e[3], "observed": e[5], "master": e[6],
                     "rel": (e[5] - e[6]) / abs(e[6]) if e[6] else None} for e in bad]})
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"isolated mismatches: {len(res)}")
    for r in res:
        for b in r["bad"]:
            rel = f"{b['rel']:+.2%}" if b["rel"] is not None else "n/a"
            print(f"{r['code']} {r['concept']:<34} n={r['n']:>3} pdf {b['pdf_quarter']} -> {b['period']} col{b['col']} {b['kind']:<8} "
                  f"observed {b['observed']:>16,.2f} master {b['master']:>16,.2f} rel {rel}")


if __name__ == "__main__":
    main()
