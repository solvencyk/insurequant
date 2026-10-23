# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import hd_lib as H
sys.stdout.reconfigure(encoding="utf-8")
for key, rel in (("O1", "data/dart/FY2023_Q1/raw/KR0009_현대해상/xml/20230515002873.xml"), ("O2", "data/dart/FY2023_Q2/raw/KR0009_현대해상/xml/20230814003156.xml")):
    L = H.lines_of(rel)
    a, b = H.section(L, r"^4\.\s*재무제표$")
    for (ta, tb) in H.all_tables(L):
        if not (a <= ta <= b):
            continue
        rows = H.table_rows(L, ta, tb)
        labs = [H.nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if any("영업이익" in x for x in labs) and any("차감전순이익" in x for x in labs):
            for r in rows:
                t = H.nspace(r["cells"][0]["text"]) if r["cells"] else ""
                if ("Ⅷ" in t or "VIII" in t or "순이익" in t or "순손익" in t) and len(t) < 40:
                    print(key, r["tr"], t, [(c["text"][:18], c["line"]) for c in r["cells"][1:]][:6])
