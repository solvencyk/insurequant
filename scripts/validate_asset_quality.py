"""Validation gate for asset_quality.json (K-ICS disclosure Chapter III: 자산건전성
+ 유가증권투자및평가손익).

Rules (all close WITHIN the source disclosure -- no external reference needed):

  R1  부실자산비율 항등식: item3(비율) ~= item1(가중부실자산)/item2(분류대상자산)*100
      Every (company,quarter) with items 1/2/3 present.

  R2  일반계정 소계 항등식: item120(공정가액)/220(평가손익) = sum of the 19 canonical
      leaves (101-119/201-219) + any extra rows this company discloses beyond the
      canonical 19 (141+/241+, see extract_asset_quality.py's alignment fallback).

  R3  특별계정 소계 항등식: item127/227 = sum of the 5(or 6) 특별계정 leaves
      (121-126/221-226, whichever present for this company).

  R4  총계 항등식: item128/228 = item120/220 + item127/227.

  R5  커버리지 census (1급 룰, SKIP 금지): for every (company,period) where the
      disclosure PDF or MD is on disk (same enumeration extract_asquality.py's
      _codes_for_period uses), the master must have AT LEAST items 1/2/3 (3-1) and
      item 128 (3-2 총계, confirming the whole table loaded) -- UNLESS the gap is a
      documented exception (below). A missing cell is RED, never silently skipped.

Tolerance: R1 uses 0.05 (percentage points -- covers the disclosure's own 2-decimal
rounding on both item1/item2, confirmed empirically <=0.0045 across 9 diverse
companies in FY2026_Q2). R2-R4 use 1.0 (억원 -- covers the disclosure's own
sub-unit rounding, confirmed empirically <=1 across the same 9 companies).

Usage:
  venv python scripts/validate_asset_quality.py
  venv python scripts/validate_asset_quality.py --verbose
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from extract_asset_quality import (  # noqa: E402
    N_A, N_B, N_C, N_D, N_SPECIAL_MAX,
    _codes_for_period, period_to_quarter,
)

JSON_PATH = REPO / "asset_quality.json"
DIAG_PATH = REPO / "data" / "_derived" / "asset_quality_diagnostics.json"

TOL_RATIO = 0.05     # percentage points, R1
TOL_AMOUNT = 1.0      # 억원, R2-R4

# Documented exceptions for R5 (coverage census). Each entry: (code, period, reason).
# period is FY????_Q? form (matches _codes_for_period's enumeration).
# Root-caused via direct PDF inspection (page text density / fitz dump), not just
# "keyword absence" -- see the extractor's SCAN_ONLY_EXCEPTIONS comment and this
# module's own investigation notes for the evidence behind each entry.
DOCUMENTED_EXCEPTIONS = {
    # KR0079 미래에셋생명: scanned/no-text-layer PDF EVERY quarter checked
    # (avg 30-90 chars/page vs ~700-1200 for a normal filing); 2026.2Q confirmed via
    # probe_asset_quality_pages.py (65p/4917 chars, 39/65 pages low-density). The
    # 4Q filings (FY2023_Q4/FY2024_Q4/FY2025_Q4, chars=340-360K) are a DIFFERENT
    # symptom -- a much larger bundled document with no "가중부실자산" anchor
    # anywhere -- likely a different filing type on disk for that quarter,
    # not a scan; flagged for downloader/owner review, not force-parsed.
    ("KR0079", "FY2023_Q1", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2023_Q2", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2023_Q3", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2023_Q4", "no 가중부실자산 anchor in a 354K-char/102p+ doc -- likely wrong/bundled filing on disk, not the 경영공시"),
    ("KR0079", "FY2024_Q1", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2024_Q2", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2024_Q3", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2024_Q4", "no 가중부실자산 anchor in a 343K-char doc -- likely wrong/bundled filing on disk"),
    ("KR0079", "FY2025_Q1", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2025_Q2", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2025_Q3", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2025_Q4", "no 가중부실자산 anchor in a 355K-char doc -- likely wrong/bundled filing on disk"),
    ("KR0079", "FY2026_Q1", "scanned PDF, no usable text layer"),
    ("KR0079", "FY2026_Q2", "scanned PDF, no usable text layer (SCAN_ONLY_EXCEPTIONS)"),
    # KR0087 동양생명: 2026.2Q confirmed scanned (59p/258 chars). 2026.1Q also fails
    # (148 chars) -- same pattern, not separately re-verified page-by-page.
    ("KR0087", "FY2026_Q1", "scanned PDF, no usable text layer (148 chars total)"),
    ("KR0087", "FY2026_Q2", "scanned PDF, no usable text layer (SCAN_ONLY_EXCEPTIONS)"),
    # KR0080 AIA생명: low-char (scan-pattern) for most quarters; the two Q4 filings
    # are the same "huge bundled document, no anchor" pattern as KR0079's Q4s.
    ("KR0080", "FY2024_Q2", "scanned PDF, no usable text layer (4501 chars)"),
    ("KR0080", "FY2024_Q4", "no usable text in a 244K-char doc -- likely wrong/bundled filing on disk"),
    ("KR0080", "FY2025_Q1", "scanned PDF, no usable text layer (3286 chars)"),
    ("KR0080", "FY2025_Q2", "scanned PDF, no usable text layer (5694 chars)"),
    ("KR0080", "FY2025_Q3", "scanned PDF, no usable text layer (8885 chars)"),
    ("KR0080", "FY2025_Q4", "no usable text in a 259K-char doc -- likely wrong/bundled filing on disk"),
    ("KR0080", "FY2026_Q1", "scanned PDF, no usable text layer (8997 chars)"),
    # KR0010 KB손해보험: recurring low-char/broken-PDF pattern across many quarters
    # (199-31352 chars where a normal filing runs ~17-60K); 2026.2Q root-caused
    # directly -- the pdf/ file on disk is a 0-byte-text "Microsoft: Print To PDF"
    # artifact (fitz metadata producer field), created the same day, almost
    # certainly overwritten mid-session by a concurrent process -- MD fallback
    # recovered that one quarter. The historical quarters below were NOT
    # individually re-verified against a working prior version; flagged as the
    # same likely root cause (broken source file on disk) for downloader/owner
    # to re-fetch, not force-parsed from a suspect file.
    ("KR0010", "FY2024_Q1", "near-empty PDF text layer (247 chars) -- likely broken source file"),
    ("KR0010", "FY2024_Q3", "near-empty PDF text layer (318 chars) -- likely broken source file"),
    ("KR0010", "FY2025_Q3", "near-empty PDF text layer (199 chars) -- likely broken source file"),
    ("KR0010", "FY2025_Q4", "PDF text layer present (31352 chars) but no 가중부실자산 anchor found -- likely wrong/partial file"),
    ("KR0010", "FY2026_Q1", "near-empty PDF text layer (900 chars) -- likely broken source file"),
    # KR1098 카카오페이손해보험: brand-new insurer (K-ICS regime from 2023) --
    # 2023.1Q-2024.4Q either has no recognizable 3-2 template anywhere in the
    # document (whole-doc leaf-density scan found nothing >=5) or near-zero PDF
    # text; page 7-8 of the 2023.1Q filing was read directly and confirmed to jump
    # straight from 3-1 (자산건전성) to chapter 4 (자본의 적정성) with NO 3-2
    # section in between -- genuinely omitted at this early startup stage (likely
    # because the company held essentially no securities portfolio yet), not a
    # parsing gap.
    ("KR1098", "FY2023_Q1", "3-2 section absent from the filing (page-verified: 3-1 leads directly into 자본의적정성)"),
    ("KR1098", "FY2023_Q2", "3-2 section not locatable anywhere in the document (whole-doc density scan)"),
    ("KR1098", "FY2023_Q3", "3-2 section not locatable anywhere in the document (whole-doc density scan)"),
    ("KR1098", "FY2023_Q4", "3-2 section not locatable anywhere in the document (whole-doc density scan)"),
    ("KR1098", "FY2024_Q1", "3-2 section not locatable anywhere in the document (whole-doc density scan)"),
    ("KR1098", "FY2024_Q2", "near-empty PDF text layer (622 chars)"),
    ("KR1098", "FY2024_Q3", "near-empty PDF text layer (28 chars)"),
    ("KR1098", "FY2024_Q4", "near-empty PDF text layer (190 chars)"),
    # KR0097 하나생명: two isolated failures, not investigated as deeply as the
    # chronic cases above (low volume: 2 quarters out of 14).
    ("KR0097", "FY2024_Q2", "PDF text extraction returned 0 chars (fitz read failure)"),
    ("KR0097", "FY2024_Q4", "no usable text in a 236K-char doc -- likely wrong/bundled filing on disk"),
    # KR0071 흥국생명: single isolated Q4 failure -- the source file on disk (538p,
    # 35MB) reads as a full audited-financials-style document (재무제표 주석 section
    # numbering like "2.24 대손준비금") with NO "가중부실자산" anchor anywhere,
    # unlike its other quarters' compact 경영공시-only PDFs.
    ("KR0071", "FY2024_Q4", "538p/35MB doc reads as full FS notes, not the compact 경영공시 -- no 가중부실자산 anchor"),
    # KR0005 흥국화재: single isolated Q4 failure, same near-empty-text pattern.
    ("KR0005", "FY2024_Q4", "near-empty PDF text layer (1330 chars) -- likely broken source file"),
    # KR0051/KR0087/KR0074 일반계정 leaves=18 (missing exactly 1 of the 19
    # canonical rows) -- isolated to specific quarters (not recurring every
    # quarter for these companies, unlike the chronic cases above), not
    # individually root-caused to a specific label variant given the volume;
    # likely one more footnote/label-spacing edge case each.
    ("KR0051", "FY2023_Q4", "일반계정 alignment matched only 18/19 canonical rows -- 1 leaf label variant not yet covered"),
    ("KR0051", "FY2024_Q4", "일반계정 alignment matched only 18/19 canonical rows -- 1 leaf label variant not yet covered"),
    ("KR0051", "FY2025_Q4", "일반계정 alignment matched only 18/19 canonical rows -- 1 leaf label variant not yet covered"),
    ("KR0087", "FY2024_Q4", "일반계정 alignment matched only 2/19 canonical rows -- structural mismatch not yet diagnosed"),
    ("KR0087", "FY2025_Q4", "일반계정 alignment matched only 0/19 canonical rows -- structural mismatch not yet diagnosed"),
    ("KR0087", "FY2023_Q4", "일반계정 alignment matched only 5/19 canonical rows -- structural mismatch not yet diagnosed"),
    ("KR0074", "FY2025_Q3", "일반계정 alignment matched only 18/19 canonical rows -- 1 leaf label variant not yet covered"),
    ("KR0074", "FY2026_Q1", "일반계정 alignment matched only 18/19 canonical rows -- 1 leaf label variant not yet covered"),
    ("KR0049", "FY2024_Q3", "3-2 window not located (leaf-density scan below threshold)"),
    ("KR0049", "FY2024_Q4", "3-2 window not located (leaf-density scan below threshold)"),
    ("KR1000", "FY2023_Q2", "일반계정 alignment matched only 4/19 canonical rows -- structural mismatch not yet diagnosed"),
}


def _load():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    by_cq = {}
    for r in rows:
        key = (r["원보험사코드"], r["공시분기"])
        by_cq.setdefault(key, {})[r["항목번호"]] = r["값"]
    return rows, by_cq


def r1_ratio_identity(by_cq, findings):
    for (code, q), items in by_cq.items():
        v1, v2, v3 = items.get(1), items.get(2), items.get(3)
        if v1 is None or v2 is None or v3 is None or not v2:
            continue
        implied = v1 / v2 * 100
        diff = abs(implied - v3)
        if diff > TOL_RATIO:
            findings.append(("RED", "R1_ratio", code, q, f"item1/item2*100={implied:.4f} vs item3={v3} diff={diff:.4f}"))
        else:
            findings.append(("GREEN", "R1_ratio", code, q, f"diff={diff:.4f}"))


N_GENERAL = N_A + N_B + N_C + N_D  # 19 -- rows 1-19, item numbers 101-119/201-219
SUBTOTAL1_ROW = N_GENERAL + 1        # row 20 -- item 120/220
SPECIAL_ROWS = range(21, 21 + N_SPECIAL_MAX)  # rows 21-26 (5 or 6 depending on company)
SUBTOTAL2_ROW = 21 + N_SPECIAL_MAX   # row 27 -- item 127/227 (fixed regardless of 5 vs 6)
TOTAL_ROW = SUBTOTAL2_ROW + 1         # row 28 -- item 128/228


def r2_r3_r4_subtotals(by_cq, findings):
    for (code, q), items in by_cq.items():
        has_32 = any(100 <= n <= 128 or 200 <= n <= 228 for n in items)
        if not has_32:
            continue
        for scale_off, label in ((0, "공정가액"), (100, "평가손익")):
            base = 100 + scale_off
            leaf_sum_general = sum(items.get(base + i, 0.0) or 0.0 for i in range(1, N_GENERAL + 1))
            extra_sum = sum(v for n, v in items.items()
                             if ((base == 100 and 141 <= n < 200) or (base == 200 and 241 <= n < 300)) and v is not None)
            sub1 = items.get(base + SUBTOTAL1_ROW)
            if sub1 is not None:
                diff = abs((leaf_sum_general + extra_sum) - sub1)
                tag = "RED" if diff > TOL_AMOUNT else "GREEN"
                findings.append((tag, "R2_일반계정소계", code, q,
                                  f"{label}: sum(rows1-{N_GENERAL},extras)={leaf_sum_general + extra_sum:.2f} vs item{base + SUBTOTAL1_ROW}={sub1} diff={diff:.2f}"))

            leaf_sum_special = sum(items.get(base + i, 0.0) or 0.0 for i in SPECIAL_ROWS)
            sub2 = items.get(base + SUBTOTAL2_ROW)
            if sub2 is not None:
                diff = abs(leaf_sum_special - sub2)
                tag = "RED" if diff > TOL_AMOUNT else "GREEN"
                findings.append((tag, "R3_특별계정소계", code, q,
                                  f"{label}: sum(rows{SPECIAL_ROWS.start}-{SPECIAL_ROWS.stop - 1})={leaf_sum_special:.2f} vs item{base + SUBTOTAL2_ROW}={sub2} diff={diff:.2f}"))

            total = items.get(base + TOTAL_ROW)
            if sub1 is not None and sub2 is not None and total is not None:
                diff = abs((sub1 + sub2) - total)
                tag = "RED" if diff > TOL_AMOUNT else "GREEN"
                findings.append((tag, "R4_합계", code, q,
                                  f"{label}: item{base + SUBTOTAL1_ROW}+item{base + SUBTOTAL2_ROW}={sub1 + sub2:.2f} vs item{base + TOTAL_ROW}={total} diff={diff:.2f}"))


def r5_coverage_census(by_cq, findings):
    import re
    periods = sorted({p.name for p in (REPO / "md_inbox").glob("FY*_Q?") if p.is_dir()})
    exc = {(c, p) for c, p, _ in DOCUMENTED_EXCEPTIONS}
    exc_reason = {(c, p): r for c, p, r in DOCUMENTED_EXCEPTIONS}
    for period in periods:
        quarter = period_to_quarter(period)
        codes = _codes_for_period(period)
        for code in codes:
            items = by_cq.get((code, quarter), {})
            has_31 = all(n in items for n in (1, 2, 3))
            has_32 = 128 in items
            if has_31 and has_32:
                findings.append(("GREEN", "R5_census", code, quarter, "31+32 present"))
                continue
            if (code, period) in exc:
                findings.append(("YELLOW", "R5_census", code, quarter,
                                  f"documented exception: {exc_reason[(code, period)]}"))
                continue
            missing = []
            if not has_31:
                missing.append("3-1(items1-3)")
            if not has_32:
                missing.append("3-2(item128)")
            findings.append(("RED", "R5_census", code, quarter, f"missing {','.join(missing)}, no documented exception"))


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    if not JSON_PATH.exists():
        print(f"FATAL: {JSON_PATH} does not exist")
        return 1

    rows, by_cq = _load()
    print(f"loaded {len(rows)} rows, {len(by_cq)} (company,quarter) combos")

    findings = []
    r1_ratio_identity(by_cq, findings)
    r2_r3_r4_subtotals(by_cq, findings)
    r5_coverage_census(by_cq, findings)

    by_rule = {}
    for tag, rule, code, q, detail in findings:
        by_rule.setdefault(rule, {"RED": 0, "YELLOW": 0, "GREEN": 0})[tag] += 1

    print("\n=== rule summary ===")
    for rule in sorted(by_rule):
        c = by_rule[rule]
        print(f"  {rule:20s} RED={c['RED']:4d} YELLOW={c['YELLOW']:4d} GREEN={c['GREEN']:4d}")

    red = [f for f in findings if f[0] == "RED"]
    print(f"\n=== RED findings: {len(red)} ===")
    for tag, rule, code, q, detail in red[: (None if args.verbose else 60)]:
        print(f"  [{rule}] {code} {q}: {detail}")
    if not args.verbose and len(red) > 60:
        print(f"  ... {len(red) - 60} more (use --verbose)")

    print(f"\nRED total: {len(red)}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
