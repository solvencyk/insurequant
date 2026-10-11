#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c: per (company, item, rule) reason for every remaining held BS cell (read-only).

Reads the Stage-B candidate files (status HOLD_REJECTED_RULE / HOLD_UNTESTED / HOLD_TRIO / HOLD_PARTIAL_GROUP / HOLD_QOQ), the same-table / chain / year-rule
reports and writes data/_derived/bspl_followup_20261011/hold_reasons_5c.json (+ hold_reasons_5c.txt).  The automatic category is a first pass; a hand
override table (OVERRIDE) gives the final wording where the automatic one is too coarse.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
HOLDS = {"HOLD_REJECTED_RULE", "HOLD_UNTESTED", "HOLD_TRIO", "HOLD_PARTIAL_GROUP", "HOLD_QOQ"}
ITEMS = {1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "AOCI", 10: "현금", 11: "FVPL", 12: "FVOCI", 13: "AC금융자산", 14: "재보험계약자산", 15: "유형자산",
         20: "보험계약부채", 21: "재보험계약부채", 22: "투자계약부채", 23: "차입부채", 24: "기타부채", 30: "자본금", 31: "이익잉여금"}

# hand override: (code, item) -> (category, wording)   (the automatic text is kept as `evidence`)
OVERRIDE = {}


def fmt(v):
    return f"{v:,.1f}"


def main():
    rep_year = {r["key"]: r for r in json.loads((W / "yearrule_report.json").read_text(encoding="utf-8"))}
    groups = defaultdict(list)
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d["candidates"]:
            if c["status"] in HOLDS:
                groups[(d["code"], c["item"], c["rule"], c["kind"], c.get("form"), c["status"])].append((d, c))
    out = []
    for (code, item, rule, kind, form, status), lst in sorted(groups.items()):
        d = lst[0][0]
        cells = sorted((c for _, c in lst), key=lambda c: c["quarter"])
        zero = [c for c in cells if abs(c.get("value_mn") or 0.0) < 1e-9]
        nz = [c for c in cells if c not in zero]
        ck = f"{rule}|{'K' if form == 'K' else 'S'}"       # calibration group: K statement lines vs everything else (S)
        ev = d["calibration"].get(ck, {}).get("evidence", [])
        bad = [e for e in ev if not e[4]]
        yearends = [e for e in ev if e[1].endswith("4Q")]
        bad_ye = [e for e in yearends if not e[4]]
        nonzero_anchor_zero_obs = [e for e in bad if abs(e[5]) < 1e-9 and abs(e[6]) > 1e-9]
        vy = defaultdict(int)
        for c in cells:
            vy[rep_year.get(f"{code}|{item}|{c['quarter']}", {}).get("verdict", "?")] += 1
        if status == "HOLD_UNTESTED":
            cat = "UNTESTED_NO_ANCHOR"
        elif status == "HOLD_TRIO":
            cat = "DEFINITION_OWNER_DECISION"
        elif status == "HOLD_PARTIAL_GROUP":
            cat = "PARTIAL_GROUP"
        elif cells and len(zero) == len(cells) and nonzero_anchor_zero_obs and len(nonzero_anchor_zero_obs) >= max(1, len(bad) // 2):
            cat = "ZERO_LINE_VS_NONZERO_AUDITED"
        elif form == "S" and kind == "sum_bs" and ev and len(bad_ye) >= max(1, len(yearends)) * 0.5:
            cat = "S_FORM_LINE_NOT_THE_K_LINE"
        elif vy.get("OWN_FAIL", 0) >= len(cells) * 0.6:
            cat = "OWN_FILING_DEFINITION_DIFFERS"
        elif vy.get("NO_FY_EVIDENCE", 0) + vy.get("SIBLING_FAIL", 0) + vy.get("SIBLING_OK", 0) >= len(cells) * 0.6:
            cat = "NO_OWN_COMPARATIVE_OR_FY2023"
        else:
            cat = "MIXED"
        sample_bad = "; ".join(f"{e[0]}/{e[1]}/col{e[2]}: {fmt(e[5])} vs {fmt(e[6])}" for e in bad[:3])
        rec = {"key": f"{code}|{item}", "name": d.get("name"), "item": item, "item_name": ITEMS.get(item, str(item)), "rule": rule, "kind": kind, "form": form, "status": status,
               "n_cells": len(cells), "n_zero": len(zero), "quarters": [c["quarter"] for c in cells], "values_mn": {c["quarter"]: round(c["value_mn"], 1) for c in cells},
               "category": cat, "n_evidence": len(ev), "n_bad": len(bad), "year_end_bad": len(bad_ye), "year_end_total": len(yearends), "yearrule": dict(vy), "sample_bad": sample_bad}
        if (code, item) in OVERRIDE:
            rec["category"], rec["text"] = OVERRIDE[(code, item)]
        out.append(rec)
    (W / "hold_reasons_5c.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    lines = []
    for r in out:
        lines.append(f"{r['key']:<12} {r['name'][:10]:<10} {r['item_name']:<8} {r['status'][5:]:<13} {r['category']:<30} n={r['n_cells']:>2} (zero {r['n_zero']:>2}) {r['quarters'][0][2:]}..{r['quarters'][-1][2:]} "
                     f"ev {r['n_evidence']:>2} bad {r['n_bad']:>2} ye {r['year_end_bad']}/{r['year_end_total']} yr={r['yearrule']}  | {r['sample_bad'][:150]}")
    txt = "\n".join(lines)
    (W / "hold_reasons_5c.txt").write_text(txt + "\n", encoding="utf-8", newline="\n")
    print(txt)
    from collections import Counter
    print(Counter(r["category"] for r in out), sum(r["n_cells"] for r in out), "held cells in", len(out), "groups")


if __name__ == "__main__":
    main()
