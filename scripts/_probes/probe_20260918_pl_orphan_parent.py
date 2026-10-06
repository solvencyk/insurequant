# -*- coding: utf-8 -*-
"""Enumerate PL_breakdown buckets where #2 생명장기손익 is None but children (#3~#12) present.

Reproduces validation's census (29 buckets / 10 display) and prints per-bucket detail
plus whether the DART raw filing dir exists on disk.
"""
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
PL = ROOT / "PL_breakdown.json"

with open(PL, encoding="utf-8") as fh:
    rows = json.load(fh)

# index: (code, quarter) -> {item_no: row}
buckets = {}
meta = {}
for r in rows:
    key = (r["원보험사코드"], r["공시분기"])
    buckets.setdefault(key, {})[r["항목번호"]] = r
    meta[r["원보험사코드"]] = (r["원수사명"], r["생손보여부"])

CHILDREN = list(range(3, 13))

orphans = []
for key, items in sorted(buckets.items()):
    row2 = items.get(2)
    v2 = row2["값"] if row2 else None
    if v2 is not None:
        continue
    present = {n: items[n]["값"] for n in CHILDREN if n in items and items[n]["값"] is not None}
    if not present:
        continue
    orphans.append((key, v2, present, 2 in items))

print(f"'자식 present · 부모(#2) None' 버킷: {len(orphans)}")

def is_display(q):
    # display scope = 4Q only for annual filers? validation said 2023.1~3Q are non-display
    return not (q.startswith("2023.") and q[-2:] in ("1Q", "2Q", "3Q"))

disp = [o for o in orphans if is_display(o[0][1])]
print(f"display(2023.4Q 이후): {len(disp)}")
print()

raw_dirs = {}
for fy in sorted((ROOT / "data" / "dart").glob("FY*_Q*")):
    rawd = fy / "raw"
    if not rawd.is_dir():
        continue
    # FY2023_Q4 -> 2023.4Q
    year = fy.name[2:6]
    q = fy.name[-1]
    quarter = f"{year}.{q}Q"
    for sub in rawd.iterdir():
        if sub.is_dir():
            code = sub.name.split("_")[0]
            raw_dirs.setdefault((code, quarter), []).append(sub.name)

print(f"{'회사':<8}{'명':<16}{'구분':<6}{'분기':<9}{'row2존재':<9}{'raw':<6} 자식present")
for (code, quarter), v2, present, has_row2 in orphans:
    name, kind = meta[code]
    rd = raw_dirs.get((code, quarter))
    print(f"{code:<8}{name[:14]:<16}{kind:<6}{quarter:<9}{str(has_row2):<9}{('Y' if rd else '-'):<6}"
          + ", ".join(f"#{n}={v:.1f}" for n, v in sorted(present.items())))

print()
print("=== raw dir names for orphan buckets ===")
for (code, quarter), _, _, _ in orphans:
    rd = raw_dirs.get((code, quarter))
    print(f"{code} {quarter}: {rd}")
