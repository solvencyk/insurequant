#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5b: prior-year-end bridge between interim K 8-1 lines and the audited year-end statement.

An interim 8-1 K-section prints [current, prior year-end]; the prior-year-end column of a filing of year D+1 is the audited balance of
year-end D, so the SAME line can be compared with the audited statement of D.  For every company / interim K line of interest it reports,
per year-end D:
    interim value (c1 of each interim filing of year D+1)   vs   audited value of the same canonical label at D
                                                              and   audited lines whose VALUE equals the interim value (label bridge)
A concept whose prior-year-end values equal the audited line in every available year-end has the same definition in both documents ->
the interim cells of that line are consistent with the audited (anchored) year-end cells of the master.  Read-only.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_bridge.py KR1101 24 [10 13 ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all, canon, col  # noqa: E402

QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
ITEM_CANON = {10: ("현금및현금성자산", "현금및예치금"), 13: ("AC_FA", "AC_SEC"), 24: ("기타부채",), 11: ("FVPL",), 12: ("FVOCI",), 14: ("재보험계약자산",), 15: ("유형자산",)}


def tables_k(doc):
    out = []
    for t in B.pick_tables(doc, "bs_full"):
        out.append(t)
    return out


def rows_by_label(t, ci):
    f = B.UNIT_FACTOR.get(t.get("unit"))
    res = []
    for r in t["rows"]:
        if len(r["vals"]) <= ci or r["dash"][ci] and False:
            continue
        v = 0.0 if r["dash"][ci] else r["vals"][ci]
        if v is None:
            continue
        res.append((r["label"], canon(r["label"], "bs"), v * f if f else None))
    return res


def main():
    code = sys.argv[1]
    items = [int(x) for x in sys.argv[2:]]
    all_v, anchor, disc, meta = B.load_master()
    mv = all_v.get(code, {})
    audits = {}                                   # year-end D -> list of (label, canon, value_mn) of the audited statement (own, c0)
    for q in QS:
        if not q.endswith("4Q"):
            continue
        doc = B.load_tables(code, q)
        if not doc:
            continue
        for t in doc["tables"]:
            if t["kind"] == "bs_full" and t.get("src") == "audit":
                audits[q] = rows_by_label(t, 0)
                audits[q + "_prior"] = rows_by_label(t, 1)
                break
    for item in items:
        want = ITEM_CANON.get(item, ())
        print(f"\n===== {code} item {item}: master series " + " ".join(f"{q[2:]}={mv.get((item, q), '-')!s:.12}" for q in QS))
        for q in QS:
            doc = B.load_tables(code, q)
            if not doc:
                continue
            for t in tables_k(doc):
                if B.table_form(t) != "K" or t.get("src") == "audit" and q.endswith("4Q"):
                    continue
                f = B.UNIT_FACTOR.get(t.get("unit"))
                if f is None or not B._has_cols(t, 2):
                    continue
                D = B.prev_year_end(q)
                for lab, cn, v in rows_by_label(t, 1):
                    if cn not in want or v is None:
                        continue
                    aud = audits.get(D, [])
                    same = [(l, round(x, 3)) for l, c2, x in aud if c2 == cn and x is not None]
                    eq = [(l, round(x, 3)) for l, c2, x in aud if x is not None and abs(x - v) <= max(0.0015 * abs(v), 2 * B.UNIT_PREC.get(t.get("unit"), 0.5), 0.01) and abs(x) > 1e-6]
                    print(f"  {q} 8-1 p{t['page']} [{t.get('unit')}] prior-year-end({D}) '{lab}' = {v:,.3f} | audited same-canon {same} | audited value-match {eq[:3]}")
                break


if __name__ == "__main__":
    main()
