# -*- coding: utf-8 -*-
"""d1: HAND RECALCULATION of the Forward Outlook (kics_forward_capital.json) for 7 companies, 2026~2030 year-ends.

Companies: 한화생명 KR0068, DB손해보험 KR0011, 하나손해보험 KR0050, 하나생명보험 KR0097, 교보생명보험 KR0073, 메리츠화재해상보험 KR0001, 코리안리재보험 KR1000.

Independence: reads only kics_disclosure.json (baseline items 1/2/14), the per-bond ledger data/bonds/capital_securities_fy2026h1.json,
the registry data/bonds/capital_tier_registry.json (types) and, for comparison only, kics_forward_capital.json.
Nothing is imported from scripts/ or src/.

Model written from the ticket / publishing documentation (not copied):
  capital_y  = capital_baseline - sum_over_bonds[ contribution(as_of) - contribution(year_end_y) ]          (no re-issuance, no replacement)
     contribution(t) of a bond with outstanding amount A:
        call date c = call_date or legal_maturity
        c > as_of (call still ahead):   A if t < c else 0                   (called at the call date, 콜 5년차 정상 상환 가정)
        c <= as_of (past call, still outstanding):  A x r(t) with r = 잔존만기 체감 from the LEGAL maturity (별표22 Ⅲ.3.다.(2)①ㄴ: 20%p per year once
                                                   the remaining maturity is below 5 years); no legal maturity -> A until as_of, 0 afterwards
  scr_y      = scr_post + (scr_pre - scr_post) x min(1, (y - 2026)/(2032 - 2026))                           (linear 경과조치 run-off, model assumption)
  basic_y    = basic_baseline + [hybrid_basic(year_end_y, scr_y) - hybrid_basic(as_of, scr_post)]
     hybrid_basic(t, S) = min(legacy_remaining(t), 15% S) + min(tier1type_remaining(t), 10% S) + 0 x tier2type_remaining(t)
     type of each hybrid = issuer_type if the registry has one (the baseline is the issuer's own disclosed 기본자본), else type
  ratios     = capital_y / scr_y , basic_y / scr_y.
Regulation-faithful variant R (report only): the limits of 별표22 Ⅲ.2.다.(1)② and Ⅵ.1.가.(1) are computed on the 총요구자본 BEFORE the 선택적용
  경과조치 (Ⅵ.1.라) = scr_pre at every date, instead of the interpolated scr_y.
Outputs: d1_forward_handcalc.csv / d1_forward_handcalc.txt
"""
import csv
import json
from datetime import date

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
AS_OF = date(2026, 6, 30)
YEARS = [2026, 2027, 2028, 2029, 2030]
CODES = ["KR0068", "KR0011", "KR0050", "KR0097", "KR0073", "KR0001", "KR1000"]

import sys
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

# (pinned load below; no worktree dependence)
# (ledger loaded from the pinned revision)
import os
SUF = "_" + audit_io.resolved_rev()
PREV_REV = os.environ.get("AUDIT_PREV", "dbbffcb5")      # the state audited before (totals / basic paths must equal it except where announced)
PIN = "rev=%s registry=%s forward=%s ledger=%s previous=%s" % (audit_io.resolved_rev(), audit_io.sha12("data/bonds/capital_tier_registry.json"),
                                                               audit_io.sha12("kics_forward_capital.json"), audit_io.sha12("data/bonds/capital_securities_fy2026h1.json"), PREV_REV)
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
reg = audit_io.load_json("data/bonds/capital_tier_registry.json")["companies"]
led = {c["code"]: c for c in audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]}
pub = {r["insurer_code"]: r for r in audit_io.load_json("kics_forward_capital.json")}


def pd(s):
    if not s:
        return None
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


def rate(maturity, t):
    """20%p per year step-down once the remaining (legal) maturity is below 5 years (Ⅲ.3.다.(2)①ㄴ)"""
    if maturity is None:
        return 1.0
    yrs = (maturity - t).days / 365.25
    if yrs >= 5:
        return 1.0
    if yrs <= 0:
        return 0.0
    import math
    return max(0.0, 1.0 - 0.20 * math.ceil(5 - yrs))


def contribution(b, t):
    A = b["amount"]
    c = b["call"]
    if c is None or c > AS_OF:
        return A if (c is None or t < c) else 0.0
    if b["maturity"] is None:
        return A if t <= AS_OF else 0.0
    return A * rate(b["maturity"], t)


