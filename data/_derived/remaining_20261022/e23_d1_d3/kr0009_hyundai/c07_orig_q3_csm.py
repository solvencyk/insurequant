# -*- coding: utf-8 -*-
"""read-only: CSM tables of the ORIGINAL FY2023 Q3 filing (separate notes): captions, opening / item 4 / closing of the 보험계약마진 column"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import hd_lib as H
sys.stdout.reconfigure(encoding="utf-8")
for key, rel in (("O3", "data/dart/FY2023_Q3/raw/KR0009_현대해상/xml/20231114002737.xml"), ("O1", "data/dart/FY2023_Q1/raw/KR0009_현대해상/xml/20230515002873.xml"), ("O2", "data/dart/FY2023_Q2/raw/KR0009_현대해상/xml/20230814003156.xml")):
    L = H.lines_of(rel)
    a, b = H.section(L, r"^5\.\s*재무제표 주석")
    print("=" * 100, key)
    for (ta, tb) in H.all_tables(L):
        if not (a <= ta <= b):
            continue
        blob = H.nspace(" ".join(L[ta:min(tb, ta + 140)]))
        if "보험계약마진상각" not in blob or "기초순보험계약부채" not in blob or "신계약효과" not in blob:
            continue
        rows = H.table_rows(L, ta, tb)
        hdr = next((r for r in rows if r["cells"] and H.nspace(r["cells"][0]["text"]) == "구분"), None)
        if hdr is None:
            continue
        j = [i for i, c in enumerate(hdr["cells"]) if H.nspace(c["text"]) == "보험계약마진"]
        if len(j) != 1:
            continue
        un, _ = H.unit_above(L, ta + 1, span=120)
        caps = []
        for k in range(ta - 1, max(ta - 120, 0), -1):
            t = H.clean(L[k])
            if t and not t.startswith("(단위"):
                caps.append((k + 1, t[:90]))
            if len(caps) >= 2:
                break
        out = {}
        for lab in ("기초순보험계약부채", "신계약효과", "보험계약마진을조정하는변동", "보험계약마진상각", "기말보험계약순부채", "당기말보험계약순부채", "분기말보험계약순부채", "반기말보험계약순부채"):
            for r in rows:
                if r["cells"] and H.nspace(r["cells"][0]["text"]) == lab:
                    c = r["cells"][j[0]]
                    out[lab] = (c["text"], c["line"])
                    break
        print("  table L%d-L%d unit %s caps %s" % (ta + 1, tb + 1, un, caps))
        for k, v in out.items():
            print("      ", k, v)
