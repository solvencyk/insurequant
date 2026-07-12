"""Close the 적용후 요구자본 census gap flagged by validation
(inbox/parser/20260712T0230Z, data/_derived/after_census_gaps.json).

Owner directive: 적용후 must get the SAME census/identity rigor as 적용전.
The existing after-capture pipeline only checked item17/19 leaf mmult; it
never checked that item15's own components (16-21) are all present. This
script closes the two mechanical fix-classes from that audit:

  CARRY  (item20/21, item36-40): 값_적용후 = 값 for cells validation has
         already determined are transition-unrelated for that
         (company, quarter) — 신용/운영위험 always, 시장 하위위험 only
         when item19 itself shows no 경과조치 effect that quarter.
  DERIVE (item16, 분산효과): value_적용후 = sum(item17..21 적용후) - item15_적용후,
         same identity recalc_basic_capital_ratio_post.py already uses for
         item27/28. Must run after CARRY (and after any EXTRACT work) so
         17-21 are fully populated first.

fix_class EXTRACT (raw re-extraction, 20 cells) is NOT handled here — those
need individual raw verification and are filled by hand per the inbox
thread, same as every other raw-extraction round this session.

UPSERT: only ever fills a currently-None 값_적용후; never overwrites an
existing value. Re-running is safe.

Usage: python scripts/fill_after_requirement_census.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GAPS_PATH = REPO / "data" / "_derived" / "after_census_gaps.json"
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]

DERIVE_INPUTS = (17, 18, 19, 20, 21)


def _parse_num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    gaps = json.loads(GAPS_PATH.read_text(encoding="utf-8"))
    carry_keys = {
        (r["code"], r["quarter"], r["child"])
        for r in gaps["records"]
        if r["fix_class"] == "CARRY"
    }
    derive_keys = {
        (r["code"], r["quarter"])
        for r in gaps["records"]
        if r["fix_class"] == "DERIVE" and r["child"] == 16
    }

    data = json.loads(TARGET_FILES[0].read_text(encoding="utf-8"))
    index: dict[tuple[str, str, int], dict] = {}
    for r in data:
        index[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r

    carry_filled = 0
    for code, quarter, item_no in sorted(carry_keys):
        row = index.get((code, quarter, item_no))
        if row is None:
            continue
        if row.get("값_적용후") not in (None, ""):
            continue
        if row.get("값") in (None, ""):
            continue
        row["값_적용후"] = row["값"]
        carry_filled += 1

    # item18(일반손해보험위험액) isn't in validation's CARRY list, but it blocks
    # nearly all of the item16 DERIVE cells for life-only insurers: these
    # companies structurally never write general/P&C insurance (값=0 always,
    # confirmed uniformly across every DERIVE-blocked company/quarter except
    # KR0003 2026.1Q, which is already its own EXTRACT case), so a K-ICS
    # transition provision has nothing to change here either — same
    # carry-forward logic as item20/21, just missed by the census audit
    # because item18 isn't one of the 15's fixed children it iterated.
    item18_filled = 0
    for code, quarter in sorted(derive_keys):
        row18 = index.get((code, quarter, 18))
        if row18 is None or row18.get("값_적용후") not in (None, ""):
            continue
        pre = _parse_num(row18.get("값"))
        if pre is not None and abs(pre) < 0.01:
            row18["값_적용후"] = row18["값"]
            item18_filled += 1

    derive_filled = 0
    derive_skipped = []
    for code, quarter in sorted(derive_keys):
        row16 = index.get((code, quarter, 16))
        row15 = index.get((code, quarter, 15))
        if row16 is None or row15 is None:
            derive_skipped.append((code, quarter, "missing item15/16 row"))
            continue
        if row16.get("값_적용후") not in (None, ""):
            continue
        post15 = _parse_num(row15.get("값_적용후"))
        if post15 is None:
            derive_skipped.append((code, quarter, "item15 후 missing"))
            continue
        components = []
        missing = []
        for n in DERIVE_INPUTS:
            row = index.get((code, quarter, n))
            v = _parse_num(row.get("값_적용후")) if row else None
            if v is None:
                missing.append(n)
            else:
                components.append(v)
        if missing:
            derive_skipped.append((code, quarter, f"item {missing} 후 still missing"))
            continue
        value = sum(components) - post15
        row16["값_적용후"] = _fmt(value)
        derive_filled += 1

    print(f"CARRY filled: {carry_filled} / {len(carry_keys)} candidates")
    print(f"item18 zero-carry filled: {item18_filled}")
    print(f"DERIVE filled: {derive_filled} / {len(derive_keys)} candidates")
    if derive_skipped:
        print(f"DERIVE skipped ({len(derive_skipped)}):")
        for code, quarter, why in derive_skipped:
            print(f"  {code} {quarter}: {why}")

    if args.dry_run:
        print("(dry-run; no write)")
        return

    for path in TARGET_FILES:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
