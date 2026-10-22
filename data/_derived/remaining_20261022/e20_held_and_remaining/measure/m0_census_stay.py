"""m0: read d_census_table.csv + d_census_addl.csv and print the STAY / not-closing rows (READ-ONLY)."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = ROOT / "data/_derived/remaining_20261022/d_census"
OUT = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/measure"


def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


tab = load(D / "d_census_table.csv")
add = load(D / "d_census_addl.csv")
print("table rows", len(tab), "addl rows", len(add))
print("columns:", list(tab[0].keys()))
from collections import Counter

print(Counter(r["disposition"] for r in tab))
print(Counter(r["latest_vector_closes_block"] for r in tab))
lines = []
for r in tab:
    if r["disposition"] != "STAY":
        continue
    lines.append(
        f"{r['code']} {r['company']} {r['quarter']} | sheets={r['sheets']} | cause={r['cause_class']} | closes={r['latest_vector_closes_block']} | "
        f"basis={r['closure_basis']} | pl_items={r['pl_items_differ']} | csm_items={r['csm_items_differ']} | gold={r['gold_cells']}\n"
        f"    detail={r['cause_detail']}\n    reason={r['disposition_reason']}\n    evidence={r['evidence']}"
    )
(OUT / "m0_census_stay.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
