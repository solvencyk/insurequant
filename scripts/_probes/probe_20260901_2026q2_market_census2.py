# -*- coding: utf-8 -*-
"""Follow-up to probe_20260901_2026q2_market_census.py: for every MD_GAP hit
(master has item, current-MD extract_mkt_subs() didn't produce it), classify
whether the section HEADER is structurally present anywhere in the current MD
text at all (normalized substring search for "<risk>위험액" + "현황").

- header ABSENT  -> docling window dropped the whole section (KR0069-class: same
  failure mode the user asked to census).
- header PRESENT -> the section survived into the MD but extract_mkt_subs()
  still can't pull a value out of it (a DIFFERENT, extractor-logic failure mode,
  not a docling-window drop).

Read-only. No writes to kics_disclosure.json.
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_market_subitems_to_disclosure import extract_mkt_subs, _norm  # noqa: E402

QUARTER = "2026.2Q"
MD_DIR = REPO / "md_inbox" / "FY2026_Q2"

RISK_KW = {36: "금리위험", 37: "주식위험", 38: "부동산위험", 39: "외환위험", 40: "자산집중위험"}

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
by_code_item = {}
names = {}
for r in rows:
    if r["공시분기"] != QUARTER:
        continue
    code = r["원보험사코드"]
    names[code] = r.get("원수사명", code)
    try:
        it = int(r["항목번호"])
    except (TypeError, ValueError):
        continue
    by_code_item.setdefault(code, {})[it] = r

header_absent = []  # (code, name, item, master_val)
header_present_but_unextracted = []  # (code, name, item, master_val)

for code, items in sorted(by_code_item.items()):
    name = names.get(code, code)
    matches = list(MD_DIR.glob(f"{code}_*.md"))
    if not matches:
        continue
    text = matches[0].read_text(encoding="utf-8")
    ntext = _norm(text)  # strips whitespace/punct/roman numerals same as extractor
    subs = extract_mkt_subs(text)
    for i in (36, 37, 38, 39, 40):
        rec = items.get(i)
        if rec is None:
            continue
        val_str = str(rec.get("값", "")).strip()
        if val_str in ("", "-"):
            continue
        if i in subs:
            continue  # extractor already reproduces this item -> not a gap
        kw = _norm(RISK_KW[i])
        present = kw in ntext
        if present:
            header_present_but_unextracted.append((code, name, i, val_str))
        else:
            header_absent.append((code, name, i, val_str))

print(f"header ABSENT from current MD (docling-window drop, KR0069-class): {len(header_absent)} cells")
by_company_absent = {}
for code, name, i, v in header_absent:
    by_company_absent.setdefault((code, name), []).append((i, v))
for (code, name), lst in sorted(by_company_absent.items()):
    items_str = ",".join(f"item{i}={v}" for i, v in lst)
    print(f"  {code} {name:<16} {items_str}")

print(f"\nheader PRESENT but extractor still can't pull a value (different failure mode): {len(header_present_but_unextracted)} cells")
by_company_present = {}
for code, name, i, v in header_present_but_unextracted:
    by_company_present.setdefault((code, name), []).append((i, v))
for (code, name), lst in sorted(by_company_present.items()):
    items_str = ",".join(f"item{i}={v}" for i, v in lst)
    print(f"  {code} {name:<16} {items_str}")

print(f"\nSUMMARY: companies with >=1 header-ABSENT cell: {len(by_company_absent)}")
print(f"SUMMARY: companies with >=1 header-PRESENT-but-unextracted cell: {len(by_company_present)}")
