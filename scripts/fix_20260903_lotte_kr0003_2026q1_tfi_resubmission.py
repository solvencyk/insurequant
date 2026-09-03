# -*- coding: utf-8 -*-
"""One-off patch: KR0003(롯데손해보험) 2026.1Q TFI table (items 47-52) -- re-submitted
filing correction.

## What happened

`data/disclosure/FY2026_Q1/raw/KR0003_롯데손해보험.pdf` was replaced 2026-09-03 (orchestrator)
with the issuer's re-submitted filing (`...재제출.pdf`, zip-internal timestamp 2026-06-02
17:09, 1,927,066 bytes). The prior "최종 제출_20260528.pdf" (886,240 bytes, zip-internal
2026-05-29 16:41) is now archived at
`data/_archive/20260903T015112Z/disclosure_superseded_20260528/`.

In the superseded filing, the "(1) 공통적용 경과조치 관련" TFI detail table (items 47-52,
raw p22) was a byte-for-byte reprint of the PRIOR quarter's (2025.4Q) TFI table -- an issuer
error. `scripts/validate_kics_disclosure.py`'s `_TIER2_ISSUER_INCONSISTENT[("KR0003",
"2026.1Q")]` documented that error and exempted the resulting 5 RED findings.

The re-submitted filing fixes it: the TFI table on p22 now matches the current quarter (its
own 지급여력금액 2,695,532백만원 = 26,955.32억 now equals headline item1=26,955). Re-parsed
2026-09-03 via `run_harness.py --stage parse` (docling, confidence 0.85) + cross-checked
directly against raw PDF text (fitz, p21-p22) -- both extractions agree exactly, and also
match `fill_tfi_table_to_disclosure.py --period FY2026_Q1 --verbose`'s dry-run candidate
values (script declines to overwrite existing cells by policy, so this script does the write
it would otherwise refuse).

## Values (raw p22, 단위: 백만원 -> /100 -> 억원)

    구분                    경과조치 적용 전    경과조치 적용 후
    지급여력금액             2,695,532          2,695,532        (item52)
    기본자본                  (396,229)          (350,858)        (item50)
    보완자본                 3,091,761          3,046,391        (item51)
    보완자본 한도 적용 전       824,718            469,814        (item47)
    보완자본 한도            1,021,614          1,021,614        (item48)
    해약환급금...초과분       2,267,042          2,267,042        (item49)

items 53/54 (기발행 신종자본증권 45,370 / 후순위채무 211,136) are UNCHANGED from the master's
current values -- the re-submitted table prints the identical bond balances (no
redemption/issuance in the quarter; independently corroborated 2026-09-01 for item53 by the
owner-directed re-review already in the exemption comment). Not touched by this script.

## Overwrite policy

This is a correction of stale-but-present cells, not a fresh fill -- so unlike
`fill_tfi_table_to_disclosure.py` (additive-only by design), this script DOES overwrite the
existing 값/값_적용후 on exactly the 6 (item_no) rows below, only for (KR0003, 2026.1Q). It
asserts each target row exists with the expected STALE value before writing (fails loudly if
the master already moved), backs up the file once, and reloads immediately before writing to
avoid clobbering a concurrent session's unrelated edits elsewhere in the same 25k-row file.

Usage: python scripts/fix_20260903_lotte_kr0003_2026q1_tfi_resubmission.py [--apply]
(dry-run by default; prints old -> new for each target row).
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"

CODE = "KR0003"
QUARTER = "2026.1Q"

# item_no -> (expected_existing_pre, expected_existing_post_or_None, new_pre, new_post_or_None)
TARGETS: dict[int, tuple[str, str | None, str, str | None]] = {
    47: ("8366.25", "5801.18", "8247.18", "4698.14"),
    48: ("10335.34", "10335.34", "10216.14", "10216.14"),
    49: ("21567.39", "21567.39", "22670.42", "22670.42"),
    50: ("-3875.14", "-3421.44", "-3962.29", "-3508.58"),
    51: ("29933.63", "29479.93", "30917.61", "30463.91"),
    52: ("26058.5", "26058.5", "26955.32", "26955.32"),
}


def main(argv: list[str]) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows from {JSON_PATH}")

    index: dict[int, dict] = {}
    for r in rows:
        if r.get("원보험사코드") == CODE and r.get("공시분기") == QUARTER and r.get("항목번호") in TARGETS:
            index[r["항목번호"]] = r

    missing = sorted(set(TARGETS) - set(index))
    if missing:
        print(f"ABORT: rows missing for {CODE} {QUARTER} items {missing}")
        return 1

    problems = []
    for item_no, (exp_pre, exp_post, new_pre, new_post) in sorted(TARGETS.items()):
        row = index[item_no]
        cur_pre = row.get("값")
        cur_post = row.get("값_적용후")
        if cur_pre != exp_pre or cur_post != exp_post:
            problems.append(
                f"item{item_no}: expected existing (pre={exp_pre!r}, post={exp_post!r}) "
                f"but master has (pre={cur_pre!r}, post={cur_post!r}) -- master moved since "
                "this script was written, refusing to guess"
            )
    if problems:
        print("ABORT: existing values don't match expected stale baseline:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"\n=== {CODE} {QUARTER}: planned changes ({len(TARGETS)} rows) ===")
    for item_no, (exp_pre, exp_post, new_pre, new_post) in sorted(TARGETS.items()):
        print(f"  item{item_no}: 값 {exp_pre!r} -> {new_pre!r}   값_적용후 {exp_post!r} -> {new_post!r}")

    if not args.apply:
        print("\n(dry-run; no write -- pass --apply to write)")
        return 0

    # Reload immediately before writing (shared working tree -- other sessions may have
    # touched unrelated rows of this same file since the load above).
    fresh_rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if len(fresh_rows) != len(rows):
        print(f"NOTE: row count changed since load ({len(rows)} -> {len(fresh_rows)}); re-resolving targets by key.")
    fresh_index: dict[int, dict] = {}
    for r in fresh_rows:
        if r.get("원보험사코드") == CODE and r.get("공시분기") == QUARTER and r.get("항목번호") in TARGETS:
            fresh_index[r["항목번호"]] = r
    fresh_missing = sorted(set(TARGETS) - set(fresh_index))
    if fresh_missing:
        print(f"ABORT: rows missing on fresh reload for items {fresh_missing}")
        return 1
    fresh_problems = []
    for item_no, (exp_pre, exp_post, new_pre, new_post) in sorted(TARGETS.items()):
        row = fresh_index[item_no]
        if row.get("값") != exp_pre or row.get("값_적용후") != exp_post:
            fresh_problems.append(item_no)
    if fresh_problems:
        print(f"ABORT: fresh reload no longer matches expected baseline for items {fresh_problems} -- someone else wrote these cells, refusing to clobber")
        return 1

    backup_path = JSON_PATH.with_name(JSON_PATH.name + ".bak_pre_lotte_tfi_resubmission_fix")
    if not backup_path.exists():
        backup_path.write_text(JSON_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"backup written: {backup_path}")

    for item_no, (exp_pre, exp_post, new_pre, new_post) in TARGETS.items():
        row = fresh_index[item_no]
        row["값"] = new_pre
        if new_post is not None:
            row["값_적용후"] = new_post
        elif "값_적용후" in row:
            del row["값_적용후"]

    JSON_PATH.write_text(json.dumps(fresh_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\napplied {len(TARGETS)} cell updates to {len(fresh_rows)} rows total (row count unchanged: {len(fresh_rows) == len(rows)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
