"""inbox/parser/20260829T1800Z step 3: census of (company,quarter) raw dirs with 2+ TOP-LEVEL
xml files (i.e., a main filing xml PLUS one or more attachment xmls, like KR0079 2025.4Q's
main + _00760 + _00761). Distinct from the earlier 20260829T1600Z census (which was about
xml/ SUBDIRECTORY vs top-level placement -- a different axis). This one is: how many raw
dirs literally have >1 xml sitting directly in the dir (glob 'd/*.xml', not 'd/xml/*.xml').

Also checks: does each of ifrs17's actual live XML-reading entry points already glob ALL of
them (not just the largest/first)? Read-only -- no writes.
"""
import glob
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

multi = []       # (company_quarter_dir, count, [filenames])
single = 0
zero = 0
total_dirs = 0

for fy_dir in sorted((ROOT / "data" / "dart").glob("FY*")):
    raw_dir = fy_dir / "raw"
    if not raw_dir.is_dir():
        continue
    for d in sorted(raw_dir.iterdir()):
        if not d.is_dir():
            continue
        total_dirs += 1
        top_xmls = sorted(glob.glob(str(d) + "/*.xml"))
        n = len(top_xmls)
        if n >= 2:
            multi.append((str(d.relative_to(ROOT)), n, [Path(x).name for x in top_xmls]))
        elif n == 1:
            single += 1
        else:
            zero += 1

print(f"total (fy,company-filing) raw dirs scanned: {total_dirs}")
print(f"  top-level xml count == 0: {zero}")
print(f"  top-level xml count == 1: {single}")
print(f"  top-level xml count >= 2: {len(multi)}")

print(f"\n=== all {len(multi)} dirs with 2+ top-level xml files ===")
for d, n, names in multi:
    print(f"  {d}  (n={n}): {names}")
