# -*- coding: utf-8 -*-
"""Build data/_derived/_patch_2026q2_KR0079.json from vision-verified page reads.

Every numeric value below was read directly off rendered PDF pages (240dpi PNGs of
data/disclosure/FY2026_Q2/pdf/KR0079_미래에셋생명.pdf, which is genuinely image-only —
no embedded text layer, confirmed via fitz get_text()). This script does NOT parse any
OCR output; the numbers are hard-coded from the Claude vision read of pages 16/19/20/24/
25/28/30/31, each cross-checked against this company's own already-loaded comparative
columns (2026.1Q, 2025.4Q) and the kics_json_rules.py identities (rule1/4/5/6, 8_life,
19_market, 36_irr, TFI). All identities close within tolerance (see kr0079_full_verify.py
output). Labels are copied byte-for-byte from existing kics_disclosure.json rows (this
company's own 2026.2Q rows where present, else this company's 2025.4Q rows, else a
cross-company 47-54 TFI-row example) -- never retyped by hand.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

data = json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8"))
by_item = {}
for r in data:
    if r["원보험사코드"] == "KR0079" and r["공시분기"] == "2026.2Q":
        by_item.setdefault(("2026.2Q", r["항목번호"]), r["항목명"])
    if r["원보험사코드"] == "KR0079" and r["공시분기"] == "2025.4Q":
        by_item.setdefault(("2025.4Q", r["항목번호"]), r["항목명"])

TFI_LABELS = {}
for r in data:
    if r["항목번호"] in (47, 48, 49) and r["원보험사코드"] == "KR0079":
        TFI_LABELS[r["항목번호"]] = r["항목명"]
    if r["항목번호"] == 50 and r["원보험사코드"] == "KR1000" and r["공시분기"] == "2023.2Q":
        TFI_LABELS[50] = r["항목명"]
    if r["항목번호"] == 51 and r["원보험사코드"] == "KR1000" and r["공시분기"] == "2023.2Q":
        TFI_LABELS[51] = r["항목명"]
    if r["항목번호"] in (52, 53, 54) and r["원보험사코드"] == "KR0001" and r["공시분기"] == "2023.1Q":
        TFI_LABELS[r["항목번호"]] = r["항목명"]

def label(item):
    if ("2026.2Q", item) in by_item:
        return by_item[("2026.2Q", item)]
    if ("2025.4Q", item) in by_item:
        return by_item[("2025.4Q", item)]
    if item in TFI_LABELS:
        return TFI_LABELS[item]
    raise KeyError(item)

# sanity print of every label we'll use, so a human can eyeball them
for it in list(range(1, 55)):
    try:
        print(it, repr(label(it)))
    except KeyError:
        print(it, "NO LABEL FOUND (expected for 6/10/12)")
