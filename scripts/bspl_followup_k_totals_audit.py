#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), steps 1+2: K-IFRS statement totals (8-1 K-form, printed unit) vs master totals, all
companies x quarters, current column AND the prior-year-end column.

Unlike Stage B this does not need the unit to be resolved against the master (a wrong master total used to hide the table):
the unit comes from the table caption.  Only K-form 별도 8-1 / audit statements are compared (the supervisory S-form has other totals).
Read-only.  Output: data/_derived/bspl_followup_20261011/k_totals_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all, col  # noqa: E402

OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "k_totals_audit.json"
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
CODES = sorted({p.name.split("_")[0] for p in (ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "tables").glob("KR*.json")})


def main():
    all_v, anchor, disc, meta = B.load_master()
    rows = []
    for code in CODES:
        mv = all_v.get(code, {})
        for q in QS:
            doc = B.load_tables(code, q)
            if not doc:
                continue
            for t in doc["tables"]:
                if t["kind"] != "bs_full":
                    continue
                va = view_all(t)
                if not all(k in va for k in ("자산총계", "부채총계", "자본총계")):
                    continue
                if B.table_form(t) != "K":
                    continue
                unit = t.get("unit")
                f = B.UNIT_FACTOR.get(unit)
                if f is None:
                    continue
                basis = t.get("basis")
                for ci, tq in ((0, q), (1, B.prev_year_end(q))):
                    for it, key in ((1, "자산총계"), (2, "부채총계"), (3, "자본총계")):
                        v = col(va[key][0], ci)
                        if v is None:
                            continue
                        m = mv.get((it, tq))
                        if m in (None, 0):
                            continue
                        rel = (v * f - m) / abs(m)
                        rows.append({"code": code, "pdf_quarter": q, "quarter": tq, "col": ci, "item": it, "master": m,
                                     "disclosure": round(v * f, 6), "rel": rel, "basis": basis, "page": t["page"], "unit": unit,
                                     "src": t.get("src"), "in_sidecar": f"{code}|{it}|{tq}" in {}})
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    big = [r for r in rows if abs(r["rel"]) > 0.001 and r["basis"] in (None, "별도")]
    big.sort(key=lambda r: (r["code"], r["quarter"], r["item"], r["col"]))
    print(f"K-form comparisons {len(rows)}; 별도/unknown basis > 0.1 % : {len(big)}")
    for r in big:
        print(f"{r['code']} pdf {r['pdf_quarter']} -> {r['quarter']} col{r['col']} item{r['item']} master {r['master']:>16,.2f} "
              f"disclosure {r['disclosure']:>16,.2f} rel {r['rel']:+.3%} (p{r['page']} {r['unit']} {r['basis']})")


if __name__ == "__main__":
    main()
