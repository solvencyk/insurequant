"""Restore item4 (Section I net assets) cells that were silently overwritten
by the sum-of-children reconcile logic in fill_period_to_disclosure.py and
recalc_kics_derived.py (inbox 20260821T1505Z item 1 / 20260821T1420Z).

Methodology (raw source, NOT back-solved from children):
  For every (code, quarter) bucket where master item4 == sum(items 5..11)
  EXACTLY (the tautology fingerprint) and master item4 != the value printed
  on item4's own row in the source md_inbox table (re-extracted via the same
  label-match used at ingest time -- extract_kics_detail_rows +
  match_baseline_value_or_zero, targeting item4's OWN row, not summing
  anything), replace item4 with the raw-matched value.

122 such cells were found (see scripts/_probes/probe_item4_raw_vs_master.py).
119 of them are a clean, unambiguous single-column match with |new_raw -
old_children_sum| <= 4 (in practice all but 3 are exactly +-1, pure
99-億원-rounding noise -- rule 2's own tolerance is 2.0, so all 119 land
GREEN/YELLOW, never RED).

3 cells needed individual raw-PDF verification beyond the MD auto-match
(documented per-cell below, all cross-checked against fitz text extraction
of the source PDF, not just docling MD):

  - KR0051 신한이지손해보험 2023.2Q: MD/PDF agree item4=1117 (raw). The
    stored children summed to 1113 (diff +4) because item11(조정준비금) was
    stored as -241 while the SAME raw row prints -237
    (md_inbox/FY2023_Q2/KR0051_신한이지손해보험.md L259). 1481+0-129+0+2-237
    = 1117, exact. Both item4 and item11 corrected from the same raw row.

  - KR0080 에이아이에이생명보험 2023.3Q: MD/PDF agree item4=34896 (raw,
    fitz-confirmed data/disclosure/FY2023_Q3/raw/KR0080_에이아이에이생명보험.pdf
    p9). Stored children summed to 35216 (diff -320) because item7
    (이익잉여금)=12488 vs raw 11977, item9(기타포괄손익누계액)=2193 vs raw
    1487, item11(조정준비금)=5453 vs raw 6350 -- none of the 3 match ANY of
    the table's 3 quarter columns (23.3Q/23.2Q/23.1Q), i.e. they trace to a
    different, unidentified source, not a column-picker off-by-one. Raw:
    15082+0+11977+0+1487+6350 = 34896, exact. item4 + items7/9/11 corrected
    together from the same raw row (same page, same column).

  - KR0003 롯데손해보험 2023.4Q: EXCLUDED from auto-apply. The raw PDF's own
    printed total row reads "2,481" (data/disclosure/FY2023_Q4/raw/
    KR0003_롯데손해보험_amended.pdf p41, confirmed via both docling MD and
    fitz text -- not a docling artifact) but that conflicts with its OWN
    listed components on the SAME row (6390+454+3804+503+1412+12245=24808,
    which also matches master's current items5-11 exactly), with the
    adjacent-quarter trend on the same table (23,548 / 24,056), and with the
    company's own item1 in the SAME column (29,296) -- "2,481" is off by
    ~10x from everything else in its own row and column. This looks like a
    filer-side typo in the total-row cell, not an extraction error. Per
    "wrong value is worse than a blank" and "do not back-solve from
    children" this script does NOT touch item4 for this one cell -- master
    already holds 24808 (which happens to equal both readings that
    cross-validate), so leaving it unchanged is a no-op either way. Flagged
    here for human/validation follow-up, not silently folded into the batch.

Any (code, quarter) whose current item4 값_적용후 exactly mirrors the OLD
(pre-fix) 값 is treated as a live non-applier mirror and updated to the NEW
값 too, to keep the mirror internally consistent (this does not invent a
disclosed post column -- it keeps an existing mirror in sync with the value
it mirrors). Same treatment for items 7/9/11 on the two special cases.

Cell-by-cell UPSERT; prints before/after census. Idempotent: rerunning after
a successful apply finds 0 remaining tautology cells (values now differ from
children-sum by design).
"""
from __future__ import annotations
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
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

