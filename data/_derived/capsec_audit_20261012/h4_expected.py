# -*- coding: utf-8 -*-
"""h4: EXPECTED screen values of K-ICS.html for every company at the NEW pin, built independently of the page code.

Differences against e2 (the dbbffcb5 version), all from the 2026-10-13 specs (coordinator message, publishing + designer changelogs, my own tickets):
   tier1 number line : limit Y = SCR x 15% only when the legacy leg binds, else SCR x 10% (also when no leg binds) -> computed here from my own SCR
   tier2 number line: numerator and 「경과조치 기발행 후순위」 amount = MY recompute (h1: ledger pre-2023 stock, past-call excluded), not the JSON's
   reference line   : 신종 / 후순위 outstanding = sum of the ledger bonds (mine)
   donut tooltips   : 100%+ -> two lines  ['사용: 100%+ (실제 X%)', over-note]; the 「보완자본형이면 X%」 part only when X (1 decimal) differs from the displayed value
   forward          : years whose capital (basic capital) is <= 0 are NOT drawn (null) and the tooltip says 「자본잠식」; the note's 2030 change for such a metric is 「—」;
                      negatives are written with the triangle; one notice line names the clipped metric(s)
   issuance cells   : the next call may be date-only (a candidate bond with a null outstanding on the earliest date); bars carry est[] (추정 rows)
Sources: pinned published JSON, my own dump of the master (a2), my own recompute files h1 (tier2) and my tier1 formula, the pinned ledger and timeline.
Output h4_expected_<rev>.json (pasted into the browser audit) and h4_expected_<rev>.txt (human check)."""
import json
import math
import sys
from decimal import Decimal, ROUND_HALF_UP

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

REV = audit_io.resolved_rev()
t1 = {r["code"]: r for r in audit_io.load_json("kics_tier1_utilization.json")["results"]}
t2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}
fwd = {r["insurer_code"]: r for r in audit_io.load_json("kics_forward_capital.json")}
tl = audit_io.load_json("kics_capital_securities_timeline.json")
reg = audit_io.load_json("data/bonds/capital_tier_registry.json")["companies"]
ledger = {c["code"]: c for c in audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]}
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
h1 = {x["code"]: x for x in json.load(open(HERE + "h1_tier2_recompute_47_%s.json" % REV, encoding="utf-8"))}


def js_tofixed(x, nd):
    """JavaScript Number.prototype.toFixed (exact binary value, half up)"""
    q = Decimal(1).scaleb(-nd)
    return str(Decimal(x).quantize(q, rounding=ROUND_HALF_UP))


def jr(x):
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))


def fmt(x):
    if x is None:
        return "-"
    return ("△" if x < 0 else "") + "{:,}".format(abs(jr(x)))


def tri(v, dp):
    """the page's fmtTriPct: triangle for negatives (unless the rounded text is zero)"""
    if v is None:
        return "-"
    t = js_tofixed(abs(v), dp)
    return ("△" if (v < 0 and float(t) != 0) else "") + t + "%"


def fmt_drop(d):
    return ("△" if d < 0 else "+") + js_tofixed(abs(d), 1)


def z(x):
    return 0.0 if x is None else x


def pp(r, k):
    x = r.get("i%d_post" % k)
    return x if x is not None else r.get("i%d_pre" % k)


# ---- my tier1 (same formula as h2, my own code)
def my_tier1(code):
    r = inp[code]
    scr = r["i14_pre"]
    item6 = z(pp(r, 6))
    l53 = z(r.get("i53_pre"))
    secs = reg.get(code, {}).get("securities", [])
    excl = sum(s["amount_eok"] for s in secs if s["type"] == "tier2")
    legacy = min(l53, max(item6, 0.0))
    new = max(0.0, item6 - legacy - excl)
    p_leg = legacy / (0.15 * scr) * 100 if scr else 0.0
    p_new = new / (0.10 * scr) * 100 if scr else 0.0
    pct = max(p_leg, p_new)
    binding = None if pct == 0 else ("legacy_15" if p_leg >= p_new else "basic_10")
    return {"scr": scr, "item6": item6, "legacy": legacy, "new": new, "pct": pct, "binding": binding}


