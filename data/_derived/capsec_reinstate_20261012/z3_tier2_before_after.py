# -*- coding: utf-8 -*-
"""Request 8 before/after (47 companies): tier2 numerator with the ledger pre-2023 deduction (owner final rule 2026-10-12 night).
before = deployed kics_tier2_utilization.json at HEAD (saved in before3/), after = capital_utilization_rules.compute_quarter now.
Writes z3_tier2_before_after_47.csv / .txt. Read-only for masters."""
import csv, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")
import capital_utilization_rules as R
HERE = Path(__file__).resolve().parent
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
ledger = R.load_ledger(); registry = R.load_registry()
comp = R.compute_quarter(recs, "2026.2Q", ledger, registry)
before = {r["code"]: r for r in json.loads((HERE / "before3" / "kics_tier2_utilization.json").read_text(encoding="utf-8"))["results"]}
cols = ["code", "company", "rule_before", "rule_after", "numerator_before", "numerator_after", "pct_before", "pct_after", "pct_change",
        "printed_53", "printed_54", "ledger_pre2023_hybrid", "ledger_pre2023_sub", "ledger_as_of", "printed_minus_ledger"]
rows = []
for code, c in comp.items():
    t2 = c["t2"]; b = before.get(code, {})
    led = ledger.get(code, {})
    pb, pa = b.get("utilization_pct"), t2["pct"]
    rows.append([code, c["name"], b.get("rule"), t2["rule"], b.get("numerator_eok"), t2["numerator"], pb, pa,
                 None if pb is None or pa is None else round(pa - pb, 1),
                 t2["grandfathered_hybrid_printed_eok"], t2["grandfathered_subordinated_printed_eok"],
                 t2["grandfathered_hybrid_eok"], t2["grandfathered_subordinated_eok"], led.get("as_of"),
                 round(t2["grandfathered_hybrid_printed_eok"] + t2["grandfathered_subordinated_printed_eok"]
                       - t2["grandfathered_hybrid_eok"] - t2["grandfathered_subordinated_eok"], 2)])
with (HERE / "z3_tier2_before_after_47.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh); w.writerow(cols); w.writerows(rows)
out = ["tier2 numerator / utilization before -> after (47 companies, 2026.2Q); changed rows first"]
chg = [r for r in rows if r[6] != r[7] or r[4] != r[5] or r[2] != r[3]]
out.append(f"changed: {len(chg)} of {len(rows)}")
for r in chg:
    out.append(f"  {r[0]} {str(r[1])[:9]:9s} rule {r[2]}->{r[3]} | num {r[4]} -> {r[5]} | pct {r[6]} -> {r[7]} ({r[8]}) | printed 53/54 {r[9]}/{r[10]} ledger<2023 hyb/sub {r[11]}/{r[12]} as_of {r[13]}")
out.append("unchanged:")
for r in rows:
    if r not in chg:
        out.append(f"  {r[0]} {str(r[1])[:9]:9s} rule {r[3]} num {r[5]} pct {r[7]} | printed {r[9]}/{r[10]} ledger {r[11]}/{r[12]}")
(HERE / "z3_tier2_before_after_47.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
