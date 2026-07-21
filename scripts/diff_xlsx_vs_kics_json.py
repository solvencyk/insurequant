# -*- coding: utf-8 -*-
"""Diff owner-edited insurequant_master_tables.xlsx (K-ICS공시 sheet) against
kics_disclosure.json, to see exactly which cells the owner hand-filled/changed.

Read-only. Prints:
  - NEW rows present in xlsx but not in JSON (by item-no / quarter / company)
  - VALUE diffs on shared keys (값 and 값_적용후)
  - focus census on market sub-risks (items 36-40) and life sub-risks (29-35)
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[1]
XLSX = REPO / "insurequant_master_tables.xlsx"
JSON_PATH = REPO / "kics_disclosure.json"

ITEM_NAMES_36_40 = {36: "금리위험액", 37: "주식위험액", 38: "부동산위험액",
                    39: "외환위험액", 40: "자산집중위험액"}


def _num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def _close(a, b) -> bool:
    na, nb = _num(a), _num(b)
    if na is None or nb is None:
        return str(a) == str(b)
    return abs(na - nb) < 0.01


def main() -> int:
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb["K-ICS공시"]
    xl = [r for r in ws.iter_rows(min_row=2, values_only=True) if r[0] is not None]
    wb.close()

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    jidx = defaultdict(list)
    for r in rows:
        jidx[(r["원보험사코드"], r["공시분기"], int(r["항목번호"]))].append(r)

    new_rows, val_diff, post_diff = [], [], []
    for r in xl:
        code, name, tick, kind, item, iname, q, val, post = r
        key = (code, q, int(item))
        js = jidx.get(key)
        if not js:
            new_rows.append(r)
            continue
        jvals = {str(x["값"]) for x in js}
        if not any(_close(val, v) for v in jvals):
            val_diff.append((key, iname, sorted(jvals), val))
        jposts = {str(x.get("값_적용후", "")) for x in js}
        if post not in (None, "") and not any(_close(post, p) for p in jposts):
            post_diff.append((key, iname, sorted(jposts), post))

    print(f"xlsx rows={len(xl)}  json rows={len(rows)}")
    print(f"\n=== NEW rows in xlsx (not in json): {len(new_rows)} ===")
    print("by item:", dict(sorted(Counter(r[4] for r in new_rows).items())))
    print("by quarter:", dict(sorted(Counter(r[6] for r in new_rows).items())))
    print("by company:", dict(sorted(Counter(r[0] for r in new_rows).items())))

    print(f"\n=== VALUE diffs (값) on shared keys: {len(val_diff)} ===")
    print("by item:", dict(sorted(Counter(k[2] for k, *_ in val_diff).items())))

    print(f"\n=== POST diffs (값_적용후): {len(post_diff)} ===")

    # focused census: market sub-risks 36-40
    print("\n=== MARKET SUB-RISK (36-40) coverage: xlsx vs json ===")
    xl_mkt = defaultdict(set)
    for r in xl:
        if 36 <= int(r[4]) <= 40 and _num(r[7]) is not None:
            xl_mkt[(r[0], r[6])].add(int(r[4]))
    j_mkt = defaultdict(set)
    for r in rows:
        if 36 <= int(r["항목번호"]) <= 40 and _num(r["값"]) is not None:
            j_mkt[(r["원보험사코드"], r["공시분기"])].add(int(r["항목번호"]))
    only_xl = sorted(set(xl_mkt) - set(j_mkt))
    print(f"xlsx has 36-40 for {len(xl_mkt)} (co,q); json has {len(j_mkt)}")
    print(f"(co,q) with 36-40 in xlsx but NOT in json: {len(only_xl)}")
    for k in only_xl[:60]:
        print(f"   {k[0]} {k[1]}: items {sorted(xl_mkt[k])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
