#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c: held cells whose OTHER observations (alternative concepts of the same cell) pass rule T (read-only).

The Stage-B selector reports, for a cell nothing can load, only the finest-precision blocked observation.  A cell may have a second observation
(another label / another table form, e.g. the supervisory composite 'AC_SEC + 대출채권' next to the K-statement 'AC_SEC') whose concept is rejected on the
whole history but reproduces the master in EVERY same-fiscal-year calibration entry.  This script enumerates all observations of every held cell
(company-wise replay of Stage B up to the calibration step), applies rule T to each concept and lists the passing ones.  Nothing is written to a master.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_altconcepts.py [KR....]
Output: data/_derived/bspl_followup_20261011/altconcepts_report.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
import bspl_granularity_candidates as C  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
REINS = set(C.REINS)


def informative(e, own_q):
    return not (abs(e[5]) < 1e-9 and abs(e[6]) > 1e-9 and e[0] != own_q)


def main():
    only = set(sys.argv[1:])
    all_v, anchor, disc, meta = B.load_master()
    report = []
    for p in sorted(CAND.glob("KR*.json")):
        code = p.stem
        if only and code not in only:
            continue
        if code in REINS:
            continue                            # reinsurer branches: anchors come from audit PDFs, separate story
        cd = json.loads(p.read_text(encoding="utf-8"))
        held = [c for c in cd["candidates"] if c["status"] in ("HOLD_REJECTED_RULE", "HOLD_UNTESTED") and abs(c.get("value_mn") or 0.0) > 1e-9]
        if not held:
            continue
        an = anchor.get(code, {})
        docs, obs_by_q = {}, {}
        for q in C.QUARTERS:
            doc = B.load_tables(code, q)
            if doc is None:
                continue
            docs[q] = doc
            obs, unit_info, nts = B.observations(code, q, doc, all_v, disc, None)
            bad = set()
            for kind, (unit, how) in unit_info.items():
                if kind == "equity" or unit is None:
                    continue
                ok, det = B.table_identity(doc, kind, unit)
                if ok is False:
                    bad.add(kind)
            obs_by_q[q] = [o for o in obs if o.kind not in bad]
        # calibration evidence exactly as Stage B builds it
        calib = defaultdict(list)
        for q, obs in obs_by_q.items():
            for o in obs:
                a = an.get((o.item, o.quarter))
                if a is None:
                    continue
                calib[(o.concept, C.group_of(o))].append((o.pdf_quarter, o.quarter, o.col, o.kind, B.match(o.value_mn, o.tol_mn, a, o.col > 0), o.value_mn, a))
        for c in held:
            q, item = c["quarter"], c["item"]
            y = int(q[:4])
            obs = [o for o in obs_by_q.get(q, []) if o.item == item and o.col == 0 and o.basis in (None, "별도")]
            seen = []
            for o in obs:
                key = (o.concept, C.group_of(o))
                ev = [e for e in calib.get(key, []) if int(e[0][:4]) == y and informative(e, q)]
                if not ev:
                    continue
                bad = [e for e in ev if not e[4]]
                ye = [e for e in ev if e[1].endswith("4Q")]
                tot_bad = [e for (cc, gg), lst in calib.items() if cc[0] in (1, 2, 3) for e in lst if e[0] == q and e[1] == q and e[2] == 0 and not e[4]]
                seen.append({"rule": B.cname(o.concept), "kind": o.kind, "form": o.form, "value_mn": o.value_mn, "unit": o.unit, "page": o.page, "n_same_year": len(ev),
                             "n_bad": len(bad), "year_end_entries": len(ye), "totals_disagree": len(tot_bad), "pass_T": bool(ev) and not bad and bool(ye) and not tot_bad})
            report.append({"key": f"{code}|{item}|{q}", "held_rule": c["rule"], "held_value_mn": c["value_mn"], "held_status": c["status"], "observations": seen})
    out = [r for r in report if any(s["pass_T"] and (s["rule"] != r["held_rule"] or abs(s["value_mn"] - r["held_value_mn"]) > 1e-6) for s in r["observations"])]
    (W / "altconcepts_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(len(report), "held cells examined;", len(out), "have an ALTERNATIVE observation passing rule T")
    for r in out:
        print(f"{r['key']:<18} held {r['held_rule']} {r['held_value_mn'] / 100:,.1f}억")
        for s in r["observations"]:
            if s["pass_T"]:
                print(f"      PASS {s['rule']:<28} {s['kind']:<7} {s['form']} {s['value_mn'] / 100:>12,.1f}억 same-year {s['n_same_year']} year-end {s['year_end_entries']}")


if __name__ == "__main__":
    main()
