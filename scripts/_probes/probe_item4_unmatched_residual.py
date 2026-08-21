"""For (code, quarter) buckets where item4 vs raw MD couldn't be auto-compared
(no md_path mapped, or label match failed), check whether item4 still equals
sum(children) exactly -- i.e. whether the tautology fingerprint survives in
cells my main sweep couldn't verify against raw text.
"""
from __future__ import annotations
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
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

    unmatched_tautology = []
    unmatched_clean = []
    for (code, q), items in buckets.items():
        r4 = items.get(4)
        if r4 is None:
            continue
        cur_val = _to_float(r4.get(KEY_VAL))
        if cur_val is None:
            continue

        comp_total = 0.0
        n_present = 0
        for n in range(5, 12):
            rn = items.get(n)
            v = _to_float(rn.get(KEY_VAL)) if rn is not None else None
            if v is not None:
                comp_total += v
                n_present += 1
        if n_present < 2:
            continue
        is_tautology = abs(cur_val - comp_total) < 1e-6

        item_name = r4.get(KEY_INAME)
        md_path = md_path_for.get((code, q))
        matched = False
        raw_val = None
        if md_path is not None:
            try:
                table = extract_kics_detail_rows(md_path.read_text(encoding="utf-8"), q)
            except Exception:
                table = None
            if table:
                lookup, core = build_label_lookups(table)
                raw_val = match_baseline_value_or_zero(item_name, lookup, core, table)
                matched = raw_val is not None

        if matched:
            continue  # already handled by the main sweep

        entry = {"code": code, "quarter": q, "master_item4": cur_val,
                 "sum_children": comp_total, "n_children": n_present,
                 "has_md_file": md_path is not None}
        if is_tautology:
            unmatched_tautology.append(entry)
        else:
            unmatched_clean.append(entry)

    print(f"unmatched buckets where item4 == sum(children) EXACTLY "
          f"(tautology fingerprint, unverified against raw): {len(unmatched_tautology)}")
    for e in unmatched_tautology:
        print(" ", e)
    print(f"\nunmatched buckets where item4 != sum(children) "
          f"(natural residual, likely fine): {len(unmatched_clean)}")
    for e in unmatched_clean[:10]:
        print(" ", e)


if __name__ == "__main__":
    main()
