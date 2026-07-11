"""Backfill 값_적용후 = 값 for rows where the company/quarter shows no evidence
of any 경과조치 (transition) effect at all.

Root cause of "적용후 하위위험액 숫자가 싹 다 사라짐": most companies never apply
경과조치, so the parser correctly never populates a separate 값_적용후 for them
(there's no separate column in the source disclosure). But K-ICS.html's
getRowValue() (fixed 2026-07-07 per inbox/_resolved/20260707T0700Z) no longer
falls back to 값 when 값_적용후 is missing, to stop a real bug: mixing a
경과조치-적용 company's after-parent with an unextracted before-child. That fix
was correct for the ~21 companies that DO apply transition, but as a side
effect it also blanked every non-적용 company's cells, since their 값_적용후
was never populated in the first place.

This script draws the same distinction at the data layer instead of the
display layer, using a two-phase approach (phase 1 only reads, phase 2 only
writes, so the "is this company/quarter transition-applied" verdict never
depends on rows this same run has already mutated):

Phase 1 — classify:
  - A company is "transition-applying" if ANY of its quarters shows a real
    (present on both sides, beyond tolerance) discrepancy between 값 and
    값_적용후 on items 1/14/27 (가용자본/기준금액/지급여력비율 — where a real
    transition effect shows up first).
  - For a transition-applying company, a specific quarter is only "safe to
    backfill" if items 1/14/27 are all present for that quarter AND equal
    (proven no effect that quarter). If the headline is missing for that
    quarter we can't prove it's safe, so it's treated as unsafe (conservative
    — matches the validated fix's intent: never mix an applied parent with a
    guessed-blank child).
  - A company that is never observed to diverge anywhere is always safe.

Phase 2 — fill: for rows still missing 값_적용후, fill from 값 only if their
(company, quarter) was classified safe in phase 1.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_FILES = [ROOT / "kics_disclosure.json", ROOT / "templates" / "kics_disclosure.json"]

HEADLINE_ITEMS = (1, 14, 27)
TOLERANCE = 0.01


def parse_num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def classify(data):
    """Returns (applying_companies: set[str], safe_quarters: set[(name, q)])."""
    index = {}
    for r in data:
        index.setdefault((r["원수사명"], r["공시분기"]), {})[r["항목번호"]] = r

    applying_companies = set()
    quarter_status = {}  # key -> True (all headline present & equal) / False (diverges) / None (unknown)
    for key, items in index.items():
        name, _ = key
        status = True  # assume equal unless proven otherwise
        for n in HEADLINE_ITEMS:
            row = items.get(n)
            if not row:
                status = None if status is not False else status
                continue
            v = parse_num(row.get("값"))
            va = parse_num(row.get("값_적용후"))
            if v is None or va is None:
                status = None if status is not False else status
                continue
            if abs(v - va) > TOLERANCE:
                status = False
                applying_companies.add(name)
        quarter_status[key] = status

    safe_quarters = set()
    for key, status in quarter_status.items():
        name, _ = key
        if name not in applying_companies:
            safe_quarters.add(key)  # company never seen to diverge -> always safe
        elif status is True:
            safe_quarters.add(key)  # this quarter proven equal even though company applies elsewhere
    return applying_companies, safe_quarters


def backfill(data):
    _, safe_quarters = classify(data)
    filled = 0
    for r in data:
        if r.get("값_적용후") not in (None, ""):
            continue
        if r.get("값") in (None, ""):
            continue  # nothing meaningful to copy
        key = (r["원수사명"], r["공시분기"])
        if key not in safe_quarters:
            continue
        r["값_적용후"] = r["값"]
        filled += 1
    return filled


def main():
    for path in TARGET_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        filled = backfill(data)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"{path.relative_to(ROOT)}: filled {filled} rows")


if __name__ == "__main__":
    main()