def bonds_of(code):
    out = []
    reg_secs = reg.get(code, {}).get("securities", [])
    for b in led[code]["bonds"]:
        amt = (b.get("outstanding_mn") or 0) / 100.0
        if amt <= 0:
            continue
        call = pd(b.get("call_date")) or pd(b.get("legal_maturity"))
        if call is None:
            continue
        typ = issuer_typ = None
        if b.get("tier") == "hybrid":
            # map by issue date to the registry security
            m = [s for s in reg_secs if s.get("issue_date") == b.get("issue_date")]
            if m:
                typ = m[0]["type"]
                issuer_typ = m[0].get("issuer_type") or m[0]["type"]
            else:
                raise SystemExit("UNMATCHED hybrid in registry: %s %s %s" % (code, b.get("issue_date"), b.get("name")))
        out.append({"name": b.get("name"), "tier": b.get("tier"), "issue": b.get("issue_date"), "amount": amt, "call": call,
                    "maturity": pd(b.get("legal_maturity")), "type": typ, "basis": issuer_typ})
    return out


def hybrid_basic(bonds, t, scr_limit, attr):
    by = {"legacy_tfi": 0.0, "tier1": 0.0, "tier2": 0.0}
    for b in bonds:
        if b["tier"] != "hybrid":
            continue
        ty = b[attr] or "tier1"
        by[ty] += contribution(b, t)
    return min(by["legacy_tfi"], 0.15 * scr_limit) + min(by["tier1"], 0.10 * scr_limit), by


def path(code, attr, variant="model"):
    r = inp[code]
    cap0 = r["i1_post"] if r["i1_post"] is not None else r["i1_pre"]
    bas0 = r["i2_post"] if r["i2_post"] is not None else r["i2_pre"]
    s_post = r["i14_post"] if r["i14_post"] is not None else r["i14_pre"]
    s_pre = r["i14_pre"] if r["i14_pre"] is not None else r["i14_post"]
    bonds = bonds_of(code)
    rows = []
    for y in YEARS:
        ye = date(y, 12, 31)
        prog = min(1.0, max(0.0, (y - 2026) / 6.0))
        s_y = s_post + (s_pre - s_post) * prog
        dedu = sum(contribution(b, AS_OF) - contribution(b, ye) for b in bonds)
        cap_y = cap0 - dedu
        if variant == "model":
            hb_y, by_y = hybrid_basic(bonds, ye, s_y, attr)
            hb_0, _ = hybrid_basic(bonds, AS_OF, s_post, attr)
        else:   # variant R: limits on the pre-경과조치 총요구자본 throughout
            hb_y, by_y = hybrid_basic(bonds, ye, s_pre, attr)
            hb_0, _ = hybrid_basic(bonds, AS_OF, s_pre, attr)
        bas_y = (bas0 or 0.0) + hb_y - hb_0
        rows.append({"year": y, "scr": s_y, "capital": cap_y, "basic": bas_y,
                     "ratio": 0.0 if cap_y <= 0 else cap_y / s_y * 100, "basic_ratio": 0.0 if bas_y <= 0 else bas_y / s_y * 100,
                     "legacy_rem": by_y["legacy_tfi"], "tier1_rem": by_y["tier1"], "tier2_rem": by_y["tier2"]})
    return rows, {"cap0": cap0, "bas0": bas0, "s_post": s_post, "s_pre": s_pre, "bonds": bonds}


