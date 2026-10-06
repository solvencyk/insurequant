# -*- coding: utf-8 -*-
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import extract_pl_backfill_disclosure as ex
import fitz

pdf = ex.find_pdf("KR0049", "2025.1Q")
print("pdf:", pdf)
doc = fitz.open(pdf)
page = doc[3]  # page4
tabs = page.find_tables()
print("n_tables:", len(tabs.tables))
for tab in tabs.tables:
    rows = tab.extract()
    print("rows:", len(rows), "cols:", len(rows[0]) if rows else 0)
    idx_cur = ex._find_idx_cur(rows)
    print("idx_cur:", idx_cur)
    if idx_cur is not None:
        res = ex.extract_table_rows(rows)
        print("result:", res)
