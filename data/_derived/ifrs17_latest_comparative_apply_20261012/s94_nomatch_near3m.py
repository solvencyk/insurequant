"""Read-only: for every NO_MATCH row of scan3m_v2.csv (statement line found, master matches none of the 4 printed columns),
report how close the master value is to the current 3-month column vs the current cumulative column.
A master within 3 % of the 3M column and not within 3 % of the cumulative column is 'near-3M' (candidate for the 3-month-as-cumulative class)."""
import ast
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / "plan_final.json").read_text(encoding="utf-8"))
fixed = {(c["code"], c["quarter"], c["item"]) for c in plan["cells"] if c["kind"] == "3m_as_cumulative"}
rows = list(csv.DictReader(open(HERE / "scan3m_v2.csv", encoding="utf-8-sig")))
out = []
for r in rows:
    if r["cls"] != "NO_MATCH":
        continue
    vals = ast.literal_eval(r["vals"])
    m = float(r["master"])
    for scale in (1e6, 1e3, 1.0):
        pass
    # choose the scale for which the cumulative column is closest in magnitude to the master
    best = min((abs(abs(vals[1] / s) - abs(m)), s) for s in (1e6, 1e3, 1.0))
    s = best[1]
    c3, cc = abs(vals[0] / s), abs(vals[1] / s)
    am = abs(m)
    d3 = abs(am - c3) / max(c3, 1.0)
    dc = abs(am - cc) / max(cc, 1.0)
    flag = "NEAR_3M" if (d3 < 0.03 and dc >= 0.03) else ("near_cum" if dc < 0.03 else "")
    out.append((r["code"], r["name"], r["quarter"], r["item"], m, round(c3, 3), round(cc, 3), round(d3, 4), round(dc, 4), flag, (r["code"], r["quarter"], int(r["item"])) in fixed))
print(len(out), "NO_MATCH rows")
for o in out:
    if o[9] == "NEAR_3M" or o[10]:
        print("NEAR_3M/fixed:", o)
print("--- near_cum (NO_MATCH within 3% of cumulative):", sum(1 for o in out if o[9] == "near_cum"))
print("--- neither:")
for o in out:
    if o[9] == "":
        print("   ", o[:10])
with open(HERE / "scan_nomatch_classified.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["code", "name", "quarter", "item", "master", "col_3m_abs", "col_cum_abs", "rel_dist_3m", "rel_dist_cum", "flag", "fixed_in_plan"])
    w.writerows(out)
