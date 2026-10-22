"""m3: print every column of the census rows matching code/quarter args (READ-ONLY)."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
code = sys.argv[1]
qs = sys.argv[2].split(",")
for nm in ("d_census_table.csv", "d_census_addl.csv"):
    with open(D / nm, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["code"] == code and r["quarter"] in qs:
                print("=====", nm)
                for k, v in r.items():
                    print(f"  {k}: {v}")
