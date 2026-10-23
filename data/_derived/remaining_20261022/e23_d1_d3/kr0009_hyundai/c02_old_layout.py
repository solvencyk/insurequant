# -*- coding: utf-8 -*-
"""read-only exploration: income statement of the ORIGINAL 2023.1Q / 2023.2Q filings (section 4. 재무제표, old layout)"""
import re, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import hd_lib as H
sys.stdout.reconfigure(encoding="utf-8")
F = {"O1": "data/dart/FY2023_Q1/raw/KR0009_현대해상/xml/20230515002873.xml", "O2": "data/dart/FY2023_Q2/raw/KR0009_현대해상/xml/20230814003156.xml"}
for key, rel in F.items():
    L = H.lines_of(rel)
    a, b = H.section(L, r"^4\.\s*재무제표$")
    print("=" * 100)
    print(key, rel, "section 4: L%d..L%d" % (a + 1, b + 1))
    for (ta, tb) in H.all_tables(L):
        if not (a <= ta <= b):
            continue
        rows = H.table_rows(L, ta, tb)
        labs = [H.nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if any("법인세" in x and "차감전" in x for x in labs) and any("영업이익" in x for x in labs):
            print(" income statement table L%d-L%d rows %d" % (ta + 1, tb + 1, len(rows)))
            print(" unit:", H.unit_above(L, ta + 1, span=300))
            print(" header paths:", H.header_paths(L, ta, tb))
            for r in rows[:14]:
                print("   L%d: %s" % (r["tr"], [(c["text"][:22], c["line"]) for c in r["cells"]]))
            for r in rows:
                t = H.nspace(r["cells"][0]["text"]) if r["cells"] else ""
                if re.search(r"보험서비스결과|기타사업비용|투자서비스결과|영업이익|영업외손익|법인세비용차감전|법인세비용|분기순이익|반기순이익|총포괄|기타포괄손익", t) and len(t) < 40:
                    print("   >>", r["tr"], [(c["text"][:16], c["line"]) for c in r["cells"]])
