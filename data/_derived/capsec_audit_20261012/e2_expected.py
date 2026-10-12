# -*- coding: utf-8 -*-
"""e2: build the EXPECTED screen values for every company (what K-ICS.html must show), independently of the page code.

Sources (pinned revision for the published JSON; my own recompute for the numerators):
   tier1/tier2 donut percentage + number lines : published JSON (pct) cross-checked with b1_recompute_47_<rev>.json (mine)
   forward curve + note                         : kics_forward_capital.json
   stacked bars + 2 big cells                   : kics_capital_securities_timeline.json  (computed here from the memo/ticket spec:
        bars   = per issue year, sum of face_eok of the tier (hybrid below, subordinated above), every year between first and last issue year
        cell   = latest coupon (latest issue_date among bonds with outstanding_eok > 0; same day -> larger outstanding),
                 total issued = sum of face_eok of ALL bonds of the tier (rounded), next call = earliest call_date >= reference date
                 (reference = max as_of of the file) among bonds with outstanding_eok > 0, amount = sum of outstanding_eok on that date)
Output: e2_expected_<rev>.json (compact; pasted into the browser audit) and e2_expected_<rev>.txt (human check)
Number format = Korean thousands separator after JS-style rounding (floor(x+0.5)).
"""
import json
import math
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
t1 = {r["code"]: r for r in audit_io.load_json("kics_tier1_utilization.json")["results"]}
t2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}
fwd = {r["insurer_code"]: r for r in audit_io.load_json("kics_forward_capital.json")}
tl = audit_io.load_json("kics_capital_securities_timeline.json")
b1 = {r["code"]: r for r in json.load(open(HERE + "b1_recompute_47" + SUF + ".json", encoding="utf-8"))}
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
ledger = {c["code"]: c for c in json.load(open(ROOT + "/data/bonds/capital_securities_fy2026h1.json", encoding="utf-8"))["companies"]}


from decimal import Decimal, ROUND_HALF_UP


def js_tofixed(x, nd):
    """JavaScript Number.prototype.toFixed: rounds the exact binary value half up (Python's % formatting rounds ties to even)."""
    q = Decimal(1).scaleb(-nd)
    return str(Decimal(x).quantize(q, rounding=ROUND_HALF_UP))


def jr(x):
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))


def fmt(x):
    if x is None:
        return "-"
    return ("△" if x < 0 else "") + "{:,}".format(abs(jr(x)))


def fmt_drop(d):
    return ("△" if d < 0 else "+") + js_tofixed(abs(d), 1)


ref = ""
for lst in tl["securities"].values():
    for b in lst:
        if b.get("as_of") and b["as_of"] > ref:
            ref = b["as_of"]

