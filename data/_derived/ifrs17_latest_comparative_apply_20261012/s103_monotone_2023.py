"""Read-only: from scan_monotone.csv print only the within-FY2023 Q1->Q2 and Q2->Q3 flags (all companies, all items), plus a per-company count of PDF-lineage buckets."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "scan_monotone.csv", encoding="utf-8-sig")))
sel = [r for r in rows if r["q_from"].startswith("2023.") and r["q_from"][5] in "12"]
print(len(sel), "flags in FY2023 Q1->Q2 / Q2->Q3")
for r in sel:
    print(r["code"], r["name"][:8], "item", r["item"], r["q_from"], r["ytd_from"], "->", r["q_to"], r["ytd_to"], "ratio", r["ratio"])
