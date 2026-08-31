#!/usr/bin/env python3
"""Cell-level fixes for 2 confirmed 금리민감도 RS1/RS2 RED parsing defects (2026-08-31 round).

Both are visually confirmed against the raw source PDF (word-bbox / high-DPI render), not
guessed or interpolated. Cell-level UPSERT only — never rewrites kics_rate_sensitivity.json
wholesale (extract_kics_rate_sensitivity.py already does a full rewrite; this script patches
its output afterward so the fix reproducibly survives review, same pattern as
data/_derived/_patch_2026q2_KR0079.json for the disclosure lane).

FIX 1 — 신한이지손해보험 (KR0051) 2024.4Q, 경과조치 적용전/적용후 (both blocks identical):
  The company's own filed PDF (data/disclosure/FY2024_Q4/raw/KR0051_신한이지손해보험.pdf,
  p.54) prints the 3 measure-rows (지급여력비율/지급여력금액/지급여력기준금액) with the
  구분(label) column rotated one position relative to the value columns — confirmed via
  fitz word-level bbox dump (labels are a separate text block from the numeric grid; visual
  row-matching in the source PDF is off by one). Proof (independent, 3-way):
    1. RS2 anchor: kics_disclosure.json item1=665 / item14=418 / item27=159.09090909
       match the values printed under "지급여력비율"(665)/"지급여력금액"(418)/
       "지급여력기준금액"(159.16) respectively -- i.e. exactly one row off.
    2. Narrative sentence in the same MD section ("50bp 상승시 0.73%p 하락, 하락시 0.76%p
       상승, 100bp 상승시 1.21%p 하락, 하락시 1.46%p 상승") reproduces the series
       (159.16, 158.43, 159.92, 157.95, 160.62) to the exact hundredth -- confirms that
       series (printed under the "지급여력기준금액" label) is the TRUE 지급여력비율 series.
    3. Values are internally coherent within each row (no cross-row noise), consistent with
       a whole-row label/value misalignment rather than random per-cell corruption.
  Fix: re-assign the 3 already-extracted value-series to their true measure label (values
  themselves are untouched, only which "measure구분" row they live under changes), and
  recompute 듀레이션/컨벡서티 for the 2 조건 rows that now do fall in _DC_MEASURES to keep
  the field derivation formula honest (지급여력비율 gets null/null per existing convention).

FIX 2 — KB손해보험 (KR0010) 2026.2Q, 경과조치 적용전/적용후 (both blocks identical on the
  source page too):
  KR0010 is a 100%-scanned filing this quarter (native text layer = 0 chars on every page
  checked; docling frontmatter parse_spec_hash=...+easyocr-ko+allpages, run today
  2026-08-31). EasyOCR mis-read several digits in the 금리 민감도 분석 table (p.47) --
  confirmed by rendering that table region at 6x zoom (~430dpi effective) and reading the
  crisp printed digits directly, which differ from what landed in kics_rate_sensitivity.json
  in exactly the failure mode already flagged for 미래에셋생명(KR0079) this same round
  (digit substitution, e.g. 135,316 -> 135,376 is a single '1'->'7' swap; 72,187 -> 72,787
  same swap; some cells lost their comma-grouping entirely, e.g. printed 73,164 came out as
  "73,7641" in the OCR text and failed/garbled downstream; some cells were dropped to None
  by stray OCR punctuation breaking the parser's numeric regex).
  Corrected values are the literal digits read off the rendered page and are self-consistent
  under RS1 (비율 = 금액/기준금액*100) on all 5 shock columns to within rounding (<=0.01),
  which the corrupted values were not (up to 10x off). See probe scripts:
    scripts/_probes/probe_20260831_kb_p47_crop.py (page locate + 6x render)
    scripts/_probes/kb_p47_crop.png (rendered evidence, still on disk)
  NOTE: kics_disclosure.json item1/14/27/28 for KR0010 2026.2Q are SEPARATELY corrupted
  (item14/27/28 missing entirely; item1=1,553,161 doesn't even satisfy item1=item2+item3
  within kics_disclosure.json itself, let alone match this RS table) -- that is a different
  file/defect or a different table in a different section, out of this script's scope, and is
  NOT touched here. It is reported via inbox and carved out as an RS2 documented exception in
  validate_kics_rate_sensitivity.py (RS2_EXCEPTIONS) pending that separate fix.

Usage: PYTHONIOENCODING=utf-8 python scripts/fix_20260831_ratesens_red_batch.py [--dry-run]
"""
from __future__ import annotations
import argparse
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "kics_rate_sensitivity.json"


