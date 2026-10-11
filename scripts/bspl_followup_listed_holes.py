#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blank BS master cells of the listed (DART-sourced) companies at 2023.1Q / 2023.2Q, per item (read-only)."""
import json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
LISTED = ["KR0001", "KR0002", "KR0003", "KR0005", "KR0008", "KR0009", "KR0010", "KR0011", "KR0032", "KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0073",
          "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104", "KR0150", "KR1000"]
ITEMS = [1, 2, 3, 4, 10, 11, 12, 13, 14, 15, 20, 21, 22, 23, 24, 30, 31]
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
have = defaultdict(set)
names = {}
for r in bs:
    if r["값"] is not None:
        have[r["원보험사코드"]].add((r["항목번호"], r["공시분기"]))
    names[r["원보험사코드"]] = r["원수사명"]
tot = 0
for q in ("2023.1Q", "2023.2Q"):
    print("==", q)
    for c in LISTED:
        miss = [i for i in ITEMS if (i, q) not in have[c]]
        if miss:
            tot += len(miss)
            print(f"  {c} {names.get(c,'')[:10]:<10} blank items: {miss}")
print("total blank listed cells at 2023.1Q/2Q:", tot)
