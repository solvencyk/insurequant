"""Cell-level fix: KR0032 capital-component slot shift (items 7/8/9/10).

Source of truth: raw 정기경영공시 PDF, verified three ways
  - fitz words -> y-bucket -> x-sort reconstruction
  - 240dpi render of the table region (artifacts/kr0032_render/*.png)
  - docling MD table in md_inbox
All three agree, unit header reads "(단위: 억원, %)" so no conversion.

The disclosure numbers the components 1..6 with NO 비지배지분 row; an older
write path shifted 이익잉여금 into the 자본조정 slot and AOCI into the
비지배지분 slot. Today's extractor already gets 2024.4Q right (see
_20260920_kr0032_match_trace.py) -- the master rows are stale.

Guards: exact (code, quarter, item) targeting; expected-old-value assertion;
canonical-항목명 assertion; sum(5..11) invariance; and a whole-file assertion
that no row other than the 12 targets differs from what was read.

--apply to write; default is dry-run.
"""
import argparse
import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
JSON_PATH = REPO / "kics_disclosure.json"

CODE = "KR0032"

# (quarter, item, canonical 항목명, expected_old, new)
PATCH = [
    ("2023.2Q", 7, "3. 이익잉여금", "0", "9577"),
    ("2023.2Q", 8, "4. 자본조정", "9577", "0"),
    ("2023.2Q", 9, "5. 기타포괄손익누계액", "0", "2383"),
    ("2023.2Q", 10, "6. 비지배지분", "2383", "0"),
    ("2023.3Q", 7, "3. 이익잉여금", "0", "9115"),
    ("2023.3Q", 8, "4. 자본조정", "9115", "0"),
    ("2023.3Q", 9, "5. 기타포괄손익누계액", "0", "2607"),
    ("2023.3Q", 10, "6. 비지배지분", "2607", "0"),
    ("2024.4Q", 7, "3. 이익잉여금", "0", "10279"),
    ("2024.4Q", 8, "4. 자본조정", "10279", "0"),
    ("2024.4Q", 9, "5. 기타포괄손익누계액", "0", "-2617"),
    ("2024.4Q", 10, "6. 비지배지분", "-2617", "0"),
]


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def comp_sum(rows, quarter):
    tot = 0.0
    for r in rows:
        if r.get("원보험사코드") != CODE or r.get("공시분기") != quarter:
            continue
        it = int(r["항목번호"])
        if 5 <= it <= 11:
            v = num(r.get("값"))
            if v is not None:
                tot += v
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    st0 = os.stat(JSON_PATH)
    original_text = JSON_PATH.read_text(encoding="utf-8")
    rows = json.loads(original_text)
    snapshot = [dict(r) for r in rows]

    quarters = sorted({q for q, _i, _n, _o, _v in PATCH})
    before_sums = {q: comp_sum(rows, q) for q in quarters}
    before_item4 = {}
    for q in quarters:
        for r in rows:
            if (r.get("원보험사코드") == CODE and r.get("공시분기") == q
                    and int(r["항목번호"]) == 4):
                before_item4[q] = num(r.get("값"))

    touched = []
    for quarter, item, label, old, new in PATCH:
        hits = [
            (i, r) for i, r in enumerate(rows)
            if r.get("원보험사코드") == CODE
            and r.get("공시분기") == quarter
            and int(r["항목번호"]) == item
        ]
        if len(hits) != 1:
            raise SystemExit(f"ABORT: {quarter} item{item}: expected 1 row, found {len(hits)}")
        idx, row = hits[0]
        if row.get("항목명") != label:
            raise SystemExit(
                f"ABORT: {quarter} item{item}: 항목명 is {row.get('항목명')!r}, expected {label!r}")
        if str(row.get("값")) != old:
            raise SystemExit(
                f"ABORT: {quarter} item{item}: 값 is {row.get('값')!r}, expected {old!r} "
                "(already fixed, or someone else changed it)")
        if "값_적용후" in row:
            raise SystemExit(
                f"ABORT: {quarter} item{item}: row carries 값_적용후={row['값_적용후']!r}; "
                "the 적용후 axis needs its own decision, not a blind copy")
        row["값"] = new
        touched.append((idx, quarter, item, label, old, new))

    # --- guard: nothing but the 12 targets may differ -------------------------
    target_idx = {t[0] for t in touched}
    if len(target_idx) != len(PATCH):
        raise SystemExit("ABORT: duplicate target index")
    diffs = []
    for i, (a_row, b_row) in enumerate(zip(snapshot, rows)):
        if a_row != b_row:
            diffs.append(i)
    if set(diffs) != target_idx:
        raise SystemExit(f"ABORT: unexpected diff set {sorted(set(diffs) ^ target_idx)}")
    if len(snapshot) != len(rows):
        raise SystemExit("ABORT: row count changed")

    # --- guard: sum(5..11) must be invariant (pure slot swap) -----------------
    for q in quarters:
        after = comp_sum(rows, q)
        if abs(after - before_sums[q]) > 1e-9:
            raise SystemExit(f"ABORT: {q} sum(5..11) {before_sums[q]} -> {after}")

    print("=== patch plan (values in 억원, unit header '(단위: 억원, %)') ===")
    for idx, q, it, lab, old, new in touched:
        print(f"  row[{idx}]  {q}  item{it:<3} {lab:<18} {old:>8} -> {new:>8}")
    print()
    print("=== rule 2 check: item4 vs sum(items 5..11) ===")
    for q in quarters:
        s = comp_sum(rows, q)
        i4 = before_item4[q]
        print(f"  {q}: item4={i4}  sum(5..11)={s}  diff={i4 - s:+.1f}  (unchanged by this patch)")

    if not a.apply:
        print("\nDRY RUN -- nothing written. Re-run with --apply.")
        return 0

    st1 = os.stat(JSON_PATH)
    if (st1.st_mtime_ns, st1.st_size) != (st0.st_mtime_ns, st0.st_size):
        raise SystemExit("ABORT: kics_disclosure.json changed on disk while we worked")

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(rows)} rows to {JSON_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