def dc(base, dn100, up100):
    """듀레이션/컨벡서티, same formula as extract_kics_rate_sensitivity.py::duration_convexity."""
    if base in (None, 0) or dn100 is None or up100 is None:
        return None, None
    dy = 0.01
    d = -(up100 - dn100) / (2.0 * base * dy)
    c = (up100 + dn100 - 2.0 * base) / (base * dy * dy)
    return round(d, 4), round(c, 2)


# {(원수사명, 공시분기, 경과조치여부, measure구분): {-100bp,-50bp,base,+50bp,+100bp}}
FIXES = {}

# ---- FIX 1: 신한이지손해보험 2024.4Q label rotation (both phases identical) ----
_SHINHAN_TRUE = {
    "지급여력비율": {"-100bp": 160.62, "-50bp": 159.92, "base": 159.16, "+50bp": 158.43, "+100bp": 157.95},
    "지급여력금액": {"-100bp": 679.0, "-50bp": 671.0, "base": 665.0, "+50bp": 661.0, "+100bp": 652.0},
    "지급여력기준금액": {"-100bp": 423.0, "-50bp": 420.0, "base": 418.0, "+50bp": 417.0, "+100bp": 413.0},
}
for phase in ("적용전", "적용후"):
    for meas, vals in _SHINHAN_TRUE.items():
        FIXES[("신한이지손해보험", "2024.4Q", phase, meas)] = dict(vals)

# ---- FIX 2: KB손해보험 2026.2Q OCR digit corruption (both phases identical on source page) ----
_KB_TRUE = {
    "지급여력비율": {"-100bp": 195.26, "-50bp": 192.14, "base": 187.45, "+50bp": 182.33, "+100bp": 176.93},
    "지급여력금액": {"-100bp": 142859.0, "-50bp": 139638.0, "base": 135316.0, "+50bp": 130950.0, "+100bp": 126669.0},
    "지급여력기준금액": {"-100bp": 73164.0, "-50bp": 72674.0, "base": 72187.0, "+50bp": 71821.0, "+100bp": 71591.0},
}
for phase in ("적용전", "적용후"):
    for meas, vals in _KB_TRUE.items():
        FIXES[("KB손해보험", "2026.2Q", phase, meas)] = dict(vals)

_DC_MEASURES = ("지급여력금액", "지급여력기준금액")


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    rows = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    before_n = len(rows)
    before_combos = {(r["원수사명"], r["공시분기"]) for r in rows}

    applied, misses = [], set(FIXES.keys())
    for r in rows:
        key = (r["원수사명"], r["공시분기"], r["경과조치여부"], r["measure구분"])
        if key not in FIXES:
            continue
        new_vals = FIXES[key]
        old_snapshot = {c: r.get(c) for c in ("-100bp", "-50bp", "base", "+50bp", "+100bp")}
        for c, v in new_vals.items():
            r[c] = v
        if r["measure구분"] in _DC_MEASURES:
            d, cvx = dc(new_vals["base"], new_vals["-100bp"], new_vals["+100bp"])
            r["듀레이션"], r["컨벡서티"] = d, cvx
        else:
            r["듀레이션"], r["컨벡서티"] = None, None
        applied.append((key, old_snapshot, new_vals, (r["듀레이션"], r["컨벡서티"])))
        misses.discard(key)

    print(f"rows before={before_n}  after={len(rows)}  (must be equal -- cell edits only)")
    print(f"combos before={len(before_combos)}  after={len({(r['원수사명'], r['공시분기']) for r in rows})}")
    print(f"FIXES defined={len(FIXES)}  applied={len(applied)}  unmatched={len(misses)}")
    for k in sorted(misses):
        print(f"  ! UNMATCHED (no row found for): {k}")
    print()
    for key, old, new, dc_new in applied:
        print(f"  {key}")
        print(f"    old: {old}")
        print(f"    new: {new}  듀레이션/컨벡서티={dc_new}")

    if before_n != len(rows) or before_combos != {(r["원수사명"], r["공시분기"]) for r in rows}:
        print("ABORT: row count or combo set changed -- refusing to write.")
        return 2

    if args.dry_run:
        print("\n(dry-run; no write)")
        return 0

    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
