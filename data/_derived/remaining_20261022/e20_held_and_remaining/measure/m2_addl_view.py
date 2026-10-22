"""m2: one-line view of d_census_table.csv and d_census_addl.csv (READ-ONLY)."""
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


lines = []
for nm in ("d_census_table.csv", "d_census_addl.csv"):
    rows = load(D / nm)
    lines.append(f"##### {nm} rows={len(rows)}")
    for r in rows:
        lines.append(
            f"{r['scope']:<14} {r['code']} {r['company']:<10} {r['quarter']} | {r['cause_class'][:14]:<14} | closes={r['latest_vector_closes_block'][:9]:<9} | "
            f"pl={r['pl_items_differ'][:40]:<40} | csm={r['csm_items_differ'][:34]:<34} | disp={r['disposition']:<14} | gold={r['gold_cells'][:40]}"
        )
(OUT / "m2_addl_view.txt").write_text("\n".join(lines), encoding="utf-8")
print(len(lines))