out_rows = []
txt = []
tot_cmp = 0
tot_bad = 0
for code in CODES:
    p = pub[code]
    flag = p.get("baseline_basis_flag")
    mine, meta = path(code, "basis")
    txt.append("== %s %s  baseline capital %.1f basic %.1f scr_post %.1f scr_pre %.1f  baseline_basis_flag(pub)=%s" % (
        code, inp[code]["name"], meta["cap0"], meta["bas0"], meta["s_post"], meta["s_pre"], flag))
    for b in meta["bonds"]:
        txt.append("   bond %-9s %s issue=%s call=%s mat=%s amt=%.1f type=%s basis=%s" % (b["tier"], (b["name"] or "")[:34], b["issue"], b["call"], b["maturity"], b["amount"], b["type"], b["basis"]))
    for m_, pr in zip(mine, p["projections"]):
        assert m_["year"] == pr["year"]
        diffs = {
            "scr": m_["scr"] - pr["scr_eok"], "capital": m_["capital"] - pr["capital_eok"], "basic": m_["basic"] - pr["basic_capital_eok"],
            "ratio": m_["ratio"] - pr["ratio_pct"], "basic_ratio": m_["basic_ratio"] - pr["basic_ratio_pct"]}
        ok = (abs(diffs["scr"]) <= 0.06 and abs(diffs["capital"]) <= 0.06 and abs(diffs["basic"]) <= 0.06
              and abs(diffs["ratio"]) <= 0.011 and abs(diffs["basic_ratio"]) <= 0.011)
        tot_cmp += 1
        tot_bad += 0 if ok else 1
        out_rows.append({"code": code, "name": inp[code]["name"], "year": m_["year"],
                         "scr_mine": round(m_["scr"], 2), "scr_pub": pr["scr_eok"],
                         "capital_mine": round(m_["capital"], 2), "capital_pub": pr["capital_eok"],
                         "basic_mine": round(m_["basic"], 2), "basic_pub": pr["basic_capital_eok"],
                         "ratio_mine": round(m_["ratio"], 3), "ratio_pub": pr["ratio_pct"],
                         "basic_ratio_mine": round(m_["basic_ratio"], 3), "basic_ratio_pub": pr["basic_ratio_pct"],
                         "match": ok, "d_ratio": round(diffs["ratio"], 4), "d_basic_ratio": round(diffs["basic_ratio"], 4),
                         "legacy_rem": round(m_["legacy_rem"], 1), "tier1_rem": round(m_["tier1_rem"], 1), "tier2_rem": round(m_["tier2_rem"], 1)})
        txt.append("   %d scr %.1f/%.1f cap %.1f/%.1f basic %.1f/%.1f ratio %.2f/%.2f basic_ratio %.2f/%.2f %s" % (
            m_["year"], m_["scr"], pr["scr_eok"], m_["capital"], pr["capital_eok"], m_["basic"], pr["basic_capital_eok"],
            m_["ratio"], pr["ratio_pct"], m_["basic_ratio"], pr["basic_ratio_pct"], "OK" if ok else "<<< DIFF"))
    # our-classification path for flagged companies
    if flag:
        alt, _ = path(code, "type")
        for a, pr in zip(alt, p["projections"]):
            pub_alt = pr.get("basic_ratio_by_type_pct")
            ok2 = pub_alt is not None and abs(a["basic_ratio"] - pub_alt) <= 0.011
            txt.append("   [our-type path] %d basic_ratio mine %.2f vs pub basic_ratio_by_type_pct %s %s" % (a["year"], a["basic_ratio"], pub_alt, "OK" if ok2 else "<<< DIFF"))
            tot_cmp += 1
            tot_bad += 0 if ok2 else 1
    # regulation-faithful variant R
    rv, _ = path(code, "basis", variant="R")
    mx = max(abs(a["basic_ratio"] - b["basic_ratio"]) for a, b in zip(rv, mine))
    txt.append("   [variant R: limits on scr_pre] basic_ratio: " + ", ".join("%d %.2f" % (a["year"], a["basic_ratio"]) for a in rv) + "   max |diff| vs model = %.2f%%p" % mx)
    for a, b in zip(rv, mine):
        out_rows[-5 + [m_["year"] for m_ in mine].index(a["year"])]["basic_ratio_variantR"] = round(a["basic_ratio"], 3)

# ----- classification sensitivity (report only): flip the securities whose issuer treatment the X test could not confirm
def path_override(code, overrides):
    """overrides: {issue_date: new_basis_type}; everything else as published basis"""
    r = inp[code]
    cap0 = r["i1_post"] if r["i1_post"] is not None else r["i1_pre"]
    bas0 = r["i2_post"] if r["i2_post"] is not None else r["i2_pre"]
    s_post = r["i14_post"] if r["i14_post"] is not None else r["i14_pre"]
    s_pre = r["i14_pre"] if r["i14_pre"] is not None else r["i14_post"]
    bonds = bonds_of(code)
    for b in bonds:
        if b["tier"] == "hybrid" and b["issue"] in overrides:
            b["basis"] = overrides[b["issue"]]
    res = []
    for y in YEARS:
        ye = date(y, 12, 31)
        prog = min(1.0, max(0.0, (y - 2026) / 6.0))
        s_y = s_post + (s_pre - s_post) * prog
        hb_y, _ = hybrid_basic(bonds, ye, s_y, "basis")
        hb_0, _ = hybrid_basic(bonds, AS_OF, s_post, "basis")
        bas_y = (bas0 or 0.0) + hb_y - hb_0
        res.append((y, 0.0 if bas_y <= 0 else bas_y / s_y * 100))
    return res


