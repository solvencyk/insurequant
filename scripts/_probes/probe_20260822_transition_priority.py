# -*- coding: utf-8 -*-
"""Read-only probe: full-PDF fitz search for the 경과조치 적용여부 table across the
priority buckets that scripts/extract_transition_applicability.py left UNKNOWN.
Dumps page number + surrounding text so a human/agent can read the O/X directly
when neither md_inbox nor the regex-based PDF fallback resolved it.

Usage: python scripts/_probes/probe_20260822_transition_priority.py KR0097:FY2024_Q4 KR0005:FY2024_Q4 ...
"""
from __future__ import annotations
import sys
import glob
import fitz

sys.stdout.reconfigure(encoding="utf-8")


def probe(code: str, period: str):
    pdfs = sorted(glob.glob(f"data/disclosure/{period}/raw/{code}_*.pdf"))
    print(f"\n===== {code} {period} =====")
    if not pdfs:
        print("NO RAW PDF FOUND")
        return
    doc = fitz.open(pdfs[-1])
    print(f"pdf={pdfs[-1]} pages={doc.page_count}")
    total_text = 0
    hit = False
    for i in range(doc.page_count):
        txt = doc[i].get_text() or ""
        total_text += len(txt.strip())
        if "적용여부" in txt or "공통적용" in txt or ("경과조치" in txt and "TFI" in txt):
            hit = True
            print(f"---- page {i+1} (1-based) ----")
            idx = txt.find("적용여부")
            if idx == -1:
                idx = txt.find("공통적용")
            print(txt[max(0, idx - 300):idx + 1200])
    print(f"total_text_chars={total_text} hit={hit}")
    if not hit:
        # report per-page text density so we can tell scanned vs just-missing-section
        densities = [(i + 1, len((doc[i].get_text() or "").strip())) for i in range(doc.page_count)]
        thin_pages = [p for p, d in densities if d < 50]
        print(f"pages_with_<50_chars={len(thin_pages)}/{doc.page_count}  sample={thin_pages[:10]}")
    doc.close()


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        code, period = arg.split(":")
        probe(code, period)
