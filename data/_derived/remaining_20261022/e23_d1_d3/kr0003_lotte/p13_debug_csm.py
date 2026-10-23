# -*- coding: utf-8 -*-
"""debug helper (read-only): which CSM roll-forward tables does kr0003_verify.csm_tables() see in each filing?"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0003_lotte")
import kr0003_verify as V   # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
for key in ("A23", "A24", "Q3", "A24AUD"):
    rel = V.F[key]
    L = V.lines_of(rel)
    print("==", key, rel)
    # raw scan: all tables whose first body label normalises to 기초순보험계약부채
    n = 0
    for (a, b) in V.all_tables(L):
        rows = V.body_rows(L, a, b)
        labs = [V.norm_label(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if labs and labs[0] == "기초순보험계약부채":
            n += 1
            paths = V.header_paths(L, a, b)
            cap = V.caption_before(L, a)
            title = V.section_title_above(L, a + 1)
            print(f"  table L{a + 1}-{b + 1} first label ok; header paths {paths}; caption {cap}; title {title}")
    print("  tables with first label 기초순보험계약부채:", n)
    ts = V.csm_tables(rel)
    print("  csm_tables():", [(t['a'] + 1, t['cap'], t['gubun'], t['title'], t['col']) for t in ts])
