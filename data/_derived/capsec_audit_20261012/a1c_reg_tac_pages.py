# -*- coding: utf-8 -*-
"""a1c: regulation pages on the 선택적용 경과조치 (자본감소분 = TAC) to see which tier the added amount goes to
and whether it is inside the 보완자본 한도 계산. Read-only."""
import fitz

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
PDF = ROOT + "/research/新지급여력제도(K-ICS) 해설서.pdf"
OUT = ROOT + "/data/_derived/capsec_audit_20261012/a1c_reg_tac_pages.txt"
doc = fitz.open(PDF)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for p in (289, 290, 291, 292):
        f.write("\n===== PDF_PAGE %d =====\n%s" % (p, doc[p - 1].get_text("text")))
print("ok")
