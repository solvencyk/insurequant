# -*- coding: utf-8 -*-
"""Tighter re-classification of probe2: use the SAME heading regex the production
extractor uses (_HEADING_RISK_RE = r"(금리|주식|부동산|외환|자산집중)\s*위험액?\s*현황")
instead of a loose substring match, to avoid false "header present" hits from
unrelated mentions (e.g. a correlation-coefficient matrix that lists "금리위험"
as a row label without the actual "N) 금리위험액현황" detail table existing).

Read-only. No writes to kics_disclosure.json.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_market_subitems_to_disclosure import extract_mkt_subs, _HEADING_RISK_RE, _HEADING_RISK_MAP  # noqa: E402

QUARTER = "2026.2Q"
MD_DIR = REPO / "md_inbox" / "FY2026_Q2"

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

header_absent = {}
header_present_but_unextracted = {}

for code, items in sorted(by_code_item.items()):
    name = names.get(code, code)
    matches = list(MD_DIR.glob(f"{code}_*.md"))
    if not matches:
        continue
    text = matches[0].read_text(encoding="utf-8")
    # collapse markdown table pipes/spaces the same way heading-context scan sees it
    present_risk_items = {_HEADING_RISK_MAP[m.group(1)] for m in _HEADING_RISK_RE.finditer(text)}
    subs = extract_mkt_subs(text)
    for i in (36, 37, 38, 39, 40):
        rec = items.get(i)
        if rec is None:
            continue
        val_str = str(rec.get("값", "")).strip()
        if val_str in ("", "-"):
            continue
        if i in subs:
            continue
        bucket = header_present_but_unextracted if i in present_risk_items else header_absent
        bucket.setdefault((code, name), []).append((i, val_str))

print(f"[A] heading-regex ABSENT (docling-window drop, KR0069-class): {sum(len(v) for v in header_absent.values())} cells, {len(header_absent)} companies")
for (code, name), lst in sorted(header_absent.items()):
    items_str = ",".join(f"item{i}={v}" for i, v in lst)
    print(f"  {code} {name:<16} {items_str}")

print(f"\n[B] heading-regex PRESENT but extractor still can't pull value (extractor-logic gap, NOT a window drop): {sum(len(v) for v in header_present_but_unextracted.values())} cells, {len(header_present_but_unextracted)} companies")
for (code, name), lst in sorted(header_present_but_unextracted.items()):
    items_str = ",".join(f"item{i}={v}" for i, v in lst)
    print(f"  {code} {name:<16} {items_str}")
