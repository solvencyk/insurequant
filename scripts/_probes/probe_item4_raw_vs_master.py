"""Compare item4 (Section I net assets) as extracted fresh from md_inbox
raw-source tables against the current kics_disclosure.json master value.

This re-runs the SAME label-matching extraction used at ingest time
(extract_kics_detail_rows + match_baseline_value_or_zero) targeting item4's
OWN row -- it does not sum children. Read-only; writes a JSON report.
"""
from __future__ import annotations
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero
from solvency.parser.kics_disclosure_parser import build_label_lookups, extract_kics_detail_rows

JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_INAME = "항목명"
KEY_Q = "공시분기"
KEY_VAL = "값"
KEY_POST = "값_적용후"


def _to_float(raw):
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _md_period_to_quarter(period):
    import re
    m = re.match(r"^FY(\d{4})_Q([1-4])$", period)
    return f"{m.group(1)}.{m.group(2)}Q"


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    buckets = defaultdict(dict)
    for r in rows:
        it = r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        buckets[(r.get(KEY_CODE), r.get(KEY_Q))][it] = r

    # map (code, quarter) -> md path
    md_path_for = {}
    for period_dir in sorted(MD_INBOX.glob("FY*_Q?")):
        if not period_dir.is_dir():
            continue
        try:
            q = _md_period_to_quarter(period_dir.name)
        except Exception:
            continue
        for md_path in sorted(period_dir.glob("*.md")):
            code = md_path.stem.split("_", 1)[0]
            md_path_for[(code, q)] = md_path

    results = []
    no_md = []
    no_row_match = []
    for (code, q), items in buckets.items():
        r4 = items.get(4)
        if r4 is None:
            continue
        cur_val = _to_float(r4.get(KEY_VAL))
        if cur_val is None:
            continue
        item_name = r4.get(KEY_INAME)
        md_path = md_path_for.get((code, q))
        if md_path is None:
            no_md.append({"code": code, "quarter": q})
            continue
        try:
            md_text = md_path.read_text(encoding="utf-8")
        except Exception as e:
            no_md.append({"code": code, "quarter": q, "error": str(e)})
            continue
        table = extract_kics_detail_rows(md_text, q)
        if not table:
            no_row_match.append({"code": code, "quarter": q, "reason": "empty table"})
            continue
        lookup, core = build_label_lookups(table)
        raw_val = match_baseline_value_or_zero(item_name, lookup, core, table)
        if raw_val is None:
            no_row_match.append({"code": code, "quarter": q, "reason": "label not matched"})
            continue
        raw_f = _to_float(raw_val)

        # children sum (rule2 semantics: missing = 0)
        comp_total = 0.0
        comp_present = 0
        for n in range(5, 12):
            rn = items.get(n)
            v = _to_float(rn.get(KEY_VAL)) if rn is not None else None
            if v is not None:
                comp_total += v
                comp_present += 1

        results.append({
            "code": code,
            "quarter": q,
            "md_path": str(md_path.relative_to(REPO)),
            "master_item4": cur_val,
            "raw_item4": raw_f,
            "sum_children": comp_total,
            "children_present_count": comp_present,
            "master_eq_raw": (raw_f is not None and abs(cur_val - raw_f) < 1e-6),
            "master_eq_children": abs(cur_val - comp_total) < 1e-6,
            "raw_eq_children": (raw_f is not None and abs(raw_f - comp_total) < 1e-6),
        })

    diffs = [r for r in results if not r["master_eq_raw"]]
    tautology_confirmed = [
        r for r in diffs
        if r["master_eq_children"] and not r["raw_eq_children"]
    ]
    unclassified = [r for r in diffs if r not in tautology_confirmed]

    report = {
        "total_buckets_with_item4": len(results),
        "same_as_raw": len(results) - len(diffs),
        "different_from_raw": len(diffs),
        "tautology_confirmed": len(tautology_confirmed),
        "unclassified_diffs": len(unclassified),
        "no_md_found": no_md,
        "no_row_match": no_row_match,
        "tautology_confirmed_cells": tautology_confirmed,
        "unclassified_diff_cells": unclassified,
    }

    out = sys.argv[1] if len(sys.argv) > 1 else None
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"wrote {out}: total={len(results)} same={len(results)-len(diffs)} "
              f"diff={len(diffs)} tautology_confirmed={len(tautology_confirmed)} "
              f"unclassified={len(unclassified)} no_md={len(no_md)} no_match={len(no_row_match)}")
    else:
        print(text)


if __name__ == "__main__":
    main()
