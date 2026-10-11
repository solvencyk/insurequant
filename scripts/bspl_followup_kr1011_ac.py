#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KR1011 (IBK연금보험) item 13: the exact DART AC definition from the 8-1 K statement lines (read-only; writes a proposal JSON only).
DART AC at 2024.4Q / 2025.4Q = 상각후원가유가증권 (AC_SEC) + 상각후원가대출채권및기타금융자산 (AC_LOAN); the 8-1 'children' sum of the Stage-B concept also counts
the 상각후원가예치금 line (a deposit that DART carries in 현금및예치금), which is the 314.0 / 1,251 백만원 gap seen at the year-ends."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all  # noqa: E402

all_v, anchor, disc, meta = B.load_master()
code = "KR1011"
out = {"_note": "PROPOSAL ONLY -- not loaded.  The master definition of IBK연금 item 13 switches between 2023.4Q (DART 16,966억 = 상각후원가유가증권 only) and 2024.4Q (49,837억 = 유가증권 + 대출채권및기타금융자산): owner must fix the definition first (TODO_parser_ifrs17 열린 일 ③).", "cells": [], "year_ends": {}}
def lines(q, col):
    doc = B.load_tables(code, q)
    t = B.pick_tables(doc, "bs_full")[0]
    f = B.UNIT_FACTOR[t["unit"]]
    va = view_all(t)
    g = lambda k: (va[k][0]["vals"][col] * f if k in va and len(va[k][0]["vals"]) > col and va[k][0]["vals"][col] is not None else None)
    dep = None
    for r in t["rows"]:
        if "상각후원가예치금" in r["label"].replace(" ", ""):
            dep = r["vals"][col] * f if len(r["vals"]) > col and isinstance(r["vals"][col], (int, float)) else None
    return {"AC_SEC": g("AC_SEC"), "AC_LOAN": g("AC_LOAN"), "상각후원가예치금": dep, "page": t["page"], "unit": t["unit"], "pdf": doc["pdf"]}
for q, col in (("2025.1Q", 1), ("2025.2Q", 1), ("2025.4Q", 0), ("2026.1Q", 1)):
    l = lines(q, col)
    ye = "2024.4Q" if q != "2026.1Q" and q != "2025.4Q" else "2025.4Q"
    anc = all_v[code].get((13, ye))
    s = (l["AC_SEC"] or 0) + (l["AC_LOAN"] or 0)
    out["year_ends"][f"{q} col{col} -> {ye}"] = {"AC_SEC+AC_LOAN": round(s, 3), "master_anchor": anc, "diff": None if anc is None else round(s - anc, 3), "deposit_line": l["상각후원가예치금"]}
for q in ("2025.1Q", "2025.2Q", "2025.3Q", "2026.1Q"):
    l = lines(q, 0)
    v = (l["AC_SEC"] or 0) + (l["AC_LOAN"] or 0)
    out["cells"].append({"key": f"{code}|13|{q}", "value_mn": round(v, 6), "AC_SEC": l["AC_SEC"], "AC_LOAN": l["AC_LOAN"], "page": l["page"], "unit": l["unit"], "pdf": l["pdf"]})
Path(ROOT / "data/_derived/bspl_followup_20261011/proposed_kr1011_item13_cells.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps(out, ensure_ascii=False, indent=1))
