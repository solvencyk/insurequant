"""q3_plan_full: print the narrative columns of plan_table.csv once per (code, scenario) (READ-ONLY)."""
import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
rows = list(csv.DictReader(open(M + "plan_table.csv", encoding="utf-8-sig")))
seen = set()
for r in rows:
    k = (r["code"], r["scenario"])
    if k in seen:
        continue
    seen.add(k)
    qs = [x["quarter"] for x in rows if (x["code"], x["scenario"]) == k]
    print("=" * 100)
    print(r["rank"], r["readiness"], "scope", r["scope_ref"], r["company"], r["code"], qs, "scn", r["scenario"])
    for col in ("census(d_census)", "e20_cause", "source_filing_and_tables", "reader_change", "verified_on", "gate_simulation", "decision_or_blocker"):
        print(f"  [{col}] {r[col]}")
