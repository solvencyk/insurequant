# -*- coding: utf-8 -*-
"""Regression proof (2/2) for inbox ticket 20260901T0430Z: the two call sites that wrap
disclosure_pdfs() with extra logic rather than calling it bare --
audit_all_periods.py::has_disclosure_file (multi-prefix alias loop) and
report_collection_status.py::check_disclosure (directory-existence branch for the note text).

Reconstructs each function's PRE-FIX behavior locally (raw/ only, same matching rule) and
diffs it against the actual (now-patched) live function, for the full 39/40-company universe
x the 13 legacy quarters. Read-only.

Usage: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
           scripts/_probes/verify_20260901_wrapper_functions_no_regression.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from scripts.audit_all_periods import has_disclosure_file, FILE_PREFIX_ALIAS, ALL as AUDIT_ALL  # noqa: E402
from scripts.report_collection_status import check_disclosure, LOSS, LIFE  # noqa: E402

DISCLOSURE = REPO / "data" / "disclosure"
# repo convention counts 13 quarters as FY2023_Q1..FY2026_Q1 inclusive (FY2026_Q1 raw=39
# pdf=1 already matches the pre-2026.2Q pattern per the ticket's own census) -- superset of
# the orchestrator prompt's literal "FY2023_Q1~FY2025_Q4" (12) so this check is strictly wider.
LEGACY_PERIODS = [f"FY{y}_Q{q}" for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)] + ["FY2026_Q1"]


def old_has_disclosure_file(period: str, kr: str) -> bool:
    """Pre-fix body of audit_all_periods.has_disclosure_file (raw/ only)."""
    raw = DISCLOSURE / period / "raw"
    if not raw.exists():
        return False
    prefixes = FILE_PREFIX_ALIAS.get(kr, [kr])
    for f in raw.iterdir():
        if f.is_file() and any(f.name.startswith(pfx + "_") for pfx in prefixes):
            return True
    return False


def old_check_disclosure(period: str, kr: str) -> tuple:
    """Pre-fix body of report_collection_status.check_disclosure (raw/ only)."""
    raw_dir = DISCLOSURE / period / "raw"
    if not raw_dir.exists():
        return ("X", "디렉토리 없음")
    matches = list(raw_dir.glob(f"{kr}_*"))
    if matches:
        return ("O", "")
    return ("X", "미수집")


def run_audit():
    total = flips = 0
    detail = []
    for period in LEGACY_PERIODS:
        for kr, _name in AUDIT_ALL:
            total += 1
            o, n = old_has_disclosure_file(period, kr), has_disclosure_file(period, kr)
            if o != n:
                flips += 1
                detail.append((period, kr, o, n))
    print(f"has_disclosure_file: pairs={total} flips={flips}")
    for d in detail[:20]:
        print(f"  {d}")
    return flips


def run_report():
    total = flips = 0
    detail = []
    universe = LOSS + LIFE
    for period in LEGACY_PERIODS:
        for kr, _name in universe:
            total += 1
            o = old_check_disclosure(period, kr)
            n = check_disclosure(period, kr)
            if o != n:
                flips += 1
                detail.append((period, kr, o, n))
    print(f"check_disclosure: pairs={total} flips={flips}")
    for d in detail[:20]:
        print(f"  {d}")
    return flips


if __name__ == "__main__":
    f1 = run_audit()
    f2 = run_report()
    print(f"\nTOTAL FLIPS (both wrapper functions, legacy 13Q, full universe) = {f1 + f2}")
    raise SystemExit(0 if (f1 + f2) == 0 else 1)
