"""Read-only: every PDF-lineage Tier-1 cell whose source PDF is a LATER filing than the cell's quarter (own=False), with the final class from pass 1 / pass 2."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
p1 = list(csv.DictReader(open(HERE / "pdf_scan.csv", encoding="utf-8-sig")))
p2 = {(r["code"], r["quarter"], r["item"], r["pdf"]): r for r in csv.DictReader(open(HERE / "pdf_scan2.csv", encoding="utf-8-sig"))}
n = 0
for r in p1:
    if r["own"] != "False":
        continue
    k = (r["code"], r["quarter"], r["item"], r["pdf"])
    cls, det = r["cls"], r["detail"]
    if k in p2:
        cls, det = "p2:" + p2[k]["cls2"], p2[k]["detail2"]
    n += 1
    print(r["code"], r["name"][:7], r["quarter"], "item", r["item"], r["master"], cls, det[:90], "|", r["pdf"][-34:])
print("later-filing rows:", n)
