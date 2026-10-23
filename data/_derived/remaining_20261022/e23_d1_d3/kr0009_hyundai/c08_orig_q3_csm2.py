# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import hd_lib as H
sys.stdout.reconfigure(encoding="utf-8")
rel = "data/dart/FY2023_Q3/raw/KR0009_현대해상/xml/20231114002737.xml"
L = H.lines_of(rel)
a, b = H.section(L, r"^5\.\s*재무제표 주석")
print("section", a + 1, b + 1)
n = 0
for (ta, tb) in H.all_tables(L):
    if not (a <= ta <= b):
        continue
    blob = H.nspace(" ".join(L[ta:min(tb, ta + 60)]))
    if "보험계약마진" in blob and ("기초" in blob) and "최선추정" in blob:
        rows = H.table_rows(L, ta, tb)
        labs = [H.nspace(r["cells"][0]["text"])[:22] for r in rows if r["cells"]]
        print("table L%d-L%d rows %d header %s" % (ta + 1, tb + 1, len(rows), [c["text"][:14] for c in rows[0]["cells"]]), labs[:14])
        n += 1
        if n >= 8:
            break
