# -*- coding: utf-8 -*-
"""e1: for every company, reproduce the two number lines the screen prints under the donuts, straight from the published JSON
(the page code reads t1.tier1_hybrid_recognized_eok / t1.tier1_hybrid_limit_eok  and  t2.numerator_eok / t2.tier2_limit_eok),
and compare the ratio of the printed numbers with the donut percentage.   Pure JSON arithmetic, independent of the page.
Reads the pinned revision of kics_tier1_utilization.json / kics_tier2_utilization.json.
Output: e1_screen_line_vs_donut_<rev>.txt / .csv
"""
import csv
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
t1 = {r["code"]: r for r in audit_io.load_json("kics_tier1_utilization.json")["results"]}
t2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}
rows = []
L = ["PIN rev=%s tier1=%s tier2=%s" % (audit_io.resolved_rev(), audit_io.sha12("kics_tier1_utilization.json"), audit_io.sha12("kics_tier2_utilization.json"))]
bad1 = bad2 = 0
for code in sorted(t1):
    a, b = t1[code], t2.get(code)
    rec = a.get("tier1_hybrid_recognized_eok")
    if rec is None:
        rec = a.get("tier1_hybrid_issued_eok")
    lim = a.get("tier1_hybrid_limit_eok")
    pct1 = a.get("utilization_pct")
    printed_ratio1 = None if not lim else rec / lim * 100
    ok1 = pct1 is not None and printed_ratio1 is not None and abs(printed_ratio1 - pct1) <= 0.6
    n2 = b.get("numerator_eok") if b else None
    l2 = b.get("tier2_limit_eok") if b else None
    pct2 = b.get("utilization_pct") if b else None
    printed_ratio2 = None if (n2 is None or not l2) else n2 / l2 * 100
    ok2 = (pct2 is None and printed_ratio2 is None) or (pct2 is not None and printed_ratio2 is not None and abs(printed_ratio2 - pct2) <= 0.6)
    bad1 += 0 if ok1 else 1
    bad2 += 0 if ok2 else 1
    rows.append({"code": code, "company": a["company"], "t1_pct": pct1, "t1_printed_X": rec, "t1_printed_Y": lim, "t1_X_over_Y": None if printed_ratio1 is None else round(printed_ratio1, 2),
                 "t1_consistent": ok1, "t1_legacy_eok": a.get("tier1_legacy_eok"), "t1_legacy_limit": a.get("tier1_legacy_limit_eok"), "t1_basic_new_eok": a.get("tier1_basic_new_eok"),
                 "t1_basic_new_limit": a.get("tier1_basic_new_limit_eok"), "t1_binding": a.get("binding_leg"), "t1_gf": a.get("tier1_grandfathered_hybrid_eok"),
                 "t2_pct": pct2, "t2_printed_X": n2, "t2_printed_Y": l2, "t2_X_over_Y": None if printed_ratio2 is None else round(printed_ratio2, 2), "t2_consistent": ok2})
    if not ok1 or not ok2:
        L.append("MISMATCH %s %s | tier1 donut %s%% vs printed %s / %s = %s%% (binding=%s legacy %s/%s basic_new %s/%s) | tier2 donut %s%% vs printed %s / %s = %s%%" % (
            code, a["company"][:8], pct1, rec, lim, None if printed_ratio1 is None else round(printed_ratio1, 1), a.get("binding_leg"), a.get("tier1_legacy_eok"), a.get("tier1_legacy_limit_eok"),
            a.get("tier1_basic_new_eok"), a.get("tier1_basic_new_limit_eok"), pct2, n2, l2, None if printed_ratio2 is None else round(printed_ratio2, 1)))
L.insert(1, "number line vs donut: tier1 inconsistent %d / 47 ; tier2 inconsistent %d / 47 (tolerance 0.6%%p)" % (bad1, bad2))
cols = list(rows[0].keys())
with open(HERE + "e1_screen_line_vs_donut" + SUF + ".csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
open(HERE + "e1_screen_line_vs_donut" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
