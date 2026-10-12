# -*- coding: utf-8 -*-
"""a1b: more regulation pages (3.나 기본자본요건 / 3.다 보완자본요건 / 잔존만기 체감). Read-only."""
import fitz
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
PDF = ROOT + "/research/新지급여력제도(K-ICS) 해설서.pdf"
OUT = ROOT + "/data/_derived/capsec_audit_20261012/a1b_reg_pages_more.txt"
doc = fitz.open(PDF)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for p in (109, 110, 111):
        f.write("\n===== PDF_PAGE %d =====\n%s" % (p, doc[p - 1].get_text("text")))
print("ok")
