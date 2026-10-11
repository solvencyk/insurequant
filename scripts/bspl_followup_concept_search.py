#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c: exact line-subset concept search for held K-statement cells (read-only).

Stage B maps an item to FIXED label families (AC_SEC, AC_CHILDREN ...).  A master (DART) value is often a SUM OF PRINTED STATEMENT LINES that the fixed
families miss (IBK연금 item 13 = 상각후원가유가증권 + 상각후원가대출채권및기타금융자산, the family sum also took the 상각후원가예치금 deposit line).  For every
(company, item) with held bs_full K cells this script looks, per fiscal year Y, for label subsets (size <= 3, nonzero lines of the check) of the statement
that reproduce the master's DART/owner anchor EXACTLY (unit precision, no comparative slack) at the year-end checks of that fiscal year:
    opening: the prior-year-end column (col 1) of every interim filing of year Y against the anchor of (Y-1).4Q
    closing: the current column (col 0) of the year-end filing of year Y against the anchor of Y.4Q
A label set is valid for year Y when it matches EVERY available check of that year (>= 1) and no other minimal set does.  A held cell of that year whose
own filing prints all labels and whose own prior-year-end column matches (L1) is reported with the sum of the labels in its current column.
Output: data/_derived/bspl_followup_20261011/concept_search_report.json / concept_search_cells.json (manual schema).
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
REINS = {"KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107", "KR1108"}
ASSET_ITEMS = {10, 11, 12, 13, 14, 15}
LIAB_ITEMS = {20, 21, 22, 23, 24}
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
TAIL = " (inbox/parser/20261011T0900Z bspl follow-up, step 5c concept search)"


def norm(label: str) -> str:
    s = re.sub(r"\s+", "", label)
    s = re.sub(r"^[\dⅠ-ⅩIVXⅩⅪⅫ]+[.)]?", "", s)          # numbering / roman prefix
    s = s.replace("Ⅴ", "").replace("XⅣ.", "")
    return s


def side_rows(table, side):
    """rows of the asset side (before 자산총계) or liability side (between 자산총계 and 부채총계) with their raw values."""
    rows = table["rows"]
    labs = [norm(r["label"]) for r in rows]
    try:
        ia = labs.index("자산총계")
    except ValueError:
        return []
    try:
        il = labs.index("부채총계")
    except ValueError:
        il = len(rows)
    return rows[:ia] if side == "A" else rows[ia + 1:il]


def val(r, col, f):
    if len(r["vals"]) <= col:
        return None
    if r.get("unsure") and len(r["unsure"]) > col and r["unsure"][col]:
        return None
    if r["dash"][col]:
        return 0.0
    v = r["vals"][col]
    return None if v is None else v * f


def subsets(rows, col, f, target, tol, kmax=3):
    """minimal label subsets (by normalised label tuple) of nonzero rows that sum to target within tol."""
    cand = []
    for r in rows:
        v = val(r, col, f)
        if v is None or abs(v) < 1e-9:
            continue
        cand.append((norm(r["label"]), v))
    # label duplicates (same normalised label twice in a side): keep first occurrence only
    seen, uniq = set(), []
    for lab, v in cand:
        if lab in seen:
            continue
        seen.add(lab)
        uniq.append((lab, v))
    out = []
    for k in range(1, kmax + 1):
        for comb in itertools.combinations(uniq, k):
            if abs(sum(v for _, v in comb) - target) <= tol:
                out.append(tuple(sorted(l for l, _ in comb)))
    return out


