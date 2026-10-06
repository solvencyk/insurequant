"""Trace what fill_period_to_disclosure actually sees for KR0032.

Calls extract_kics_detail_rows on the MD and replays match_baseline_value_or_zero
for the item4-13 baseline labels, printing the table pairs it matched against.
"""
import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from solvency.parser.kics_baseline_match import match_baseline_value_or_zero  # noqa: E402
from solvency.parser.kics_disclosure_parser import (  # noqa: E402
    build_label_lookups,
    extract_kics_detail_rows,
    normalise_label,
    core_words,
)

CASES = [
    ("2023.2Q", "md_inbox/FY2023_Q2/KR0032_NH농협손해보험_amended.md"),
    ("2023.3Q", "md_inbox/FY2023_Q3/KR0032_NH농협손해보험_amended.md"),
    ("2024.4Q", "md_inbox/FY2024_Q4/KR0032_NH농협손해보험.md"),
    ("2023.1Q", "md_inbox/FY2023_Q1/KR0032_NH농협손해보험_amended.md"),
    ("2024.3Q", "md_inbox/FY2024_Q3/KR0032_NH농협손해보험_amended.md"),
]

BASE_LABELS = [
    (4, "Ⅰ. 건전성감독기준 재무상태표 상의 순자산"),
    (5, "1. 보통주"),
    (6, "2. 자본항목 중 보통주 이외의 자본증권"),
    (7, "3. 이익잉여금"),
    (8, "4. 자본조정"),
    (9, "5. 기타포괄손익누계액"),
    (10, "6. 비지배지분"),
    (11, "7. 조정준비금"),
]

for quarter, rel in CASES:
    path = REPO / rel
    print("=" * 96)
    print(f"### {quarter}  {rel}")
    if not path.exists():
        print("  MISSING")
        continue
    table = extract_kics_detail_rows(path.read_text(encoding="utf-8"), quarter)
    print(f"  extract_kics_detail_rows -> {len(table)} pairs")
    for lab, raw in table:
        nl = normalise_label(lab)
        cw = core_words(lab)
        print(f"    raw_label={lab!r:<58} val={raw!r:<12} norm={nl!r} core={cw!r}")
    lookup, core = build_label_lookups(table)
    print("  --- match results ---")
    for it, name in BASE_LABELS:
        v = match_baseline_value_or_zero(name, lookup, core, table)
        print(f"    item{it:>3}  base_label={name!r:<42} -> {v!r}")
