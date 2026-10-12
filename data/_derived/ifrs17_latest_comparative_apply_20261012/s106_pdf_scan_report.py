"""Read-only: summarise pdf_scan.csv (s105) - which PDF-lineage Tier-1 cells equal the current / prior-year printed column, split by own-filing vs later-filing PDF."""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "pdf_scan.csv", encoding="utf-8-sig")))
print("rows", len(rows))
print(Counter((r["own"], r["cls"]) for r in rows).most_common())
print()
print("=== own-filing PDF, master equals ONLY the 2nd/3rd printed column (suspect: prior-year / change column)")
for r in rows:
    if r["own"] == "True" and r["cls"] in ("COL2", "COL3", "COL2/3", "COL4"):
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r["cls"], r["detail"][:110], "|", r["pdf"][-40:])
print()
print("=== later-filing PDF, master equals ONLY the 1st column (suspect: wrong-year current column)")
for r in rows:
    if r["own"] == "False" and r["cls"] in ("COL1",):
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r["cls"], r["detail"][:110], "|", r["pdf"][-40:])
print()
print("=== NONE (master matches no printed number within tolerance)")
for r in rows:
    if r["cls"] == "NONE":
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r["own"], r["detail"][:130])
print()
print("=== NO_PDF / UNREADABLE")
for r in rows:
    if r["cls"] in ("NO_PDF", "PDF_UNREADABLE"):
        print(r["code"], r["quarter"], r["cls"], r["detail"])
print("NOLABEL by item:", Counter(r["item"] for r in rows if r["cls"] == "NOLABEL"))
