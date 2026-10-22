import csv, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
rows = list(csv.DictReader(open(OUT / "d_census_table.csv", encoding="utf-8-sig", newline="")))
want = sys.argv[1:] 
for r in rows:
    if r["scope"] != "A51": continue
    if want and not any(w in r["company"] + r["quarter"] for w in want): continue
    print("=" * 100)
    for k, v in r.items():
        if k in ("evidence", "code", "pl_restatement_note"): continue
        print(f"  {k}: {v}")
