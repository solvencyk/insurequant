"""Read-only: final class counts of the PDF-lineage scan after pass 1 (s105) + pass 2 (s109) -> pdf_scan_final.csv (one row per cell) and printed counts."""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
p1 = list(csv.DictReader(open(HERE / "pdf_scan.csv", encoding="utf-8-sig")))
p2 = {(r["code"], r["quarter"], r["item"], r["pdf"]): r for r in csv.DictReader(open(HERE / "pdf_scan2.csv", encoding="utf-8-sig"))}
final = []
for r in p1:
    k = (r["code"], r["quarter"], r["item"], r["pdf"])
    cls, det, passno = r["cls"], r["detail"], 1
    if k in p2:
        cls, det, passno = p2[k]["cls2"], p2[k]["detail2"], 2
    final.append({"code": r["code"], "name": r["name"], "quarter": r["quarter"], "item": r["item"], "master": r["master"], "own_filing_pdf": r["own"], "final_class": cls, "pass": passno, "detail": det, "pdf": r["pdf"]})
with open(HERE / "pdf_scan_final.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(final[0].keys()))
    w.writeheader()
    w.writerows(final)
print("cells", len(final))
c = Counter(r["final_class"] for r in final)
print(c.most_common())
dec = sum(v for k, v in c.items() if k.startswith("COL"))
print("decisive (master equals a printed column):", dec, " undecided (NONE/NOLABEL/UNREADABLE):", len(final) - dec)
print("own-filing PDF:", sum(1 for r in final if r["own_filing_pdf"] == "True"), "later-filing PDF:", sum(1 for r in final if r["own_filing_pdf"] == "False"))
cur = sum(1 for r in final if r["final_class"] in ("COL1", "COL1/2", "COL1/3", "COL1/2/3") and r["own_filing_pdf"] == "True")
cmp_ = sum(1 for r in final if r["final_class"] in ("COL2",) and r["own_filing_pdf"] == "False")
print("own PDF -> current column:", cur, "| later PDF -> comparative (prior-year) column:", cmp_)
print("companies", len({r["code"] for r in final}), "quarters", len({r["quarter"] for r in final}))
