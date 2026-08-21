# -*- coding: utf-8 -*-
"""UPSERT fix (2026-08-21) — 5 REDs from INTERNAL_MODEL_36IRR_EXEMPT disproof (KICS_36_irr):
loads items 41-46 (금리위험 순자산가치 6-scenario) for 교보생명 2025.2Q + 신한라이프 2024.2Q/
2024.4Q/2025.2Q/2025.4Q from raw (당기/current-period column only — verified against the
comparative/전기 column to avoid the known column-confusion trap). Also fixes 1 RED from
_POST_PARENT_NOT_DISCLOSED disproof (POST_TRANSITION_PARENT_MISSING): 하나생명 KR0097 2024.4Q
item16/17 값_적용후, sourced directly from raw p281 [지급여력기준금액] table (경과조치 적용후
column is disclosed outright, not derived).

Raw sources (all verified directly via scripts/_probes/dump_pages_20260821.py, cross-checked
against a second independent table in the same filing where available — see inbox reply
inbox/parser/20260821T1600Z and 20260821T1620Z for full citations):
  KR0073 2025.2Q  data/disclosure/FY2025_Q2/raw/KR0073_교보생명보험.pdf            p21 (당기, 백만원)
  KR0094 2024.2Q  data/disclosure/FY2024_Q2/raw/KR0094_신한라이프생명보험.pdf      p22 (당기, 백만원)
  KR0094 2024.4Q  data/disclosure/FY2024_Q4/raw/KR0094_신한라이프생명보험.pdf      p101(당기말,천원)+p144(당기,백만원xcheck)
  KR0094 2025.2Q  data/disclosure/FY2025_Q2/raw/KR0094_신한라이프생명보험.pdf      p28 (당기, 백만원)
  KR0094 2025.4Q  data/disclosure/FY2025_Q4/raw/KR0094_신한라이프생명보험.pdf      p95 (당기말,천원)+p131(당기,백만원xcheck)
  KR0097 2024.4Q  data/disclosure/FY2024_Q4/raw/KR0097_하나생명보험.pdf            p281 [지급여력기준금액]

Sign/unit convention: 억원, 2-decimal (matches existing item36/41-46 rows e.g. KR0001 2023.2Q).
값_적용후 mirrors 값 for items 41-46: both companies fall outside (or, for KR0073, elected only
"IR","EQ" not "INT" per _TRANSITION_KIND) the 금리위험(INT) selective-transition axis, so 후=전
is the correct/expected relationship for this axis (matches item36's existing 값_적용후=값
mirror already in the master, and matches the established convention for other non-elected-axis
companies e.g. KR0001 above).

Idempotent UPSERT (safe re-run): match on (원보험사코드, 공시분기, 항목번호); update in place if
found, append using the neighboring-row schema if not. Whole-list read-modify-write is
unavoidable for a JSON array on disk, but the mutation itself touches only the listed cells —
this is NOT a call into build_root_masters.py / any batch builder.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_NAME = "원수사명"
KEY_TICKER = "티커"
KEY_TYPE = "생손보여부"
KEY_ITEM = "항목번호"
KEY_ITEM_NAME = "항목명"
KEY_QUARTER = "공시분기"
KEY_VALUE = "값"
KEY_VALUE_POST = "값_적용후"

ITEM_NAMES = {
    41: "3-1-0. 금리위험 순자산가치(충격전)",
    42: "3-1-1. 금리위험 순자산가치(평균회귀)",
    43: "3-1-2. 금리위험 순자산가치(금리상승)",
    44: "3-1-3. 금리위험 순자산가치(금리하락)",
    45: "3-1-4. 금리위험 순자산가치(금리평탄)",
    46: "3-1-5. 금리위험 순자산가치(금리경사)",
}

# code -> name/ticker/type (from existing item36 rows, reused so new rows match neighbors)
COMPANY_META = {
    "KR0073": ("교보생명보험", "X", "생명보험"),
    "KR0094": ("신한라이프생명보험", "X", "생명보험"),
}

# (code, quarter) -> {item: value_str}  (값_적용후 mirrors 값 for all of these — see docstring)
IRR_FIXES: dict[tuple[str, str], dict[int, str]] = {
    ("KR0073", "2025.2Q"): {
        41: "-56677.11", 42: "-54149.04", 43: "-63523.38",
        44: "-55868.99", 45: "-54631.38", 46: "-57420.51",
    },
    ("KR0094", "2024.2Q"): {
        41: "83261.56", 42: "83612.77", 43: "78623.16",
        44: "84055.36", 45: "78616.47", 46: "87681.84",
    },
    ("KR0094", "2024.4Q"): {
        41: "83189.35", 42: "83520.02", 43: "79993.16",
        44: "81808.19", 45: "79291.45", 46: "86897.18",
    },
    ("KR0094", "2025.2Q"): {
        41: "73407.00", 42: "74330.20", 43: "75124.74",
        44: "64813.82", 45: "69255.77", 46: "76923.21",
    },
    ("KR0094", "2025.4Q"): {
        41: "62419.44", 42: "63310.93", 43: "62796.73",
        44: "57197.61", 45: "59854.75", 46: "64637.59",
    },
}

# Expected pre-existing item36 (전=후, sanity cross-check only — script does not write item36)
EXPECTED_ITEM36 = {
    ("KR0073", "2025.2Q"): "4599.88",
    ("KR0094", "2024.2Q"): "7501.04",
    ("KR0094", "2024.4Q"): "6332.14",
    ("KR0094", "2025.2Q"): "9318.33",
    ("KR0094", "2025.4Q"): "5789.99",
}

# 하나생명 KR0097 2024.4Q — POST_TRANSITION_PARENT_MISSING fix (raw p281, 천원->억원 /100000)
HANA_FIX = {
    "code": "KR0097",
    "quarter": "2024.4Q",
    16: "1613.67",   # NEW key (raw (161,367,358)천원 = 1613.67358억, 분산효과=children-parent convention)
    17: "2001.90",   # CORRECTED from 1757.32 (raw 200,189,811천원 = 2001.89811억)
}


def load() -> list[dict]:
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def save(data: list[dict]) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")  # normalize -> CRLF (match on-disk convention)
    with open(JSON_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def find_row(data, code, quarter, item):
    for r in data:
        if r.get(KEY_CODE) == code and r.get(KEY_QUARTER) == quarter and r.get(KEY_ITEM) == item:
            return r
    return None


def main():
    data = load()
    print(f"loaded {len(data)} rows from {JSON_PATH}")

    census = []  # (label, before, after)
    inserted = 0
    updated = 0

    # --- Part A: 36_irr items 41-46 ---
    for (code, quarter), items in IRR_FIXES.items():
        name, ticker, styp = COMPANY_META[code]
        # sanity: item36 must already be present & match expectation (we do NOT write it)
        row36 = find_row(data, code, quarter, 36)
        exp36 = EXPECTED_ITEM36[(code, quarter)]
        actual36 = row36.get(KEY_VALUE) if row36 else None
        status36 = "OK" if actual36 == exp36 else f"MISMATCH(expected {exp36})"
        print(f"[sanity] {code} {quarter} item36 = {actual36!r} [{status36}] (not modified)")
        if row36 is None or actual36 != exp36:
            raise SystemExit(f"ABORT: item36 sanity check failed for {code} {quarter}")

        for item, val in items.items():
            row = find_row(data, code, quarter, item)
            label = f"{code} {quarter} item{item} ({ITEM_NAMES[item]})"
            if row is None:
                before = None
                new_row = {
                    KEY_NAME: name,
                    KEY_TICKER: ticker,
                    KEY_TYPE: styp,
                    KEY_CODE: code,
                    KEY_ITEM: item,
                    KEY_ITEM_NAME: ITEM_NAMES[item],
                    KEY_QUARTER: quarter,
                    KEY_VALUE: val,
                    KEY_VALUE_POST: val,
                }
                data.append(new_row)
                inserted += 1
                after = f"값={val} 값_적용후={val} [NEW ROW]"
            else:
                before = f"값={row.get(KEY_VALUE)!r} 값_적용후={row.get(KEY_VALUE_POST)!r}"
                row[KEY_VALUE] = val
                row[KEY_VALUE_POST] = val
                updated += 1
                after = f"값={val} 값_적용후={val}"
            census.append((label, before, after))

    # --- Part B: 하나생명 KR0097 2024.4Q item16/17 값_적용후 ---
    code, quarter = HANA_FIX["code"], HANA_FIX["quarter"]
    for item in (16, 17):
        row = find_row(data, code, quarter, item)
        if row is None:
            raise SystemExit(f"ABORT: expected existing row for {code} {quarter} item{item} not found")
        label = f"{code} {quarter} item{item} ({row.get(KEY_ITEM_NAME)})"
        before = f"값={row.get(KEY_VALUE)!r} 값_적용후={row.get(KEY_VALUE_POST)!r}"
        row[KEY_VALUE_POST] = HANA_FIX[item]
        updated += 1
        after = f"값={row.get(KEY_VALUE)!r} 값_적용후={HANA_FIX[item]!r}"
        census.append((label, before, after))

    print(f"\n=== BEFORE / AFTER CENSUS ({len(census)} cells: {inserted} inserted, {updated} updated) ===")
    for label, before, after in census:
        print(f"  {label}")
        print(f"    before: {before}")
        print(f"    after:  {after}")

    save(data)
    print(f"\nsaved {len(data)} rows ({len(data) - (len(data) - inserted)} net new = {inserted}) to {JSON_PATH}")

    # --- immediate re-read verification (lost-update guard) ---
    data2 = load()
    ok = True
    for (code, quarter), items in IRR_FIXES.items():
        for item, val in items.items():
            row = find_row(data2, code, quarter, item)
            if row is None or row.get(KEY_VALUE) != val or row.get(KEY_VALUE_POST) != val:
                print(f"VERIFY FAIL: {code} {quarter} item{item} -> {row}")
                ok = False
    row16 = find_row(data2, "KR0097", "2024.4Q", 16)
    row17 = find_row(data2, "KR0097", "2024.4Q", 17)
    if row16.get(KEY_VALUE_POST) != "1613.67":
        print(f"VERIFY FAIL: KR0097 2024.4Q item16 -> {row16}")
        ok = False
    if row17.get(KEY_VALUE_POST) != "2001.90":
        print(f"VERIFY FAIL: KR0097 2024.4Q item17 -> {row17}")
        ok = False
    print("VERIFY:", "ALL OK (re-read matches write)" if ok else "MISMATCH DETECTED — investigate concurrent write")


if __name__ == "__main__":
    main()
