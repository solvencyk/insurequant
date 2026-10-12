"""Read-only: within-FY monotonicity flags 2024-2026 (Q1->Q2, Q2->Q3, Q3->Q4) for Tier-1 flow items, with the source lineage of both buckets, to spot wrong-year/3M loads outside FY2023."""
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
src = {}
for c in prov["cells"]:
    if c["item_block"] != "income_statement":
        continue
    hows = sorted({f.get("how", "?") for f in c.get("source_files", [])})
    src[(c["company_code"], c["quarter"])] = c.get("source_id", "?") + ":" + "+".join(h[:14] for h in hows)
rows = list(csv.DictReader(open(HERE / "scan_monotone.csv", encoding="utf-8-sig")))
want = {"1", "16", "17", "20", "22", "23", "24"}
n = 0
for r in rows:
    if r["item"] not in want or not r["q_from"].startswith(("2024.", "2025.", "2026.")):
        continue
    n += 1
    print(r["code"], r["name"][:6], "item", r["item"], r["q_from"], r["ytd_from"], "->", r["q_to"], r["ytd_to"], "ratio", r["ratio"], "|", src.get((r["code"], r["q_from"]), "-")[:36], "->", src.get((r["code"], r["q_to"]), "-")[:36])
print(n, "flags")
