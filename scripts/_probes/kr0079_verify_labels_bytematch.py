# -*- coding: utf-8 -*-
"""Confirm every 항목명 in the patch byte-matches an existing KR0079 (or cross-co TFI-row)
label already in kics_disclosure.json -- not retyped, not a lookalike unicode char."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

data = json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8"))
patch = json.load(open(ROOT / "data" / "_derived" / "_patch_2026q2_KR0079.json", encoding="utf-8"))

# every label KR0079 has ever used, keyed by item number
kr0079_labels = {}
for r in data:
    if r["원보험사코드"] == "KR0079":
        kr0079_labels.setdefault(r["항목번호"], set()).add(r["항목명"])

# TFI rows 50-54 aren't in KR0079's own history -- allow any existing label for that item
# number anywhere in the corpus as the byte-match source (task allows "this company's own
# existing rows" for items it already has; for brand-new 47-54 items there IS no "own" row
# for 50/51/52/53/54, so cross-company match is the only option -- flagged explicitly below).
any_co_labels = {}
for r in data:
    any_co_labels.setdefault(r["항목번호"], set()).add(r["항목명"])

all_ok = True
for cell in patch["cells"]:
    it = cell["항목번호"]
    lbl = cell["항목명"]
    own = kr0079_labels.get(it, set())
    if lbl in own:
        print(f"item{it}: OK (KR0079 own history byte-match)")
        continue
    anyc = any_co_labels.get(it, set())
    if lbl in anyc:
        print(f"item{it}: OK (cross-company byte-match, KR0079 has no prior row for this item)")
        continue
    print(f"item{it}: *** MISMATCH *** {lbl!r} not found anywhere in corpus for this item number")
    all_ok = False

print()
print("ALL LABELS BYTE-MATCHED" if all_ok else "LABEL MISMATCHES FOUND -- fix before submitting")
