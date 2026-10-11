#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all  # noqa: E402
all_v, anchor, disc, meta = B.load_master()
for q in ("2026.2Q",):
    doc = B.load_tables("KR1011", q)
    for t in B.pick_tables(doc, "bs_full")[:2]:
        f = B.UNIT_FACTOR[t["unit"]]
        va = view_all(t)
        g = lambda k: va[k][0]["vals"][0] * f if k in va else None
        dep = [r["vals"][0] * f for r in t["rows"] if "상각후원가예치금" in r["label"].replace(" ", "")]
        print(q, "page", t["page"], "src", t.get("src"), "AC_SEC", g("AC_SEC"), "AC_LOAN", g("AC_LOAN"), "dep", dep, "sum2", (g("AC_SEC") or 0) + (g("AC_LOAN") or 0), "master", all_v["KR1011"].get((13, q)))