ref = ""
for lst in tl["securities"].values():
    for b in lst:
        if b.get("as_of") and b["as_of"] > ref:
            ref = b["as_of"]

out = {}
problems = []
for code in sorted(t1):
    a, b = t1[code], t2[code]
    m1 = my_tier1(code)
    m2 = h1[code]
    row = {"name": inp[code]["name"]}
    # ------------------------------------------------------------------ tier1
    pct1 = a["utilization_pct"]
    scr = m1["scr"]
    if m1["binding"] == "basic_10":
        X1, Y1 = m1["new"], 0.10 * scr
    elif m1["binding"] == "legacy_15":
        X1, Y1 = m1["legacy"], 0.15 * scr
    else:
        X1, Y1 = 0.0, 0.10 * scr          # 2026-10-13: no binding leg -> the 10% rule (printed limit)
    line1 = "기본자본 자본증권 %s억원 / 인정한도 %s억원" % (fmt(X1), fmt(Y1))
    if m1["binding"] == "legacy_15" and m1["legacy"] > 0:
        line1 += " 경과조치 기발행분 %s억원 포함" % fmt(m1["legacy"])
    led = ledger.get(code)
    n_out = sum(1 for x in led.get("bonds", []) if (x.get("outstanding_mn") or 0) > 0) if led else 0
    nosec_expected = (m1["item6"] <= 0.5) and n_out == 0
    if abs(m1["pct"] - pct1) > 0.15:
        problems.append("tier1 %s mine %.2f json %s" % (code, m1["pct"], pct1))
    unconf = bool(a.get("type_unconfirmed"))
    unconf_pct = a.get("tier1_pct_if_unconfirmed_tier2")
    unconf_differs = unconf_pct is not None and js_tofixed(unconf_pct, 1) != js_tofixed(pct1, 1)
    unconf_text = ("기본자본형/보완자본형 미확정 신종 포함" + (", 보완자본형이면 %s%%" % js_tofixed(unconf_pct, 1) if unconf_differs else "")) if unconf else None
    row["t1"] = {"pct": pct1, "pct_mine": round(m1["pct"], 3),
                 "aria": "기본자본 자본증권 인정한도 소진율 " + (("100%% 초과 (%s%%)" % js_tofixed(pct1, 1)) if pct1 > 100 else ("%s%%" % js_tofixed(pct1, 1))),
                 "nosec": nosec_expected, "nosec_json": a.get("no_capital_securities"), "unconf": unconf, "unconf_text": unconf_text,
                 "excl_t2": a.get("tier1_excluded_tier2_type_eok") or 0, "over_note": "초과분은 보완자본으로 재분류"}
    # ------------------------------------------------------------------ tier2
    pct2 = b["utilization_pct"]
    if (m2["pct_mine"] is None) != (pct2 is None) or (pct2 is not None and abs(m2["pct_mine"] - pct2) > 0.15):
        problems.append("tier2 %s mine %s json %s" % (code, m2["pct_mine"], pct2))
    N2 = m2["N2_mine"]
    lim2 = m2["limit_mine"]
    dh, ds = m2["ledger_hybrid_mine"], m2["ledger_sub_mine"]
    line2 = "보완자본 한도 적용 전 %s / 보완자본 한도 %s억원" % ("—" if N2 is None else fmt(N2) + "억원", fmt(lim2))
    if (ds or 0) > 0:
        line2 += " 경과조치 기발행 후순위 %s억원" % fmt(ds)
    lapse_line = None
    sup = b.get("supplementary_capital_eok")
    if N2 == 0 and sup and sup > 0:
        lapse = b.get("lapse_excess_item49_eok")
        if not (lapse and lapse > 0) and not (((dh or 0) + (ds or 0)) > 0):
            lapse = sup
        if lapse and lapse > 0:
            lapse_line = "해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 %s억원" % fmt(lapse)
    # reference line: outstanding hybrid / subordinated from the ledger bonds (mine)
    bh = sum((x.get("outstanding_mn") or 0) for x in (led or {}).get("bonds", []) if x["tier"] == "hybrid") / 100.0
    bs = sum((x.get("outstanding_mn") or 0) for x in (led or {}).get("bonds", []) if x["tier"] == "subordinated") / 100.0
    if abs(bh - (a.get("hybrid_outstanding_eok") or 0)) > 0.6 or abs(bs - (a.get("subordinated_outstanding_eok") or 0)) > 0.6:
        problems.append("outstanding %s ledger %.1f/%.1f json %s/%s" % (code, bh, bs, a.get("hybrid_outstanding_eok"), a.get("subordinated_outstanding_eok")))
    ref_line = ("참고 — 자본성증권 발행잔액: 신종 %s억원 · 후순위 %s억원" % (fmt(bh), fmt(bs))) if (bh > 0 or bs > 0) else None
    lines = [line1, line2]
    if lapse_line:
        lines.append(lapse_line)
    if ref_line:
        lines.append(ref_line)
    if pct2 is None:
        aria2 = "보완자본 한도 소진율 " + (b.get("reason") or "데이터 없음")
    else:
        aria2 = "보완자본 한도 소진율 " + (("100%% 초과 (%s%%)" % js_tofixed(pct2, 1)) if pct2 > 100 else ("%s%%" % js_tofixed(pct2, 1)))
    row["t2"] = {"pct": pct2, "pct_mine": m2["pct_mine"], "aria": aria2, "na": pct2 is None, "over_note": "초과분은 지급여력금액에서 불인정"}
    row["note"] = " | ".join(lines)
    # ------------------------------------------------------------------ forward
    f = fwd.get(code)
    if f is None:
        row["fwd"] = None
    elif f.get("status") != "ok":
        row["fwd"] = {"status": f.get("status"), "reason": f.get("exclusion_reason")}
    else:
        pr = f["projections"]
        base = f.get("baseline") or f.get("baseline_2025_4Q") or {}
        # exhausted = the capital (basic capital) of that year is <= 0 (my reading of the amounts, not the flag)
        exR = [p["capital_eok"] <= 0 for p in pr]
        exB = [p["basic_capital_eok"] <= 0 for p in pr]
        for i, p in enumerate(pr):
            if exR[i] != bool(p.get("capacity_exhausted")) or exB[i] != bool(p.get("basic_capacity_exhausted")):
                problems.append("flag/amount disagree %s %s" % (code, p["year"]))
        last = pr[-1]
        d_r = None if (exR[-1] or base.get("ratio_post_pct") is None or last["ratio_pct"] is None) else last["ratio_pct"] - base["ratio_post_pct"]
        d_b = None if (exB[-1] or base.get("basic_ratio_post_pct") is None or last["basic_ratio_pct"] is None) else last["basic_ratio_pct"] - base["basic_ratio_post_pct"]
        note = "Baseline (%s 적용후): 지급여력 %s, 기본자본 %s  |  2030 변화: 지급여력 %s, 기본자본 %s  |  잔액(콜 차감 대상): %s억원" % (
            f.get("baseline_quarter") or "최신", tri(base.get("ratio_post_pct"), 1), tri(base.get("basic_ratio_post_pct"), 1),
            "—" if d_r is None else fmt_drop(d_r) + "%p", "—" if d_b is None else fmt_drop(d_b) + "%p", fmt(f.get("outstanding_bonds_total_eok")))
        clipped = []
        if any(exR):
            clipped.append("자본잠식(가용자본<=0)")
        if any(exB):
            clipped.append("기본자본 잠식(가용 기본자본<=0)")
        clip_note = (" · ".join(clipped) + " 해의 비율은 표시하지 않습니다") if clipped else None
        row["fwd"] = {"status": "ok", "years": [str(p["year"]) for p in pr],
                      "ratio": [None if exR[i] else p["ratio_pct"] for i, p in enumerate(pr)], "basic": [None if exB[i] else p["basic_ratio_pct"] for i, p in enumerate(pr)],
                      "exR": exR, "exB": exB, "note": note, "clip_note": clip_note,
                      "flag": bool(f.get("baseline_basis_flag")), "by_type": [p.get("basic_ratio_by_type_pct") for p in pr],
                      "if_t2": [p.get("basic_ratio_if_tier2_type_pct") for p in pr]}
    # ------------------------------------------------------------------ issuance bars + cells (timeline JSON, verified against the ledger in e9)
    lst = tl["securities"].get(code)
    if not lst:
        row["cap"] = None
    else:
        by = {}
        for x in lst:
            y = int(str(x["issue_date"])[:4])
            e = by.setdefault(y, {"h": 0.0, "s": 0.0, "est": False})
            if x["tier"] == "hybrid":
                e["h"] += float(x["face_eok"])
            elif x["tier"] == "subordinated":
                e["s"] += float(x["face_eok"])
            if x.get("estimated") is True:
                e["est"] = True
        y0, y1 = min(by), max(by)
        years = [str(y) for y in range(y0, y1 + 1)]
        hy = [round(by.get(y, {"h": 0.0})["h"], 4) for y in range(y0, y1 + 1)]
        sb = [round(by.get(y, {"s": 0.0})["s"], 4) for y in range(y0, y1 + 1)]
        est = [bool(by.get(y, {"est": False})["est"]) for y in range(y0, y1 + 1)]

        def cell(tier):
            allb = [x for x in lst if x["tier"] == tier]
            if not allb:
                return None
            outb = [x for x in allb if x.get("outstanding_eok") is not None and float(x["outstanding_eok"]) > 0]
            latest = None
            for x in outb:
                if not x.get("issue_date"):
                    continue
                if latest is None or x["issue_date"] > latest["issue_date"] or (x["issue_date"] == latest["issue_date"] and float(x["outstanding_eok"]) > float(latest["outstanding_eok"])):
                    latest = x
            total = sum(float(x["face_eok"]) for x in allb)
            # call candidates: call date >= reference date and the balance is either unknown (null) or positive (a balance of 0 = redeemed = no candidate)
            cands = [x for x in allb if x.get("call_date") and x["call_date"] >= ref and (x.get("outstanding_eok") is None or float(x["outstanding_eok"]) > 0)]
            nd = ne = None
            if cands:
                nd = sorted(x["call_date"] for x in cands)[0]
                same = [x for x in cands if x["call_date"] == nd]
                ne = None if any(x.get("outstanding_eok") is None for x in same) else sum(float(x["outstanding_eok"]) for x in same)
            rate = "—" if (latest is None or latest.get("coupon_pct") is None) else js_tofixed(float(latest["coupon_pct"]), 2) + "%"
            call = "—" if nd is None else (nd + ("" if ne is None else " (" + fmt(ne) + "억)"))
            return {"rate": rate, "issued": fmt(total) + "억", "call": call}
        row["cap"] = {"years": years, "hybrid": hy, "sub": sb, "est": est, "hybrid_cell": cell("hybrid"), "sub_cell": cell("subordinated")}
    out[code] = row
json.dump(out, open(HERE + "h4_expected_%s.json" % REV, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
with open(HERE + "h4_expected_%s.txt" % REV, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("reference date (max as_of of the timeline) = %s ; rev %s\n" % (ref, REV))
    fh.write("problems while building the expectation (JSON vs my own numbers): %s\n" % (problems or "none"))
    for code in out:
        r = out[code]
        fh.write("%s %s | t1 %s%% | t2 %s%% | %s\n" % (code, r["name"], r["t1"]["pct"], r["t2"]["pct"], r["note"]))
print("wrote", len(out), "companies; reference date", ref, "; problems:", problems or "none")
