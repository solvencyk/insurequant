"""Fill missing 항목번호 27 (지급여력비율) and 28 (기본자본비율) rows.

Convention:
  - 27 = 항목1 (지급여력금액) / 항목14 (지급여력기준금액) × 100
  - 28 = 항목2 (기본자본)       / 항목14 (지급여력기준금액) × 100

For every (company, period) bucket where 27 is missing but both 1 and 14
exist, we synthesise a 27 row. Same for 28 (needs 2 and 14). Buckets that
lack the required inputs are reported and left untouched.

Existing 27/28 rows are NEVER overwritten - only missing rows get filled.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

JSON_PATH = Path(r"C:\Users\sangwook.cho\Desktop\solvency\kics_disclosure.json")

# Canonical item names (taken from existing rows so we re-emit identically).
ITEM_NAMES = {
    27: "다. 지급여력비율 : 가 ÷ 라 × 100",
    28: "기본자본비율",
}


def _to_float(s: str) -> float:
    """Parse a stored value string: supports '1,234', '(123)' for negatives."""
    s = s.strip()
    if not s:
        raise ValueError("empty value")
    s = s.replace(",", "")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    v = float(s)
    return -v if neg else v


def _format_ratio(x: float) -> str:
    """Match existing convention - up to 4 decimal places, trim trailing zeros."""
    s = f"{x:.4f}"
    # trim trailing zeros / trailing dot
    s = s.rstrip("0").rstrip(".") if "." in s else s
    return s or "0"


def main() -> int:
    with JSON_PATH.open(encoding="utf-8") as f:
        data: list[dict] = json.load(f)

    # Group rows by (company_code, period) -> {item_no: row}
    buckets: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
    for row in data:
        buckets[(row["원보험사코드"], row["공시분기"])][row["항목번호"]] = row

    # Pre-compute canonical item names from existing rows (use most common form).
    name_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in data:
        name_counts[row["항목번호"]][row["항목명"]] += 1
    for item_no in (27, 28):
        if name_counts[item_no]:
            ITEM_NAMES[item_no] = max(
                name_counts[item_no].items(), key=lambda kv: kv[1]
            )[0]

    new_rows: list[dict] = []
    skipped_27: list[tuple[str, str, str]] = []
    skipped_28: list[tuple[str, str, str]] = []

    for (code, period), items in sorted(buckets.items()):
        # peer row for metadata (use item 1 if present, else any row)
        meta_src = items.get(1) or items.get(2) or items.get(14) or next(iter(items.values()))

        def _new_row(item_no: int, value_str: str) -> dict:
            return {
                "원보험사코드": meta_src["원보험사코드"],
                "원수사명": meta_src["원수사명"],
                "티커": meta_src["티커"],
                "생손보여부": meta_src["생손보여부"],
                "항목번호": item_no,
                "항목명": ITEM_NAMES[item_no],
                "공시분기": meta_src["공시분기"],
                "값": value_str,
            }

        # Item 27: 가(1) / 라(14) × 100
        if 27 not in items:
            if 1 in items and 14 in items:
                try:
                    a = _to_float(items[1]["값"])
                    b = _to_float(items[14]["값"])
                    if b == 0:
                        skipped_27.append((code, period, "denominator(14)=0"))
                    else:
                        new_rows.append(_new_row(27, _format_ratio(a / b * 100)))
                except ValueError as exc:
                    skipped_27.append((code, period, f"parse_error:{exc}"))
            else:
                missing = [n for n in (1, 14) if n not in items]
                skipped_27.append((code, period, f"missing_inputs:{missing}"))

        # Item 28: 기본자본(2) / 라(14) × 100
        if 28 not in items:
            if 2 in items and 14 in items:
                try:
                    a = _to_float(items[2]["값"])
                    b = _to_float(items[14]["값"])
                    if b == 0:
                        skipped_28.append((code, period, "denominator(14)=0"))
                    else:
                        new_rows.append(_new_row(28, _format_ratio(a / b * 100)))
                except ValueError as exc:
                    skipped_28.append((code, period, f"parse_error:{exc}"))
            else:
                missing = [n for n in (2, 14) if n not in items]
                skipped_28.append((code, period, f"missing_inputs:{missing}"))

    if not new_rows:
        print("Nothing to fill.")
        return 0

    # Backup
    backup = JSON_PATH.with_suffix(
        JSON_PATH.suffix + f".bak_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    )
    shutil.copy2(JSON_PATH, backup)
    print(f"Backup -> {backup.name}")

    data.extend(new_rows)
    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    added_27 = sum(1 for r in new_rows if r["항목번호"] == 27)
    added_28 = sum(1 for r in new_rows if r["항목번호"] == 28)
    print()
    print(f"Added rows: {len(new_rows)}  (27: {added_27}, 28: {added_28})")
    print(f"Skipped 27: {len(skipped_27)}; Skipped 28: {len(skipped_28)}")
    if skipped_27:
        print("\nUnable to derive 27:")
        for code, period, why in skipped_27:
            print(f"  {code} {period}: {why}")
    if skipped_28:
        print("\nUnable to derive 28:")
        for code, period, why in skipped_28:
            print(f"  {code} {period}: {why}")

    print()
    print("Sample new 27 rows:")
    for r in [x for x in new_rows if x["항목번호"] == 27][:6]:
        print(f"  {r['원보험사코드']} {r['공시분기']} = {r['값']}")
    print("Sample new 28 rows:")
    for r in [x for x in new_rows if x["항목번호"] == 28][:6]:
        print(f"  {r['원보험사코드']} {r['공시분기']} = {r['값']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
