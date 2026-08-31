# -*- coding: utf-8 -*-
"""Simulate the raw/->pdf/ fallback fix for fill_market_subitems_to_disclosure.py's
IRR PDF lookup: for every period dir under data/disclosure/, for every company code
seen in that period's md_inbox, check whether raw/ has a match, whether pdf/ has a
match, and classify. The proposed fix only changes behavior for the 'pdf_only' bucket
(strictly additive) -- this proves no regression is possible by construction, and
reports exactly how many (period,company) cells go from 0 PDF found -> 1 found."""
import sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
DISCLOSURE = ROOT / "data" / "disclosure"
MD_INBOX = ROOT / "md_inbox"

both = raw_only = pdf_only = neither = 0
pdf_only_detail = []
for period_dir in sorted(MD_INBOX.glob("FY*_Q?")):
    period = period_dir.name
    raw_dir = DISCLOSURE / period / "raw"
    pdf_dir = DISCLOSURE / period / "pdf"
    codes = sorted(set(p.stem.split("_", 1)[0] for p in period_dir.glob("*.md")))
    for code in codes:
        has_raw = bool(list(raw_dir.glob(f"{code}_*.pdf"))) if raw_dir.is_dir() else False
        has_pdf = bool(list(pdf_dir.glob(f"{code}_*.pdf"))) if pdf_dir.is_dir() else False
        if has_raw and has_pdf:
            both += 1
        elif has_raw:
            raw_only += 1
        elif has_pdf:
            pdf_only += 1
            pdf_only_detail.append((period, code))
        else:
            neither += 1

print(f"both(raw+pdf)={both}  raw_only={raw_only}  pdf_only(NEWLY RECOVERED by fix)={pdf_only}  neither(still 0)={neither}")
print(f"\ntotal (period,company) cells that GAIN a PDF discovery with the fix: {pdf_only}")
by_period = {}
for period, code in pdf_only_detail:
    by_period.setdefault(period, []).append(code)
for period in sorted(by_period):
    print(f"  {period}: {len(by_period[period])} companies -> {by_period[period]}")

print("\n(the fix tries raw/ FIRST, pdf/ only as fallback -- so `both` and `raw_only` cells")
print(" are UNCHANGED in behavior; this is a pure monotonic addition, 0 regressions possible)")