def main():
    only = set(sys.argv[1:])
    all_v, anchor, disc, meta = B.load_master()
    report, cells = [], []
    for p in sorted(CAND.glob("KR*.json")):
        code = p.stem
        if code in REINS or (only and code not in only):
            continue
        cd = json.loads(p.read_text(encoding="utf-8"))
        held = [c for c in cd["candidates"] if c["status"] in ("HOLD_REJECTED_RULE", "HOLD_UNTESTED") and c["kind"] == "bs_full" and c.get("form") == "K"
                and c["item"] in (ASSET_ITEMS | LIAB_ITEMS) and abs(c.get("value_mn") or 0.0) > 1e-9]
        if not held:
            continue
        tabs = {}
        for q in QS:
            doc = B.load_tables(code, q)
            if doc is None:
                continue
            ts = [t for t in B.pick_tables(doc, "bs_full") if B.table_form(t) == "K"]
            if ts:
                tabs[q] = (doc, ts[0])
        for item in sorted({c["item"] for c in held}):
            side = "A" if item in ASSET_ITEMS else "L"
            anc = {q: v for (it, q), v in anchor.get(code, {}).items() if it == item and q.endswith("4Q")}
            # checks per fiscal year
            by_year = defaultdict(list)       # Y -> [(filing q, col, D, anchor, tol, unit)]
            for q, (doc, t) in tabs.items():
                f = B.UNIT_FACTOR.get(t.get("unit"))
                if f is None:
                    continue
                y = int(q[:4])
                tol = max(B.UNIT_TOL[t["unit"]] * 0.5, 0.02)
                if q.endswith("4Q") and q in anc:
                    by_year[y].append((q, 0, q, anc[q], tol, t))
                D = B.prev_year_end(q)
                if D in anc and B._has_cols(t, 2):
                    by_year[y].append((q, 1, D, anc[D], tol, t))
            for y, checks in sorted(by_year.items()):
                sets_per_check = []
                for q, col, D, a, tol, t in checks:
                    f = B.UNIT_FACTOR[t["unit"]]
                    ss = set(subsets(side_rows(t, side), col, f, a, tol))
                    sets_per_check.append((q, col, D, a, ss))
                valid = None
                for q, col, D, a, ss in sets_per_check:
                    valid = ss if valid is None else (valid & ss)
                valid = valid or set()
                # drop non-minimal supersets
                minimal = {s for s in valid if not any(set(o) < set(s) for o in valid)}
                held_y = [c for c in held if c["item"] == item and int(c["quarter"][:4]) == y]
                rec = {"code": code, "item": item, "fiscal_year": y, "checks": [(q, col, D, round(a, 3), len(ss)) for q, col, D, a, ss in sets_per_check],
                       "valid_label_sets": [list(s) for s in sorted(minimal)], "held_cells": [c["quarter"] for c in held_y]}
                report.append(rec)
                if len(minimal) != 1 or not held_y:
                    continue
                (labels,) = minimal
                for c in held_y:
                    q = c["quarter"]
                    if q not in tabs:
                        continue
                    doc, t = tabs[q]
                    f = B.UNIT_FACTOR[t["unit"]]
                    rows = {norm(r["label"]): r for r in side_rows(t, side)}
                    if any(l not in rows for l in labels):
                        continue
                    # L1: this filing's own prior-year-end column must match the anchor with the same labels
                    D = B.prev_year_end(q)
                    own_ok = None
                    if not q.endswith("4Q") and B._has_cols(t, 2) and D in anc:
                        s1 = sum(val(rows[l], 1, f) or 0.0 for l in labels)
                        own_ok = abs(s1 - anc[D]) <= max(B.UNIT_TOL[t["unit"]] * 0.5, 0.02)
                    s0 = sum(val(rows[l], 0, f) or 0.0 for l in labels)
                    rec2 = {"key": f"{code}|{item}|{q}", "labels": list(labels), "value_mn": s0, "own_prior_column_ok": own_ok, "held_rule": c["rule"], "held_value_mn": c["value_mn"]}
                    rec.setdefault("cells", []).append(rec2)
    # second pass printing
    (W / "concept_search_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    n_cells = 0
    for r in report:
        if r.get("cells"):
            print(f"{r['code']}|{r['item']} FY{r['fiscal_year']} labels={r['valid_label_sets']} checks={r['checks']}")
            for c in r["cells"]:
                n_cells += 1
                print(f"     {c['key']:<18} value {c['value_mn'] / 100:>12,.1f}억 own_prior_ok={c['own_prior_column_ok']} (held rule {c['held_rule']} {c['held_value_mn'] / 100:,.1f}억)")
    print(len(report), "(company,item,FY) checked;", n_cells, "held cells with a unique exact label set")


if __name__ == "__main__":
    main()
