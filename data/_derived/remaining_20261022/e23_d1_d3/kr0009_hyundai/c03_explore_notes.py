# -*- coding: utf-8 -*-
"""read-only exploration: separate-notes tables with a 보험계약마진상각 row (item 4) and the CSM roll-forward tables of the Hyundai FY2024 filings"""
import re, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import hd_lib as H
sys.stdout.reconfigure(encoding="utf-8")
F = {
 "N1": "data/dart/FY2024_Q1/raw/KR0009_현대해상/20240516002153.xml",
 "N2": "data/dart/FY2024_Q2/raw/KR0009_현대해상/20240814004187.xml",
 "N3": "data/dart/FY2024_Q3/raw/KR0009_현대해상/20241114003026.xml",
 "N4": "data/dart/FY2024_Q4/raw/KR0009_현대해상_20250313001346/20250313001346.xml",
}
def caption(L, ta, maxback=60):
    out = []
    for k in range(ta - 1, max(ta - maxback, 0), -1):
        t = H.clean(L[k])
        if t:
            out.append((k + 1, t))
        if len(out) >= 4:
            break
    return out
for key in sys.argv[1:] or list(F):
    L = H.lines_of(F[key])
    a, b = H.section(L, r"^5\.\s*재무제표 주석")
    print("=" * 110)
    print(key, "separate notes L%d..L%d" % (a + 1, b + 1))
    for (ta, tb) in H.all_tables(L):
        if not (a <= ta <= b):
            continue
        rows = H.table_rows(L, ta, tb)
        labs = [H.nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if "보험계약마진상각" in labs:
            hdr = [c["text"] for c in rows[0]["cells"]]
            print(" ITEM4 TABLE L%d-L%d rows %d header %s" % (ta + 1, tb + 1, len(rows), hdr))
            print("    caption:", caption(L, ta))
            print("    unit:", H.unit_above(L, ta + 1, span=200))
            for r in rows:
                if r["cells"] and H.nspace(r["cells"][0]["text"]) in ("보험계약마진상각", "보험수익", "구분"):
                    print("      L%d: %s" % (r["tr"], [(c["text"][:14], c["line"]) for c in r["cells"]]))