out = {}
for code in sorted(t1):
    a, b, m = t1[code], t2[code], b1[code]
    inp_c = inp[code]
    row = {"name": None}
    # ---- donut tier1
    pct1 = a["utilization_pct"]
    bind = m["t1_binding_mine"]
    scr = m["t1_scr"]
    if bind == "basic_10":
        X1, Y1 = m["t1_new_basic_mine"], 0.10 * scr
    elif bind == "legacy_15":
        X1, Y1 = m["t1_legacy53_mine"], 0.15 * scr
    else:
        X1, Y1 = 0.0, 0.15 * scr
    line1 = "기본자본 자본증권 %s억원 / 인정한도 %s억원" % (fmt(X1), fmt(Y1))
    gf = m["t1_legacy53_mine"] if bind == "legacy_15" else 0
    if gf > 0:
        line1 += " 경과조치 기발행분 %s억원 포함" % fmt(gf)
    # ---- no capital securities (item 6 <= 0 AND no outstanding bond in the ledger)
    led = ledger.get(code)
    n_out = 0
    if led:
        n_out = sum(1 for x in led.get("bonds", []) if (x.get("outstanding_mn") or 0) > 0)
    nosec_expected = (m["t1_item6"] <= 0.5) and n_out == 0
    # ---- donut tier2
    pct2 = b["utilization_pct"]
    N2 = b.get("numerator_eok")
    lim2 = b["tier2_limit_eok"]
    line2 = "보완자본 한도 적용 전 %s / 보완자본 한도 %s억원" % ("—" if N2 is None else fmt(N2) + "억원", fmt(lim2))
    gf2 = b.get("grandfathered_subordinated_eok") or 0
    if gf2 > 0:
        line2 += " 경과조치 기발행 후순위 %s억원" % fmt(gf2)
    lapse_line = None
    sup = b.get("supplementary_capital_eok")
    if N2 == 0 and sup and sup > 0:
        lapse = b.get("lapse_excess_item49_eok")
        if not (lapse and lapse > 0) and not (((b.get("grandfathered_hybrid_eok") or 0) + (b.get("grandfathered_subordinated_eok") or 0)) > 0):
            lapse = sup
        if lapse and lapse > 0:
            lapse_line = "해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 %s억원" % fmt(lapse)
    bh = a.get("hybrid_outstanding_eok") or 0
    bs = a.get("subordinated_outstanding_eok") or 0
    ref_line = ("참고 — 자본성증권 발행잔액: 신종 %s억원 · 후순위 %s억원" % (fmt(bh), fmt(bs))) if (bh > 0 or bs > 0) else None
    lines = [line1, line2]
    if lapse_line:
        lines.append(lapse_line)
    if ref_line:
        lines.append(ref_line)
    row["t1"] = {"pct": pct1, "pct_mine": m["t1_pct_mine"], "aria": "기본자본 자본증권 인정한도 소진율 " + (("100%% 초과 (%s%%)" % js_tofixed(pct1, 1)) if pct1 > 100 else ("%s%%" % js_tofixed(pct1, 1))),
                 "nosec": nosec_expected, "nosec_json": a.get("no_capital_securities"), "unconf": bool(a.get("type_unconfirmed")),
                 "excl_t2": a.get("tier1_excluded_tier2_type_eok") or 0, "unconf_pct": a.get("tier1_pct_if_unconfirmed_tier2")}
    if pct2 is None:
        aria2 = "보완자본 한도 소진율 " + (b.get("reason") or "데이터 없음")
    else:
        aria2 = "보완자본 한도 소진율 " + (("100%% 초과 (%s%%)" % js_tofixed(pct2, 1)) if pct2 > 100 else ("%s%%" % js_tofixed(pct2, 1)))
    row["t2"] = {"pct": pct2, "pct_mine": m["t2_pct_mine"], "aria": aria2, "na": pct2 is None}
    row["note"] = " | ".join(lines)
    # ---- forward
    f = fwd.get(code)
    if f is None:
        row["fwd"] = None
    elif f.get("status") != "ok":
        row["fwd"] = {"status": f.get("status"), "reason": f.get("exclusion_reason")}
    else:
        pr = f["projections"]
        base = f.get("baseline") or f.get("baseline_2025_4Q") or {}
        last = pr[-1]
        d_r = last["ratio_pct"] - base["ratio_post_pct"] if (base.get("ratio_post_pct") is not None and last["ratio_pct"] is not None) else None
        d_b = last["basic_ratio_pct"] - base["basic_ratio_post_pct"] if (base.get("basic_ratio_post_pct") is not None and last["basic_ratio_pct"] is not None) else None
        note = "Baseline (%s 적용후): 지급여력 %s%%, 기본자본 %s%%  |  2030 변화: 지급여력 %s%%p, 기본자본 %s%%p  |  잔액(콜 차감 대상): %s억원" % (
            f.get("baseline_quarter") or "최신", "-" if base.get("ratio_post_pct") is None else js_tofixed(base["ratio_post_pct"], 1),
            "-" if base.get("basic_ratio_post_pct") is None else js_tofixed(base["basic_ratio_post_pct"], 1),
            "-" if d_r is None else fmt_drop(d_r), "-" if d_b is None else fmt_drop(d_b), fmt(f.get("outstanding_bonds_total_eok")))
        row["fwd"] = {"status": "ok", "years": [str(p["year"]) for p in pr], "ratio": [p["ratio_pct"] for p in pr], "basic": [p["basic_ratio_pct"] for p in pr], "note": note,
                      "flag": bool(f.get("baseline_basis_flag")), "by_type": [p.get("basic_ratio_by_type_pct") for p in pr],
                      "if_t2": [p.get("basic_ratio_if_tier2_type_pct") for p in pr]}
    # ---- capsec bars + cells from the timeline JSON
    lst = tl["securities"].get(code)
    if not lst:
        row["cap"] = None
    else:
        by = {}
        for x in lst:
            y = int(str(x["issue_date"])[:4])
            e = by.setdefault(y, {"h": 0.0, "s": 0.0})
            if x["tier"] == "hybrid":
                e["h"] += float(x["face_eok"])
            elif x["tier"] == "subordinated":
                e["s"] += float(x["face_eok"])
        y0, y1 = min(by), max(by)
        years = [str(y) for y in range(y0, y1 + 1)]
        hy = [round(by.get(y, {"h": 0.0})["h"], 4) for y in range(y0, y1 + 1)]
        sb = [round(by.get(y, {"s": 0.0})["s"], 4) for y in range(y0, y1 + 1)]

        def cell(tier):
            allb = [x for x in lst if x["tier"] == tier]
            if not allb:
                return None
            outb = [x for x in allb if float(x["outstanding_eok"]) > 0]
            latest = None
            for x in outb:
                if not x.get("issue_date"):
                    continue
                if latest is None or x["issue_date"] > latest["issue_date"] or (x["issue_date"] == latest["issue_date"] and float(x["outstanding_eok"]) > float(latest["outstanding_eok"])):
                    latest = x
            total = sum(float(x["face_eok"]) for x in allb)
            calls = [x for x in outb if x.get("call_date") and x["call_date"] >= ref]
            nd = ne = None
            if calls:
                nd = sorted(x["call_date"] for x in calls)[0]
                ne = sum(float(x["outstanding_eok"]) for x in calls if x["call_date"] == nd)
            rate = "—" if (latest is None or latest.get("coupon_pct") is None) else js_tofixed(float(latest["coupon_pct"]), 2) + "%"
            return {"rate": rate, "issued": fmt(total) + "억", "call": ("—" if nd is None else nd + " (" + fmt(ne) + "억)")}
        row["cap"] = {"years": years, "hybrid": hy, "sub": sb, "hybrid_cell": cell("hybrid"), "sub_cell": cell("subordinated")}
    out[code] = row
# names: 원수사명 from the master dump
for code in out:
    out[code]["name"] = inp[code]["name"]
json.dump(out, open(HERE + "e2_expected" + SUF + ".json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
with open(HERE + "e2_expected" + SUF + ".txt", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("reference date (max as_of of the timeline) = %s ; rev %s\n" % (ref, audit_io.resolved_rev()))
    for code in out:
        r = out[code]
        fh.write("%s %s | t1 %s%% (mine %s) %s | t2 %s%% (mine %s) | %s\n" % (code, r["name"], r["t1"]["pct"], r["t1"]["pct_mine"], "NOSEC" if r["t1"]["nosec"] else "", r["t2"]["pct"], r["t2"]["pct_mine"], r["note"]))
print("wrote", len(out), "companies; reference date", ref)
