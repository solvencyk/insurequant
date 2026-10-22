"""q7_stay_map: join the STAY / not-closing rows of d_census_table.csv (+ d_census_addl.csv) with plan_table.csv -> stay_mapping.csv  (READ-ONLY)"""
import csv, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/"
H = ROOT + "e20_held_and_remaining/measure/"
def load(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig", newline="")))
tab = load(ROOT + "d_census/d_census_table.csv")
add = load(ROOT + "d_census/d_census_addl.csv")
plan = {(r["code"], r["quarter"]): r for r in load(H + "plan_table.csv")}
print("table cols:", list(tab[0].keys())[:14]); print("addl cols:", list(add[0].keys())[:14])
rows = []
for src, data in (("d_census_table", tab), ("d_census_addl", add)):
    for r in data:
        disp = r.get("disposition") or ""
        if src == "d_census_table" and disp != "STAY":
            continue
        k = (r["code"], r["quarter"])
        p = plan.get(k)
        rows.append({"source": src, "code": r["code"], "company": r.get("company", ""), "quarter": r["quarter"], "census_disposition": disp or r.get("kind", ""), "cause_class": r.get("cause_class", ""),
                     "plan_readiness": p["readiness"] if p else "(not in plan: see note)", "plan_scenario": p["scenario"] if p else "", "plan_rank": p["rank"] if p else ""})
with open(H + "stay_mapping.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), Counter((r["source"], r["plan_readiness"]) for r in rows))
for r in rows:
    print(r["source"][:11], r["code"], r["company"][:6], r["quarter"], "|", r["census_disposition"][:22], "|", r["cause_class"][:18], "->", r["plan_readiness"], r["plan_scenario"])
