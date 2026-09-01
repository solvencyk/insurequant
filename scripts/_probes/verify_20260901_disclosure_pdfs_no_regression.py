# -*- coding: utf-8 -*-
"""Regression proof for inbox tickets 20260901T0430Z / 20260901T0500Z (raw-vs-pdf-dir fix).

All 11 scripts flagged in the first ticket now call the SAME shared function,
`scripts/_disclosure_pdf_paths.py::disclosure_pdfs(period, code)`, in place of their old
`sorted((DISCLOSURE/period/"raw").glob(f"{code}_*.pdf"))` (or `glob.glob(str(...))`) one-liner.
So proving the shared function reproduces the OLD raw-only result for every (period, code) pair
that ever had a raw/ hit, across the 13 legacy quarters, proves all 11 call sites are regression-free
simultaneously -- they're calling the identical function with the identical two arguments.

Read-only. Does not touch kics_disclosure.json or any master. Prints counts only.

Usage: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
           scripts/_probes/verify_20260901_disclosure_pdfs_no_regression.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

DISCLOSURE = REPO / "data" / "disclosure"

LEGACY_PERIODS = [f"FY{y}_Q{q}" for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)]
NEW_PERIODS = ["FY2026_Q1", "FY2026_Q2"]


def old_raw_only(period: str, code: str) -> list[Path]:
    """The exact expression every one of the 11 scripts used before this fix."""
    raw = DISCLOSURE / period / "raw"
    if not raw.is_dir():
        return []
    return sorted(raw.glob(f"{code}_*.pdf"))


def codes_seen(period: str) -> set[str]:
    """Union of every code prefix that appears as a file in EITHER raw/ or pdf/ for this
    period -- this is the universe worth diffing (codes with zero files in both dirs trivially
    agree: old=[] new=[])."""
    out = set()
    for sub in ("raw", "pdf"):
        d = DISCLOSURE / period / sub
        if d.is_dir():
            out |= {p.name.split("_", 1)[0] for p in d.glob("*.pdf")}
    return out


def run(periods: list[str], label: str):
    total = 0
    flips = 0
    recovered = 0  # old=[] new=nonempty (expected: pdf-only periods)
    flip_detail = []
    recovered_detail = []
    per_period = {}
    for period in periods:
        codes = sorted(codes_seen(period))
        n_flip = n_rec = 0
        for code in codes:
            old = old_raw_only(period, code)
            new = disclosure_pdfs(period, code)
            total += 1
            old_s = [str(p) for p in old]
            new_s = [str(p) for p in new]
            if old_s == new_s:
                continue
            if not old_s and new_s:
                recovered += 1
                n_rec += 1
                recovered_detail.append((period, code, new_s))
            else:
                flips += 1
                n_flip += 1
                flip_detail.append((period, code, old_s, new_s))
        per_period[period] = (len(codes), n_flip, n_rec)

    print(f"=== {label} ===")
    print(f"pairs checked={total}  flips(old!=new, non-additive)={flips}  "
          f"recovered(old=[] new=nonempty)={recovered}")
    for period in periods:
        n, nf, nr = per_period[period]
        if n or nf or nr:
            print(f"  {period}: codes={n} flips={nf} recovered={nr}")
    if flip_detail:
        print("  FLIP DETAIL (first 20):")
        for ex in flip_detail[:20]:
            print(f"    {ex}")
    if recovered_detail and label != "legacy 13Q (FY2023_Q1..FY2025_Q4)":
        print(f"  recovered companies: {[c for _, c, _ in recovered_detail]}")
    print()
    return flips


if __name__ == "__main__":
    f1 = run(LEGACY_PERIODS, "legacy 13Q (FY2023_Q1..FY2025_Q4)")
    f2 = run(NEW_PERIODS, "FY2026_Q1 / FY2026_Q2 (post-fix expected to gain hits)")
    print(f"TOTAL FLIPS across all periods = {f1 + f2}  (must be 0 for legacy; ok elsewhere)")
    raise SystemExit(0 if f1 == 0 else 1)