EXCLUDE_FROM_AUTOFIX = {("KR0003", "2023.4Q")}  # see module docstring

# Extra same-row corrections discovered while raw-verifying the 3 outliers.
# item -> new value string, read directly off the same raw table row as item4.
SPECIAL_CASE_EXTRA_ITEMS = {
    ("KR0051", "2023.2Q"): {11: "-237"},
    ("KR0080", "2023.3Q"): {7: "11977", 9: "1487", 11: "6350"},
}


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


def find_tautology_cells(rows):
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

    confirmed = []
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
            continue
        table = extract_kics_detail_rows(md_path.read_text(encoding="utf-8"), q)
        if not table:
            continue
        lookup, core = build_label_lookups(table)
        raw_val = match_baseline_value_or_zero(item_name, lookup, core, table)
        if raw_val is None:
            continue
        raw_f = _to_float(raw_val)
        if raw_f is None or abs(cur_val - raw_f) < 1e-6:
            continue  # same as raw already, nothing to do

        comp_total = 0.0
        n_present = 0
        for n in range(5, 12):
            rn = items.get(n)
            v = _to_float(rn.get(KEY_VAL)) if rn is not None else None
            if v is not None:
                comp_total += v
                n_present += 1

        master_eq_children = abs(cur_val - comp_total) < 1e-6
        raw_eq_children = abs(raw_f - comp_total) < 1e-6
        if master_eq_children and not raw_eq_children:
            confirmed.append((code, q, cur_val, raw_val, raw_f, comp_total))
    return confirmed


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    confirmed = find_tautology_cells(rows)
    print(f"tautology-confirmed cells found this run: {len(confirmed)} (expect 122)")
    if len(confirmed) != 122:
        print("WARNING: count drifted from the probed 122 -- proceeding anyway, "
              "review the list below before trusting the summary.")

    by_key = defaultdict(dict)
    for r in rows:
        it = r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        by_key[(r.get(KEY_CODE), r.get(KEY_Q), it)] = r

    pre_changes = []   # (code, q, item, old_val, new_val)
    post_changes = []  # (code, q, item, old_post, new_post)
    skipped = []

    for code, q, cur_val, raw_val, raw_f, comp_total in confirmed:
        if (code, q) in EXCLUDE_FROM_AUTOFIX:
            skipped.append((code, q, cur_val, raw_val, comp_total))
            continue
        item_new_values = {4: raw_val}
        item_new_values.update(SPECIAL_CASE_EXTRA_ITEMS.get((code, q), {}))
        for item_no, new_val_str in item_new_values.items():
            row = by_key.get((code, q, item_no))
            if row is None:
                print(f"  ABORT: {code} {q} item{item_no} row not found")
                sys.exit(1)
            old_val = row.get(KEY_VAL)
            if str(old_val) != str(new_val_str):
                row[KEY_VAL] = new_val_str
                pre_changes.append((code, q, item_no, old_val, new_val_str))
            old_post = row.get(KEY_POST)
            if old_post is not None and _to_float(old_post) is not None and old_val is not None:
                if abs(_to_float(old_post) - _to_float(old_val)) < 1e-6:
                    # was a straight mirror of the (old) pre value -- keep it mirrored
                    if str(old_post) != str(new_val_str):
                        row[KEY_POST] = new_val_str
                        post_changes.append((code, q, item_no, old_post, new_val_str))

    print(f"\npre-column (값) cells changed: {len(pre_changes)}")
    for c in pre_changes:
        print("  ", c)
    print(f"\npost-column (값_적용후) cells re-mirrored: {len(post_changes)}")
    for c in post_changes:
        print("  ", c)
    print(f"\nexcluded from auto-apply (documented, see module docstring): {len(skipped)}")
    for s in skipped:
        print("  ", s)

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(rows)} rows (row_count unchanged) "
          f"-- {len(pre_changes)} pre cells + {len(post_changes)} post cells touched")


if __name__ == "__main__":
    main()
