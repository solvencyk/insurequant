# -*- coding: utf-8 -*-
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.stdout = __import__("io").TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import extract_pl_backfill_disclosure as ex
import fitz

pdf = ex.find_pdf("KR0049", "2025.1Q")
doc = fitz.open(pdf)
for i in range(min(40, doc.page_count)):
    page = doc[i]
    t = page.get_text()
    if "포괄손익계산서" not in t:  # 포괄손익계산서
        continue
    hits = sum(1 for lab in ex.CORE_LABELS if lab in t)
    print(f"page {i+1}: has title, core label hits={hits}")
    if hits < 3:
        continue
    tabs = page.find_tables()
    print(f"  n_tables={len(tabs.tables)}")
    for ti, tab in enumerate(tabs.tables):
        rows = tab.extract()
        res = ex.extract_table_rows(rows)
        if res is None:
            print(f"  table{ti}: rows={len(rows)} -> extract_table_rows returned None")
            continue
        found, warnings = res
        print(f"  table{ti}: rows={len(rows)} -> found items={sorted(found.keys())} warnings={warnings}")
