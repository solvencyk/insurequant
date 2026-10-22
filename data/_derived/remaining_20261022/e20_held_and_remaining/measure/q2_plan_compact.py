"""q2_plan_compact: compact view of plan_table.csv (READ-ONLY)."""
import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
rows = list(csv.DictReader(open(M + "plan_table.csv", encoding="utf-8-sig")))
print(len(rows), "rows;", list(rows[0].keys()))
for r in rows:
    print(r["rank"], r["readiness"], r["scope_ref"], r["company"], r["code"], r["quarter"], r["scenario"], "PL", r["pl_value_cells"], "CSM", r["csm_cells"], "resid", r["bridge_residual_mn"], "| head", r["headline_delta_eok"][:60], "| csm", r["csm_closing_delta_eok"])
