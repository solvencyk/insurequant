# -*- coding: utf-8 -*-
"""a1: print selected PDF pages of the K-ICS 해설서 text dump (read-only). Audit 20261012.

Re-extracts text directly from research/*.pdf with fitz (does not rely on the earlier dump)
so the regulation check is independent of the earlier memo's transcription.
"""
import sys
import fitz  # PyMuPDF

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
PDF = ROOT + "/research/新지급여력제도(K-ICS) 해설서.pdf"
OUT = ROOT + "/data/_derived/capsec_audit_20261012/a1_reg_pages.txt"

PAGES = [7, 8, 13, 14, 98, 99, 100, 101, 102, 103, 106, 107, 108, 109, 112, 288, 289, 298]

doc = fitz.open(PDF)
print("pages", doc.page_count)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for p in PAGES:
        if p > doc.page_count:
            continue
        t = doc[p - 1].get_text("text")
        f.write("\n===== PDF_PAGE %d =====\n%s" % (p, t))
print("wrote", OUT)
