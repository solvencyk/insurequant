#!/usr/bin/env python3
"""Investigation-only probe (writes nothing to any shared master/gold file).

Purpose: compare AIA(KR0080) 2025.4Q PL items currently sourced from the FY2025-template
PROSE paragraph (억-rounded) against the same items re-derived from the audited 포괄손익
계산서(별도) statement (precise), per
inbox/parser/20260901T1630Z__parser__MULTI__pl_gap14_remaining_and_owner_scope.md Q2.

Reuses the existing extractor functions in scripts/pl_breakdown/companies.py (imported
read-only -- no file is written by this script).
"""
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import (  # noqa: E402
    _iter_tables_by_basis,
    _tag_basis,
)
from scripts.pl_breakdown.companies import (  # noqa: E402
    extract_tier2_aia,
    _aia_from_statement,
    _aia_statement,
    _aia_statement_unit,
    _aia_ofs_text,
    _aia_prose_fy2024,
    _row_by_label,
    _row_nums,
    _lab0,
)
from scripts.pl_breakdown.tier2 import _prefer_ofs  # noqa: E402

RAW = "data/dart/FY2025_Q4/raw"
DIRS = sorted(glob.glob(RAW + "/KR0080_*"))
print("dirs:", DIRS)

# ---- 1. build `tables` exactly the way parse_filing() does ----
tables = []
for d in DIRS:
    for x in sorted(glob.glob(d + "/*.xml")):
        try:
            tables.extend(_tag_basis(
                list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
        except Exception as e:
            print("  parse error", x, e)

print(f"\ntotal tables parsed: {len(tables)}")
for t in tables:
    basis = getattr(t, "_basis", None)
    print(f"  basis={basis!s:5s} caption={t.caption!r}")

# ---- 2. current production path (prose, FY2025 template) ----
print("\n" + "=" * 70)
print("CURRENT extract_tier2_aia(tables, dirs) -- prose path (= today's PL_breakdown.json)")
print("=" * 70)
cur = extract_tier2_aia(tables, dirs=DIRS)
for k in sorted(cur):
    print(f"  item{k:2d} = {cur[k]}")

# ---- 3. statement-only path (_aia_from_statement bypasses the FY2025 prose regex) ----
print("\n" + "=" * 70)
print("STATEMENT-ONLY _aia_from_statement(tables, dirs) -- audited 포괄손익계산서(별도)")
print("=" * 70)
stmt_full = _aia_from_statement(tables, DIRS)
for k in sorted(stmt_full):
    print(f"  item{k:2d} = {stmt_full[k]}")

# ---- 4. raw _aia_statement() alone (no FY2024-prose enrichment) ----
ofs_text = _aia_ofs_text(DIRS)
f = _aia_statement_unit(ofs_text)
print(f"\nunit cue -> multiplier to 백만원: f={f}")
stmt_only = _aia_statement(tables, f) if f is not None else {}
print("\n_aia_statement(tables, f) raw (no FY2024-prose enrichment):")
for k in sorted(stmt_only):
    print(f"  item{k:2d} = {stmt_only[k]}")

# ---- 5. does the FY2024-template prose regex match this FY2025 filing at all? ----
enrich = _aia_prose_fy2024(ofs_text, stmt_only) if stmt_only else {}
print("\n_aia_prose_fy2024(ofs_text, stmt_only) match:", enrich)

# ---- 6. locate the exact statement table + print its raw rows for citation ----
print("\n" + "=" * 70)
print("RAW STATEMENT TABLE ROWS (별도, basis != CFS, 포괄손익계산서 candidate)")
print("=" * 70)
cand = None
for t in _prefer_ofs(tables):
    if getattr(t, "_basis", None) == "CFS":
        continue
    labs = [_lab0(r) for r in (t.rows or [])]
    if (any("보험영업수익" in l for l in labs)
            and any("보험영업비용" in l for l in labs)
            and any("당기순이익" in l for l in labs)):
        cand = t
        break
if cand is None:
    print("  NO CANDIDATE TABLE FOUND")
else:
    print(f"  caption={cand.caption!r} basis={getattr(cand, '_basis', None)}")
    print(f"  header={cand.header}")
    for r in cand.rows or []:
        lab = _lab0(r)
        nums = _row_nums(r)
        print(f"    {lab!r:45s} nums(first 4)={nums[:4]}")

# ---- 7. search full filing text for a genuine CSM roll-forward NOTE TABLE (not prose) ----
print("\n" + "=" * 70)
print("SEARCH: genuine CSM(보험계약마진) roll-forward NOTE TABLE across ALL tables")
print("=" * 70)
csm_table_hits = []
for t in tables:
    cap = t.caption or ""
    labs = [_lab0(r) for r in (t.rows or [])]
    hay = cap + " " + " ".join(labs)
    if "보험계약마진" in hay or "CSM" in hay:
        csm_table_hits.append(t)
for t in csm_table_hits:
    print(f"  caption={t.caption!r} basis={getattr(t, '_basis', None)} n_rows={len(t.rows or [])}")
    for r in (t.rows or [])[:20]:
        print(f"      {_lab0(r)!r}")

if not csm_table_hits:
    print("  NONE -- no table (caption or row-label) mentions 보험계약마진/CSM anywhere in the filing.")

# ---- 8. raw-text occurrence count of 보험계약마진 (to see if it's prose-only) ----
print("\n" + "=" * 70)
print("RAW TEXT occurrences of 보험계약마진 in each xml (tag-stripped)")
print("=" * 70)
for d in DIRS:
    for x in sorted(glob.glob(d + "/*.xml")):
        try:
            raw = open(x, "rb").read().decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        stripped = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw))
        n = stripped.count("보험계약마진")
        print(f"  {x}: {n} occurrences (raw len={len(raw)})")
        if n:
            # print each occurrence with 80-char context
            for m in re.finditer("보험계약마진", stripped):
                s = max(0, m.start() - 60)
                e = min(len(stripped), m.end() + 80)
                print(f"      ...{stripped[s:e]}...")
