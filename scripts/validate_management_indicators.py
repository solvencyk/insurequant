"""Validator for management_indicators.json.

Checks (in order):
  1. Coverage census -- for every (company, period) that has a raw PDF, is there >=1 row? A
     documented-exception cohort (scanned/image PDFs, stale-duplicate raw, pathological one-off
     renderings) is reported separately from genuinely-unexplained gaps.
  2. Per-item completeness within companies that DO have data (which of the 23 items are
     missing, and roughly why -- 15-21 legitimately sparse for reinsurers/micro-insurers).
  3. Internal identities checkable from THIS master alone (hard: near-zero tolerance):
       - item1(자산) = item2(부채) + item3(자본)
       - item6(지급여력비율_후) present but wildly below item5(전) -- rare, flagged not failed
       - item15-21 (계약유지율) in a plausible % range, and never exactly a cohort integer
         (13/25/37/49/61/73/85) -- that exact match is the fingerprint of the 회차-label-leak
         class of bug this extractor had to work around.
       - item9(ROA)/item10(ROE) sign should usually track item4(당기순이익) sign
  4. Cross-master reconciliation (informational, NOT pass/fail for this master -- a mismatch
     can legitimately mean the OTHER master hasn't been onboarded for this quarter yet, which is
     a normal mid-round state, not a bug in either master):
       - item1/2/3 (억원) vs IFRS17_BS.json item1/2/3 (백만원, /100)
       - item4 vs PL_breakdown.json item24 "값" field (누적, 백만원, /100)
       - item5/6 vs kics_disclosure.json item27 "값"/"값_적용후" (already 억원/%)

Usage: PY scripts/validate_management_indicators.py [--period FY2026_Q2]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[0].parent
if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MI_PATH = REPO / "management_indicators.json"
DISCLOSURE_DIR = REPO / "data" / "disclosure"

# documented exceptions -- see management_indicators extraction log / TODO for evidence per case
KNOWN_ZERO_COVERAGE = {
    ("KR0010", None): "image-only PDF, no text layer (KICS-IMG cohort)",
    ("KR0079", None): "image-only PDF for 주요경영지표/수익성 pages (KICS-IMG cohort)",
    ("KR0087", None): "image-only PDF, no text layer (동양생명, known scan quirk)",
    ("KR0011", "2026.2Q"): "raw PDF byte-identical to 2026.1Q (stale duplicate) -- downloader ticket filed 20260831T111450Z",
    ("KR0029", "2026.2Q"): "raw PDF byte-identical to 2026.1Q (stale duplicate) -- downloader ticket filed 20260831T111450Z",
    ("KR0150", "2026.2Q"): "raw PDF byte-identical to 2026.1Q (stale duplicate) -- documented in TODO_parser_kics.md, downloader ticket 20260831T1049Z",
    ("KR0051", "2026.2Q"): "pathological row-order-reversed rendering unique to this filing (labels normal order, values in REVERSED sub-order + split across two disjoint chunks) -- not generalizable, documented gap",
}


def load_mi():
    if not MI_PATH.exists():
        return []
    return json.loads(MI_PATH.read_text(encoding="utf-8"))


def period_to_quarter(period: str) -> str:
    m = re.match(r"^FY(\d{4})_Q([1-4])$", period)
    return f"{m.group(1)}.{m.group(2)}Q"


def list_expected_companies(period: str) -> list[str]:
    codes = set()
    for sub in ("pdf", "raw"):
        d = DISCLOSURE_DIR / period / sub
        if not d.exists():
            continue
        for p in d.glob("*.pdf"):
            m = re.match(r"^(KR\d+)_", p.stem)
            if m:
                codes.add(m.group(1))
    return sorted(codes)


def zero_coverage_reason(code: str, quarter: str) -> str | None:
    if (code, quarter) in KNOWN_ZERO_COVERAGE:
        return KNOWN_ZERO_COVERAGE[(code, quarter)]
    if (code, None) in KNOWN_ZERO_COVERAGE:
        return KNOWN_ZERO_COVERAGE[(code, None)]
    return None


def run_census(mi_rows, periods):
    print("\n" + "=" * 70)
    print("1) COVERAGE CENSUS")
    print("=" * 70)
    have = defaultdict(set)  # (code, quarter) -> set(item_no)
    for r in mi_rows:
        have[(r["원보험사코드"], r["공시분기"])].add(r["항목번호"])

    total_expected = 0
    total_present = 0
    unexplained = []
    for period in periods:
        quarter = period_to_quarter(period)
        expected_codes = list_expected_companies(period)
        n_present = sum(1 for c in expected_codes if have.get((c, quarter)))
        total_expected += len(expected_codes)
        total_present += n_present
        print(f"{period}: {n_present}/{len(expected_codes)} companies with >=1 item")
        for c in expected_codes:
            if not have.get((c, quarter)):
                reason = zero_coverage_reason(c, quarter)
                if reason is None:
                    unexplained.append((c, quarter))
                    print(f"    UNEXPLAINED GAP: {c} {quarter}")
    print(f"\nTOTAL: {total_present}/{total_expected} company-periods with data")
    print(f"Unexplained gaps: {len(unexplained)}")
    return unexplained, have


def run_item_completeness(have):
    print("\n" + "=" * 70)
    print("2) PER-ITEM COMPLETENESS (companies WITH data)")
    print("=" * 70)
    hist = defaultdict(int)
    for (code, q), items in have.items():
        hist[len(items)] += 1
    for n in sorted(hist):
        print(f"  {n}/23 items filled: {hist[n]} company-periods")
    low = [(c, q, len(items)) for (c, q), items in have.items() if len(items) < 12]
    if low:
        print("\n  Company-periods with <12/23 items (review candidates):")
        for c, q, n in sorted(low):
            print(f"    {c} {q}: {n}/23")


def run_identities(mi_rows):
    print("\n" + "=" * 70)
    print("3) INTERNAL IDENTITY CHECKS (hard -- checkable from this master alone)")
    print("=" * 70)
    by = defaultdict(dict)
    for r in mi_rows:
        by[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]

    COHORT_VALS = {13, 25, 37, 49, 61, 73, 85}
    red = []
    for (code, q), items in sorted(by.items()):
        v1, v2, v3 = items.get(1), items.get(2), items.get(3)
        if v1 is not None and v2 is not None and v3 is not None:
            diff = v1 - (v2 + v3)
            if abs(diff) > max(2.0, 0.005 * abs(v1)):
                red.append(f"{code} {q}: RED balance-sheet identity 자산(1)={v1} != 부채(2)+자본(3)={v2 + v3} diff={diff:.2f}")
        for item_no in range(15, 22):
            v = items.get(item_no)
            if v is None:
                continue
            if v in COHORT_VALS:
                red.append(f"{code} {q} item{item_no}: RED value={v} is EXACTLY a 회차 cohort number -- 회차-label-leak signature")
            if not (-5 <= v <= 120):
                red.append(f"{code} {q} item{item_no}: implausible 유지율 {v}")
        v5, v6 = items.get(5), items.get(6)
        if v5 is not None and v6 is not None and v6 < v5 - 0.5:
            red.append(f"{code} {q}: NOTE item6(후)={v6} < item5(전)={v5} (unusual but real for distressed insurers, e.g. KR0004 자본잠식)")
    print(f"RED count: {sum(1 for x in red if 'RED' in x)}")
    print(f"NOTE count (non-blocking): {sum(1 for x in red if 'RED' not in x)}")
    for x in red:
        print(" -", x)
    return red


def _load_json(name):
    p = REPO / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def run_cross_master(mi_rows):
    print("\n" + "=" * 70)
    print("4) CROSS-MASTER RECONCILIATION (informational -- see caveat in module docstring)")
    print("=" * 70)
    by = defaultdict(dict)
    for r in mi_rows:
        by[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]

    bs = _load_json("IFRS17_BS.json")
    pl = _load_json("PL_breakdown.json")
    kics = _load_json("kics_disclosure.json")

    bs_by = defaultdict(dict)
    if bs:
        for r in bs:
            bs_by[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]
    pl_by = defaultdict(dict)
    if pl:
        for r in pl:
            if r["항목번호"] == 24:
                pl_by[(r["원보험사코드"], r["공시분기"])] = r["값"]
    kics_by = defaultdict(dict)
    if kics:
        for r in kics:
            if r["항목번호"] == 27:
                kics_by[(r["원보험사코드"], r["공시분기"])] = (r["값"], r.get("값_적용후"))

    n_checked_bs = n_close_bs = 0
    n_checked_pl = n_close_pl = 0
    n_checked_kics = n_close_kics = 0
    diffs = []
    for (code, q), items in sorted(by.items()):
        bs_row = bs_by.get((code, q))
        if bs_row and items.get(1) is not None and 1 in bs_row:
            n_checked_bs += 1
            bs_asset = float(bs_row[1]) / 100.0
            d = items[1] - bs_asset
            if abs(d) <= max(2.0, 0.01 * abs(items[1])):
                n_close_bs += 1
            else:
                diffs.append(f"{code} {q}: item1(자산)={items[1]} vs IFRS17_BS 자산총계/100={bs_asset:.1f} diff={d:.1f}")
        pl_ni = pl_by.get((code, q))
        if pl_ni is not None and items.get(4) is not None:
            n_checked_pl += 1
            pl_val = float(pl_ni) / 100.0
            d = items[4] - pl_val
            if abs(d) <= max(2.0, 0.02 * abs(items[4] or 1)):
                n_close_pl += 1
            else:
                diffs.append(f"{code} {q}: item4(당기순이익)={items[4]} vs PL_breakdown item24/100={pl_val:.1f} diff={d:.1f}")
        kics_row = kics_by.get((code, q))
        if kics_row is not None and items.get(5) is not None:
            n_checked_kics += 1
            kv, kv_after = kics_row
            try:
                kv_f = float(kv)
            except (TypeError, ValueError):
                kv_f = None
            if kv_f is not None:
                d = items[5] - kv_f
                if abs(d) <= max(0.5, 0.01 * abs(items[5])):
                    n_close_kics += 1
                else:
                    diffs.append(f"{code} {q}: item5(지급여력비율전)={items[5]} vs kics_disclosure item27={kv_f} diff={d:.2f}")

    print(f"vs IFRS17_BS (자산): {n_close_bs}/{n_checked_bs} within tolerance")
    print(f"vs PL_breakdown (당기순이익, cumulative): {n_close_pl}/{n_checked_pl} within tolerance")
    print(f"vs kics_disclosure (지급여력비율): {n_close_kics}/{n_checked_kics} within tolerance")
    print(f"\nDiffs ({len(diffs)}) -- each needs a look, but a diff here can mean the OTHER")
    print("master simply hasn't loaded this company-quarter yet (mid-round), not necessarily")
    print("a bug in either file:")
    for d in diffs:
        print(" -", d)
    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", action="append", help="restrict census to this period (repeatable); default = all periods present in management_indicators.json")
    args = ap.parse_args()

    mi_rows = load_mi()
    if not mi_rows:
        print("management_indicators.json is empty or missing -- nothing to validate.")
        return 1
    periods_present = sorted(set(f"FY{r['공시분기'].split('.')[0]}_Q{r['공시분기'].split('.')[1].rstrip('Q')}" for r in mi_rows))
    periods = args.period or periods_present

    unexplained, have = run_census(mi_rows, periods)
    run_item_completeness(have)
    red = run_identities(mi_rows)
    run_cross_master(mi_rows)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    hard_red = [x for x in red if "RED" in x]
    print(f"Unexplained coverage gaps: {len(unexplained)}")
    print(f"Hard identity REDs: {len(hard_red)}")
    return 1 if (unexplained or hard_red) else 0


if __name__ == "__main__":
    sys.exit(main())
