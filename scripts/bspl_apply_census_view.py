#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B): the downloader's per-cell census (attachments_20261011/census_result.json) next to the CURRENT blanks of the BS master.  Read-only.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_census_view.py [CATEGORY]
Items checked for blanks: 1,2,3,4,10,11,12,13,14,15,20,21,22,23,24,30,31 (5-8 reserves excluded).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
ITEMS = [1, 2, 3, 4, 10, 11, 12, 13, 14, 15, 20, 21, 22, 23, 24, 30, 31]


def main():
    cat = sys.argv[1] if len(sys.argv) > 1 else None
    census = json.loads((ROOT / "data/disclosure/_meta/attachments_20261011/census_result.json").read_text(encoding="utf-8"))
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    n = 0
    for c in census:
        if cat and c["category"] != cat:
            continue
        kr, q = c["kr"], c["period"]
        blanks = [i for i in ITEMS if (kr, i, q) not in mv]
        print(f"{kr} {q} {c['category']:<24} census_missing={c['missing_items']} current_blank={blanks}  | {c['detail'][:90]}")
        n += len(blanks)
    print("total current blank cells in the listed (company, quarter) pairs:", n)


if __name__ == "__main__":
    main()
