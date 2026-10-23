# -*- coding: utf-8 -*-
"""read-only exploration: separate 4-2 statement structure (periods, THEAD paths, unit, first rows) of the Hyundai filings"""
import re, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import hd_lib as H
sys.stdout.reconfigure(encoding="utf-8")
F = {
 "N1": "data/dart/FY2024_Q1/raw/KR0009_현대해상/20240516002153.xml",
 "N2": "data/dart/FY2024_Q2/raw/KR0009_현대해상/20240814004187.xml",
 "N3": "data/dart/FY2024_Q3/raw/KR0009_현대해상/20241114003026.xml",
 "N4": "data/dart/FY2024_Q4/raw/KR0009_현대해상_20250313001346/20250313001346.xml",
 "O1": "data/dart/FY2023_Q1/raw/KR0009_현대해상/xml/20230515002873.xml",
 "O2": "data/dart/FY2023_Q2/raw/KR0009_현대해상/xml/20230814003156.xml",
 "O3": "data/dart/FY2023_Q3/raw/KR0009_현대해상/xml/20231114002737.xml",
 "O4": "data/dart/FY2023_Q4/raw/KR0009_현대해상_20240314001515/xml/20240314001515.xml",
}
PERIOD_RE = re.compile(r"제\s*(\d+)\s*기\s*(?:(1분기|반기|3분기)\s*)?(\d{4})\.(\d{2})\.(\d{2})\s*부터\s*(\d{4})\.(\d{2})\.(\d{2})\s*까지")
for key in sys.argv[1:] or list(F):
    rel = F[key]
    L = H.lines_of(rel)
    print("=" * 110)
    print(key, rel, len(L), "lines")
    ts = H.titles(L)
    for k, t in ts:
        if re.search(r"^(4|2|3|5)(-\d)?\.\s", t) and len(t) < 60:
            print("   title L%d: %s" % (k + 1, t))
    try:
        a, b = H.section(L, r"^4-2\.\s*포괄손익계산서")
    except Exception as e:
        print("   NO 4-2 section:", e)
        continue
    print("   section 4-2: L%d..L%d" % (a + 1, b + 1))
    tab = None
    for (ta, tb) in H.all_tables(L):
        if not (a <= ta <= b):
            continue
        labs = {H.nspace(r["cells"][0]["text"]) for r in H.table_rows(L, ta, tb) if r["cells"]}
        if "보험손익" in labs and ("법인세차감전순이익" in labs or "법인세비용차감전순이익" in labs):
            tab = (ta, tb)
            break
    print("   statement table:", None if tab is None else (tab[0] + 1, tab[1] + 1))
    if tab is None:
        # show all leaf tables in the section
        for (ta, tb) in H.all_tables(L):
            if a <= ta <= b:
                rows = H.table_rows(L, ta, tb)
                print("      leaf table L%d-%d rows %d first labels %s" % (ta + 1, tb + 1, len(rows), [r["cells"][0]["text"][:14] for r in rows[:4] if r["cells"]]))
        continue
    ta, tb = tab
    for k in range(a, ta):
        m = PERIOD_RE.search(H.clean(L[k]))
        if m:
            print("   period L%d: %s" % (k + 1, H.clean(L[k])))
    print("   unit:", H.unit_above(L, ta + 1, span=200), H.unit_above(L, ta + 40, span=300))
    paths = H.header_paths(L, ta, tb)
    print("   header paths:", paths)
    rows = H.body_rows(L, ta, tb)
    for r in rows[:3]:
        print("   row L%d: %s" % (r["tr"], [(c["text"][:20], c["line"]) for c in r["cells"]]))
