# -*- coding: utf-8 -*-
"""Seed kics_disclosure.json with first-time companies (one item-1 row each).

fill_period_to_disclosure skips a company that has zero rows in the master
(no baseline of any kind). One seeded row per company unlocks the
same-quarter-partial path, and _supplement_core_baseline then templates the
remaining items 1-28, so a normal fill run absorbs the company. The seed value
is taken from the company's own MD extraction so the row is real data, not a
placeholder.

2026-06-12: KR0004 예별손해보험 (구 MG손해보험; 2026.1Q MD only), KR0080 에이아이에이생명보험
(MDs 2023.1Q~2025.4Q; text layer only up to 2024.4Q — 2025+ are scans).
Idempotent: existing (code, quarter, item) rows are left untouched.

Usage: PYTHONIOENCODING=utf-8 python scripts/seed_new_companies.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from solvency.parser.kics_disclosure_parser import (  # noqa: E402
    build_label_lookups,
    extract_kics_detail_rows,
)
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero  # noqa: E402

JSON_PATH = REPO / "kics_disclosure.json"

# (code, 원수사명, 티커, 생손보여부, seed quarter, md path)
SEEDS = [
    ("KR0004", "예별손해보험", "X", "손해보험", "2026.1Q",
     "md_inbox/FY2026_Q1/KR0004_예별손해보험.md"),
    ("KR0080", "에이아이에이생명보험", "X", "생명보험", "2023.1Q",
     "md_inbox/FY2023_Q1/KR0080_에이아이에이생명보험.md"),
]


def main() -> int:
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows}
    n_add = 0
    for code, cname, ticker, kind, quarter, md_rel in SEEDS:
        if (code, quarter, 1) in have:
            print(f"{code} {quarter}: already seeded, skip")
            continue
        md = (REPO / md_rel).read_text(encoding="utf-8")
        table = extract_kics_detail_rows(md, quarter)
        if not table:
            print(f"{code} {quarter}: extraction empty, NOT seeded")
            continue
        lookup, core = build_label_lookups(table)
        value = match_baseline_value_or_zero("지급여력금액", lookup, core, table)
        if value is None:
            print(f"{code} {quarter}: 지급여력금액 not matched, NOT seeded")
            continue
        rows.append({
            "원보험사코드": code, "원수사명": cname, "티커": ticker,
            "생손보여부": kind, "항목번호": 1, "항목명": "지급여력금액",
            "공시분기": quarter, "값": value,
        })
        n_add += 1
        print(f"{code} {cname} {quarter}: seeded item1 = {value}")
    if n_add:
        JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {len(rows)} rows (+{n_add})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
