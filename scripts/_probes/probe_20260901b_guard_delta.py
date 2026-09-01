# -*- coding: utf-8 -*-
"""Isolate exactly how many of the 39 files flip accept->review because of the
NEW missing_window/ratio_critical checks, vs how many were already review
under the pre-existing missing_core/missing_ext/score<0.7 conditions."""
from __future__ import annotations
import io, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "src"))
from solvency.parser import quality_check as qc

md_root = REPO / "md_inbox"
new_review = 0
old_review = 0
flipped_by_guard = []
for p in sorted(md_root.rglob("*.md")):
    meta, body = qc._read_md(p)
    missing_core = qc._missing_rows(body, qc._RE_REQUIRED_CORE)
    missing_extended = qc._missing_rows(body, qc._RE_REQUIRED_EXTENDED)
    has_unit = qc._has_unit(body)
    has_date = bool(meta.get("disclosure_date", "").strip())
    rate = qc._numeric_normalisation_rate(body)
    score_value = 1.0
    score_value -= 0.2 * len(missing_core)
    score_value -= 0.1 * len(missing_extended)
    if not has_unit:
        score_value -= 0.15
    if not has_date:
        score_value -= 0.1
    score_value *= max(rate, 0.5)
    score_value = max(0.0, min(1.0, score_value))
    critical_missing = "생명장기손해보험위험액" in missing_extended
    was_review = bool(missing_core or critical_missing or score_value < 0.7)

    report = qc.score(p)
    is_review = report.decision == "review"

    if was_review:
        old_review += 1
    if is_review:
        new_review += 1
    if is_review and not was_review:
        flipped_by_guard.append(p.name)

print(f"old-style review count (pre-existing rules only): {old_review}/39")
print(f"new (with missing_window/ratio guard) review count: {new_review}/39")
print(f"files flipped accept->review SOLELY by the new guard: {len(flipped_by_guard)}")
for f in flipped_by_guard:
    print(" ", f)
