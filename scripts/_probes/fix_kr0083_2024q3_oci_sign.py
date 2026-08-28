#!/usr/bin/env python3
"""Cell-level fix: inbox/parser/20260828T1200Z (KR0083 2024.3Q DART FS-API sign reversal).

Flips the SIGN of `값` (cumulative) for exactly 3 rows in data/dart/viz/pl_breakdown_master.json
(items 27/28/30, KR0083, "2024.3Q") -- confirmed against raw XML by the orchestrator ticket AND
independently re-derived here (see census_dart_sign_reversal.py). `값_당분기` is untouched here;
it does not even exist as a field in this file (only the derived root PL_breakdown.json has it,
regenerated separately by build_root_masters.build_pl()).

Does NOT touch any other row. Does NOT rerun the extractor/builder (raw discovery on this branch
is broad and a full rebuild is out of scope for a 3-cell fix per the ticket + SKILL.md trap #1).

Usage:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/fix_kr0083_2024q3_oci_sign.py
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json"

# (item, expected_current_값 [wrong sign, as verified 2026-08-28], corrected_값 [raw XML sign])
FIXES = {
    27: (265226.939791, -265226.939791),
    28: (5322.135208, -5322.135208),
    30: (536.616012, -536.616012),
}
CODE, QUARTER = "KR0083", "2024.3Q"


def main():
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    n_before = len(rows)
    changed = []
    for r in rows:
        if r["원보험사코드"] != CODE or r["공시분기"] != QUARTER:
            continue
        item = r["항목번호"]
        if item not in FIXES:
            continue
        expected_wrong, corrected = FIXES[item]
        cur = r["값"]
        if cur is not None and abs(cur - corrected) < 1e-6:
            print(f"  item{item}: already corrected ({cur}) -- skipping (idempotent)")
            continue
        if cur is None or abs(cur - expected_wrong) > 1e-6:
            raise SystemExit(
                f"ABORT: item{item} 값={cur!r} does not match the expected wrong value "
                f"{expected_wrong!r} (nor the corrected value) -- refusing to guess, the on-disk "
                f"file has moved since this script was written. Re-verify before patching."
            )
        r["값"] = corrected
        changed.append((item, cur, corrected))

    if len(changed) != 3 and not all(
        abs(r2["값"] - FIXES[r2["항목번호"]][1]) < 1e-6
        for r2 in rows
        if r2["원보험사코드"] == CODE and r2["공시분기"] == QUARTER and r2["항목번호"] in FIXES
    ):
        raise SystemExit(f"ABORT: expected to touch 3 rows, touched {len(changed)}: {changed}")

    n_after = len(rows)
    assert n_after == n_before, f"row count changed {n_before} -> {n_after}, aborting write"

    if changed:
        MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {MASTER} ({n_after} rows, unchanged count)")
    else:
        print("nothing to do (all 3 cells already corrected)")

    for item, old, new in changed:
        print(f"  {CODE} {QUARTER} item{item}: {old} -> {new}")


if __name__ == "__main__":
    main()
