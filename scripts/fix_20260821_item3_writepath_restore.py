"""Restore item3 (보완자본) cells silently overwritten by the unconditional
item3 = item1 - item2 derivation in recalc_kics_derived.py (lines 188-210,
no tolerance gate at all -- unlike item4's, this one overwrites regardless of
how large the discrepancy is). Flagged by validation's new IDENTITY_TAUTOLOGY
meta-rule: R1_가용자본=기본+보완 적용전, n=477, 97.7% exact-zero vs 75.0% null
(excess=1.30, z=11.4).

Methodology identical to fix_20260821_item4_writepath_restore.py: for every
(code, quarter) where master item3 == item1-item2 EXACTLY (tautology
fingerprint) and raw md_inbox's own item3 row (label match, not derived)
differs, replace item3 with the raw value.

80 candidates found (scripts/_probes/probe_item3_raw_vs_master.py). 1
excluded (documented below) -- the rest are a clean, uniform +-1 rounding
signature except one +3 cell that raw-verifies unambiguously.

  - KR0087 동양생명 2024.4Q: EXCLUDED. The auto-matcher's "raw" hit (2,231,293)
    came from a DIFFERENT table (경과조치 세부, 백만원 units,
    md_inbox/FY2024_Q4/KR0087_동양생명.md L214) than the main summary table
    (억원 units) -- 2,231,293백만원 / 100 = 22,312.93억원, which is what
    master already holds (22313, matching item1-item2). Master's current
    value is very likely already correct; the "difference" was a unit-scale
    mismatch in automated matching, not a real discrepancy. Left untouched.

  - KR0004 예별손해 2024.2Q: raw=3085 (md_inbox/FY2024_Q2/KR0004_예별손해보험.md
    L270, column "2024년 2/4분기") vs master/derived=3082.02, diff=+2.98.
    Applied -- single unambiguous column read, no competing table.

Cell-by-cell UPSERT; prints before/after census.
"""
from __future__ import annotations
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero
from solvency.parser.kics_disclosure_parser import build_label_lookups, extract_kics_detail_rows

JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_INAME = "항목명"
KEY_Q = "공시분기"
KEY_VAL = "값"

EXCLUDE_FROM_AUTOFIX = {("KR0087", "2024.4Q")}  # see module docstring


def _to_float(raw):
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _md_period_to_quarter(period):
    import re
    m = re.match(r"^FY(\d{4})_Q([1-4])$", period)
    return f"{m.group(1)}.{m.group(2)}Q"


def find_tautology_cells(rows):
    buckets = defaultdict(dict)
    for r in rows:
        it = r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        buckets[(r.get(KEY_CODE), r.get(KEY_Q))][it] = r

    md_path_for = {}
    for period_dir in sorted(MD_INBOX.glob("FY*_Q?")):
        if not period_dir.is_dir():
            continue
        try:
            q = _md_period_to_quarter(period_dir.name)
        except Exception:
            continue
        for md_path in sorted(period_dir.glob("*.md")):
            code = md_path.stem.split("_", 1)[0]
            md_path_for[(code, q)] = md_path

    confirmed = []
    for (code, q), items in buckets.items():
        r3 = items.get(3)
        r1 = items.get(1)
        r2 = items.get(2)
        if r3 is None or r1 is None or r2 is None:
            continue
        cur_val = _to_float(r3.get(KEY_VAL))
        i1 = _to_float(r1.get(KEY_VAL))
        i2 = _to_float(r2.get(KEY_VAL))
        if cur_val is None or i1 is None or i2 is None:
            continue
        derived = i1 - i2
        item_name = r3.get(KEY_INAME)
        md_path = md_path_for.get((code, q))
        if md_path is None:
            continue
        table = extract_kics_detail_rows(md_path.read_text(encoding="utf-8"), q)
        if not table:
            continue
        lookup, core = build_label_lookups(table)
        raw_val = match_baseline_value_or_zero(item_name, lookup, core, table)
        if raw_val is None:
            continue
        raw_f = _to_float(raw_val)
        if raw_f is None or abs(cur_val - raw_f) < 1e-6:
            continue

        master_eq_derived = abs(cur_val - derived) < 1e-6
        raw_eq_derived = abs(raw_f - derived) < 1e-6
        # include both: (a) classic tautology (master==derived, raw differs)
        # and (b) the KR0097 2024.4Q pattern (raw==derived, master matches
        # neither -- so raw is still the best evidenced value; see docstring
        # in probe_item3_raw_vs_master.py output for this one case).
        if (master_eq_derived and not raw_eq_derived) or (raw_eq_derived and not master_eq_derived):
            confirmed.append((code, q, cur_val, raw_val, raw_f, derived))
    return confirmed


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    confirmed = find_tautology_cells(rows)
    print(f"tautology/mismatch-confirmed item3 cells found this run: {len(confirmed)} (expect 81)")

    by_key = defaultdict(dict)
    for r in rows:
        it = r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        by_key[(r.get(KEY_CODE), r.get(KEY_Q), it)] = r

    pre_changes = []
    skipped = []

    for code, q, cur_val, raw_val, raw_f, derived in confirmed:
        if (code, q) in EXCLUDE_FROM_AUTOFIX:
            skipped.append((code, q, cur_val, raw_val, derived))
            continue
        row = by_key.get((code, q, 3))
        if row is None:
            print(f"  ABORT: {code} {q} item3 row not found")
            sys.exit(1)
        old_val = row.get(KEY_VAL)
        if str(old_val) != str(raw_val):
            row[KEY_VAL] = raw_val
            pre_changes.append((code, q, old_val, raw_val))

    print(f"\npre-column (값) item3 cells changed: {len(pre_changes)}")
    for c in pre_changes:
        print("  ", c)
    print(f"\nexcluded from auto-apply (documented, see module docstring): {len(skipped)}")
    for s in skipped:
        print("  ", s)

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(rows)} rows (row_count unchanged) -- {len(pre_changes)} cells touched")


if __name__ == "__main__":
    main()
