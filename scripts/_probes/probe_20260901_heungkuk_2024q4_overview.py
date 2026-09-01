# -*- coding: utf-8 -*-
"""Heungkuk 2024.4Q raw PDF is 538 pages and scan found zero 경과조치 hits --
suspicious. Check: is this really the 정기경영공시 filing? Print per-page char
count for page 1-40 (where the K-ICS section normally lives, ~11-20 in other
quarters) and search the whole doc for '지급여력비율' / 'K-ICS' / '경과조치' with
page numbers, to locate where (or whether) the content actually is."""
import io
import sys

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PDF = r"C:\Users\sangwook.cho\Desktop\insurequant\data\disclosure\FY2024_Q4\raw\KR0071_흥국생명보험.pdf"

doc = fitz.open(PDF)
print(f"pages={doc.page_count}")

print("\n-- page 1-3 text (first 400 chars each) --")
for i in range(min(3, doc.page_count)):
    t = doc[i].get_text()
    print(f"p{i+1} chars={len(t)}: {t[:400]!r}")

print("\n-- pages 1-45 char density --")
for i in range(min(45, doc.page_count)):
    t = doc[i].get_text()
    print(f"p{i+1:>3} chars={len(t):>5}")

for kw in ("지급여력비율", "K-ICS", "경과조치", "기타요구자본", "장수위험"):
    hits = [i + 1 for i in range(doc.page_count) if kw in doc[i].get_text()]
    print(f"\nkeyword {kw!r}: {len(hits)} pages -> {hits[:30]}")

doc.close()