SENS = {
    "KR1000": ("코리안리 제5·6회 -> 기본자본형(발행사 기본자본 처리 가정)", {"2023-03-16": "tier1", "2024-10-11": "tier1"}),
    "KR0097": ("하나생명 제1회 -> 보완자본형(우리 분류)", {"2023-03-31": "tier2"}),
    "KR0073": ("교보 2024-11 -> 보완자본형(우리 분류)", {"2024-11-12": "tier2"}),
}
txt.append("")
txt.append("classification sensitivity of the basic-ratio path (published basis vs flipped), %p:")
for code, (label, ov) in SENS.items():
    base = [(m_["year"], m_["basic_ratio"]) for m_ in path(code, "basis")[0]]
    alt = path_override(code, ov)
    txt.append("  %s %s : " % (code, label) + "; ".join("%d %.2f -> %.2f (%+.2f)" % (y, b, a, a - b) for (y, b), (_, a) in zip(base, alt)))

# total-path invariance of the published file against the pre-reinstatement snapshot
before_path = ROOT + "/data/_derived/capsec_reinstate_20261012/before/kics_forward_capital.json"
try:
    bef = {r["insurer_code"]: r for r in json.load(open(before_path, encoding="utf-8"))}
    ndiff = ncmp = 0
    for code, r in pub.items():
        if r.get("status") != "ok" or code not in bef or bef[code].get("status") != "ok":
            continue
        for a, b in zip(r["projections"], bef[code]["projections"]):
            for k in ("capital_eok", "ratio_pct", "scr_eok"):
                ncmp += 1
                if a[k] != b[k]:
                    ndiff += 1
    txt.append("")
    txt.append("total-path invariance, published after vs 'before' snapshot (capital/ratio/scr, all ok rows): %d compared, %d differ" % (ncmp, ndiff))
    nb = 0
    changed = []
    for code, r in pub.items():
        if r.get("status") != "ok" or code not in bef or bef[code].get("status") != "ok":
            continue
        if any(a["basic_ratio_pct"] != b["basic_ratio_pct"] for a, b in zip(r["projections"], bef[code]["projections"])):
            nb += 1
            changed.append(code)
    txt.append("basic-ratio path changed for %d companies: %s" % (nb, ", ".join(changed)))
except FileNotFoundError:
    txt.append("before snapshot not found: %s" % before_path)

# ----- previous committed state (ef62969, before the issuer-basis change): which fields moved?
try:
    prev = {r["insurer_code"]: r for r in audit_io.load_json("kics_forward_capital.json", rev=PREV_REV)}
    n_tot = n_basic = n_cmp = 0
    changed_basic = []
    for code, r in pub.items():
        if r.get("status") != "ok" or code not in prev or prev[code].get("status") != "ok":
            continue
        for a, b in zip(r["projections"], prev[code]["projections"]):
            n_cmp += 1
            if any(a[k] != b[k] for k in ("capital_eok", "ratio_pct", "scr_eok")):
                n_tot += 1
            if a["basic_ratio_pct"] != b["basic_ratio_pct"] or a["basic_capital_eok"] != b["basic_capital_eok"]:
                n_basic += 1
                changed_basic.append(code)
    txt.append("")
    txt.append("vs previous audited state %s: %d year-points compared; total-path (capital/ratio/scr) differs in %d; basic path (capital or ratio) differs in %d %s" % (
        PREV_REV, n_cmp, n_tot, n_basic, sorted(set(changed_basic))))
    other = []
    for code, r in pub.items():
        if code in prev and r != prev[code]:
            ch = sorted(k for k in set(r) | set(prev[code]) if r.get(k) != prev[code].get(k))
            other.append((code, ch))
    txt.append("rows of kics_forward_capital.json that differ AT ALL from the previous audited state (code, changed top-level keys): %s" % other)
    gone = [c for c, r in pub.items() if r.get("status") == "ok" and ("baseline_basis_flag" in r and r.get("baseline_basis_flag"))]
    txt.append("rows still carrying baseline_basis_flag=true: %s ; rows with the field at all: %d" % (gone, sum(1 for r in pub.values() if "baseline_basis_flag" in r)))
    leftovers = sorted({k for r in pub.values() if r.get("status") == "ok" for p_ in r["projections"] for k in p_ if k in ("basic_capital_by_type_eok", "basic_ratio_by_type_pct")})
    txt.append("projection fields basic_*_by_type present anywhere (should be only when a mismatch exists): %s" % leftovers)
except Exception as exc:  # noqa: BLE001
    txt.append("previous-state comparison failed: %r" % (exc,))

txt.append("")
txt.append("COMPARED %d series points, %d differ beyond rounding tolerance" % (tot_cmp, tot_bad))
cols = []
for r in out_rows:
    for k in r:
        if k not in cols:
            cols.append(k)
with open(HERE + "d1_forward_handcalc" + SUF + ".csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(out_rows)
txt.insert(0, "PIN " + PIN)
open(HERE + "d1_forward_handcalc" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(txt) + "\n")
print("\n".join(txt))
