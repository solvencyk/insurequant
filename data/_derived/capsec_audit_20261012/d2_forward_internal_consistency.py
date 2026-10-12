# -*- coding: utf-8 -*-
"""d2: is every ratio of kics_forward_capital.json equal to its own capital / SCR?  (clamped / floored values are false improvements)
For each ok company and each projection year:
    ratio_calc = capital_eok / scr_eok * 100        vs ratio_pct
    basic_calc = basic_capital_eok / scr_eok * 100   vs basic_ratio_pct
and the headline the page prints:  "2030 변화" = projection[2030] - baseline  (percentage points) - recomputed with the clamped and with the true values.
Independent: reads only the pinned JSON.   Output d2_forward_internal_consistency_<rev>.txt
"""
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
fw = audit_io.load_json("kics_forward_capital.json")
L = ["PIN rev=%s forward=%s" % (audit_io.resolved_rev(), audit_io.sha12("kics_forward_capital.json"))]
bad_cos = []
for r in fw:
    if r.get("status") != "ok":
        continue
    b = r["baseline"]
    flags = []
    for p in r["projections"]:
        scr = p["scr_eok"]
        rc = p["capital_eok"] / scr * 100
        bc = p["basic_capital_eok"] / scr * 100
        dr = p["ratio_pct"] - rc
        db = p["basic_ratio_pct"] - bc
        if abs(dr) > 0.011 or abs(db) > 0.011:
            flags.append((p["year"], p["capital_eok"], p["basic_capital_eok"], scr, p["ratio_pct"], round(rc, 2), p["basic_ratio_pct"], round(bc, 2),
                          p.get("capacity_exhausted"), p.get("basic_capacity_exhausted")))
    if flags:
        last = r["projections"][-1]
        shown_chg_r = last["ratio_pct"] - b["ratio_post_pct"]
        shown_chg_b = last["basic_ratio_pct"] - b["basic_ratio_post_pct"]
        true_chg_r = last["capital_eok"] / last["scr_eok"] * 100 - b["ratio_post_pct"]
        true_chg_b = last["basic_capital_eok"] / last["scr_eok"] * 100 - b["basic_ratio_post_pct"]
        bad_cos.append(r["insurer_code"])
        L.append("%s %s | baseline ratio %.2f basic %.2f | 2030 change printed on the page: ratio %+.2f / basic %+.2f %%p ; recomputed from the JSON's own capital/SCR: ratio %+.2f / basic %+.2f %%p" % (
            r["insurer_code"], r["insurer_name"], b["ratio_post_pct"], b["basic_ratio_post_pct"], shown_chg_r, shown_chg_b, true_chg_r, true_chg_b))
        for f in flags:
            L.append("    %d capital %.1f basic_capital %.1f SCR %.1f | ratio_pct %.2f (own capital/SCR %.2f) | basic_ratio_pct %.2f (own %.2f) | capacity_exhausted=%s basic_capacity_exhausted=%s" % f)
L.append("")
L.append("companies whose projections are not equal to their own capital/SCR: %d  %s" % (len(bad_cos), bad_cos))

# ---- baseline block vs the master (all ok companies, not only the 7 of the hand calculation)
import json
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))


def pick(c, k):
    r = inp[c]
    v = r.get("i%d_post" % k)
    return v if v is not None else r.get("i%d_pre" % k)


bl_amt, bl_ratio = [], []
n_ok = 0
for r in fw:
    if r.get("status") != "ok":
        continue
    n_ok += 1
    c = r["insurer_code"]
    b = r["baseline"]
    for key, ref in (("capital_eok", pick(c, 1)), ("basic_capital_eok", pick(c, 2)), ("scr_post_eok", pick(c, 14)), ("scr_pre_eok", inp[c].get("i14_pre"))):
        if ref is None or abs(b[key] - ref) > 0.06:
            bl_amt.append((c, r["insurer_name"], key, b[key], ref))
    for key, ref in (("ratio_post_pct", pick(c, 27)), ("basic_ratio_post_pct", pick(c, 28))):
        if ref is None or abs(b[key] - ref) > 0.02:
            bl_ratio.append((c, r["insurer_name"], key, b[key], ref, b[key] - ref if ref is not None else None))
L.append("baseline AMOUNTS (capital / basic capital / SCR post / SCR pre) vs master items 1/2/14 (2026.2Q, 적용후 else 적용전): %d ok companies, %d mismatches" % (n_ok, len(bl_amt)))
for x in bl_amt:
    L.append("    %s %s %s json %s master %s" % x)
L.append("baseline RATIOS vs the issuer-printed items 27/28: %d fields differ by more than 0.02%%p (the JSON ratio is capital/SCR of the rounded 억원 amounts); max |diff| = %.2f%%p" % (
    len(bl_ratio), max([abs(x[5]) for x in bl_ratio if x[5] is not None] or [0.0])))
for x in bl_ratio:
    L.append("    %s %s %s json %s issuer-printed %s (diff %+.2f)" % x)
open(HERE + "d2_forward_internal_consistency" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
