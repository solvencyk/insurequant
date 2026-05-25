"""Add FY2025_Q4 rows to kics_disclosure.json from md_inbox parses."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from solvency.parser.kics_baseline_match import match_baseline_value_or_zero
from solvency.parser.kics_disclosure_parser import (
    build_label_lookups,
    extract_kics_detail_rows,
)

JSON_PATH = REPO / "kics_disclosure.json"
MD_DIR = REPO / "md_inbox" / "FY2025_Q4"

TARGET_QUARTER = "2025.4Q"
BASELINE_QUARTER = "2025.3Q"


def _build_company_baseline(rows: list[dict]) -> dict[str, list[dict]]:
    bucket: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("공시분기") == BASELINE_QUARTER:
            bucket[r["원보험사코드"]].append(r)
    return bucket


NEW_COMPANIES: dict[str, tuple[str, str, str]] = {
    "KR0029": ("AIG손해보험", "60", "손해보험"),
    "KR0080": ("AIA생명", "70", "생명보험"),
    "KR0097": ("하나생명보험", "70", "생명보험"),
    "KR0099": ("KB라이프생명", "70", "생명보험"),
    "KR0150": ("서울보증보험", "60", "손해보험"),
    "KR1000": ("코리안리재보험", "60", "손해보험"),
    "KR1010": ("교보라이프플래닛생명보험", "70", "생명보험"),
    "KR1011": ("IBK연금보험", "70", "생명보험"),
    "KR1098": ("카카오페이손해보험", "60", "손해보험"),
}


def _synthesise_baseline(rows: list[dict], code: str) -> list[dict]:
    info = NEW_COMPANIES.get(code)
    if not info:
        return []
    name, ticker, kind = info
    template_code = "KR0001" if kind == "손해보험" else "KR0068"
    template = [
        r
        for r in rows
        if r["원보험사코드"] == template_code and r["공시분기"] == BASELINE_QUARTER
    ]
    return [
        {
            "원보험사코드": code,
            "원수사명": name,
            "티커": ticker,
            "생손보여부": kind,
            "항목번호": t["항목번호"],
            "항목명": t["항목명"],
            "공시분기": BASELINE_QUARTER,
            "값": "",
        }
        for t in template
    ]


def _delete_stale_kr0005_q4(rows: list[dict]) -> int:
    keep: list[dict] = []
    removed = 0
    for r in rows:
        if (
            r.get("원보험사코드") == "KR0005"
            and r.get("공시분기") == TARGET_QUARTER
            and r.get("항목번호") in range(18, 27)
        ):
            removed += 1
        else:
            keep.append(r)
    rows[:] = keep
    return removed


def fill_company(
    md_path: Path,
    baseline: list[dict],
    index: dict[tuple[str, int, str], dict],
    refresh: bool,
) -> tuple[list[dict], int, int, int]:
    md = md_path.read_text(encoding="utf-8")
    table = extract_kics_detail_rows(md, TARGET_QUARTER)
    if not table:
        return [], 0, 0, len(baseline)

    lookup, core_lookup = build_label_lookups(table)
    new_rows: list[dict] = []
    updated = 0
    missed = 0
    for base in baseline:
        item_name = base["항목명"]
        code = base["원보험사코드"]
        item_no = base["항목번호"]
        value = match_baseline_value_or_zero(item_name, lookup, core_lookup, table)
        if value is None:
            missed += 1
            continue
        key = (code, item_no, item_name)
        existing = index.get(key)
        if existing is not None:
            if refresh and existing.get("값") != value:
                existing["값"] = value
                updated += 1
        else:
            new_row = {
                "원보험사코드": code,
                "원수사명": base["원수사명"],
                "티커": base["티커"],
                "생손보여부": base["생손보여부"],
                "항목번호": item_no,
                "항목명": item_name,
                "공시분기": TARGET_QUARTER,
                "값": value,
            }
            index[key] = new_row
            new_rows.append(new_row)
    return new_rows, len(new_rows) + updated, updated, missed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    removed = _delete_stale_kr0005_q4(rows)
    baselines = _build_company_baseline(rows)
    index: dict[tuple[str, int, str], dict] = {}
    for r in rows:
        if r.get("공시분기") == TARGET_QUARTER:
            index[(r["원보험사코드"], r["항목번호"], r["항목명"])] = r

    all_new: list[dict] = []
    total_updated = 0
    for md_path in sorted(MD_DIR.glob("*.md")):
        code = md_path.stem.split("_", 1)[0]
        baseline = baselines.get(code) or _synthesise_baseline(rows, code)
        if not baseline:
            continue
        new_rows, _matched, upd, _miss = fill_company(
            md_path, baseline, index, args.refresh
        )
        total_updated += upd
        all_new.extend(new_rows)

    print(f"removed_stale={removed} inserted={len(all_new)} updated={total_updated}")
    if args.dry_run:
        return 0
    rows.extend(all_new)
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
