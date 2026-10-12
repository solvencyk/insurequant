# -*- coding: utf-8 -*-
"""b2: (1) the coordinator's extra audit item - does reclassifying a security between tier1 and tier2 change the 보완자본 소진율, and how much
of a reclassified security is inside item 47 vs outside BOTH displays (하나생명, 교보 2024-11), plus the consistency view of 코리안리 /
농협생명 / 푸본현대;  (2) 100%+ companies: is the limit really binding in the issuer's own headline (item 3);
(3) tier1 bucket sensitivity for companies that hold both legacy (15%) and non-legacy (10%) amounts.

Reads: a2_inputs_2026_2Q.json (my own dump of kics_disclosure.json), registry + published tier1/tier2 JSON from the pinned git revision.
Imports nothing from scripts/ or src/.   Outputs: b2_gap_and_regulation_<rev>.txt / .csv
"""
import csv
import json
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
reg = audit_io.load_json("data/bonds/capital_tier_registry.json")["companies"]
pub1 = {r["code"]: r for r in audit_io.load_json("kics_tier1_utilization.json")["results"]}
pub2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}
L = ["PIN rev=%s registry=%s tier1=%s tier2=%s" % (audit_io.resolved_rev(), audit_io.sha12("data/bonds/capital_tier_registry.json"),
                                                audit_io.sha12("kics_tier1_utilization.json"), audit_io.sha12("kics_tier2_utilization.json"))]
rows = []


def v(c, k, col="pre"):
    return inp[c].get("i%d_%s" % (k, col))


def sec_amount(code, date_prefix):
    for s in reg[code]["securities"]:
        if (s.get("issue_date") or "").startswith(date_prefix):
            return s
    return None


# ---------------------------------------------------------------- (1) 하나생명 / 교보
L.append("== (1) tier1 -> tier2 reclassification: does it move the 보완자본 소진율?  tier2 numerator = issuer item 47 (적용후), minus 49, minus 53/54 -- it is read from the")
L.append("   issuer's own reclassification (item 13 = 보완자본으로 재분류하는 항목), NOT from the per-security type.  Proof by construction: type enters only tier1 (exclusion)")
L.append("   and the forward model; the tier2 numerator formula has no type input.  Quantification of what that leaves outside both displays:")
for code, date_prefix, label in (("KR0097", "2023-03-31", "하나생명 제1회"), ("KR0073", "2024-11-12", "교보 2024-11-12")):
    s = sec_amount(code, date_prefix)
    scr = v(code, 14)
    cap10 = 0.10 * scr
    limit50 = 0.5 * scr
    item6 = v(code, 6)
    l53 = v(code, 53) or 0.0
    x = v(code, 13) - v(code, 49)
    n2 = pub2[code]["numerator_eok"]
    i47 = v(code, 47, "post")
    stock = s["amount_eok"]
    # tier1-type pool in the issuer's table = this security + other basic-type items (item6 - legacy - other tier2-type securities)
    other_t2 = sum(x2["amount_eok"] for x2 in reg[code]["securities"] if x2["type"] == "tier2" and x2 is not s and (x2.get("issuer_type") or x2["type"]) == "tier2")
    pool_other = max(0.0, item6 - l53 - stock - other_t2)
    overflow = max(0.0, pool_other + stock - cap10)          # what a tier1-type security above the 10% cap pushes into 보완자본 (inside item 13/47)
    inside47 = min(stock, overflow)
    outside = stock - inside47
    n2_alt = n2 + outside
    L.append("  [%s] security %s stock %.2f | SCR_pre %.1f -> 10%% cap %.1f, 50%% limit %.1f | item6 %.1f, legacy53 %.1f, other tier2-type %.1f, other tier1-type pool %.1f" % (
        label, s["issue_date"], stock, scr, cap10, limit50, item6, l53, other_t2, pool_other))
    L.append("        X = item13 - item49 = %.1f ; item47(post) = %s ; published tier2 N2 = %.2f (%.1f%%) ; registry type=%s issuer_type=%s" % (
        x, i47, n2, pub2[code]["utilization_pct"], s["type"], s.get("issuer_type")))
    L.append("        issuer overflow model (tier1-type, 10%% cap): overflow = max(0, %.1f + %.1f - %.1f) = %.2f  => inside item 47: %.2f (%.1f%% of the security) ; outside BOTH displays: %.2f (%.1f%%)" % (
        pool_other, stock, cap10, overflow, inside47, 100 * inside47 / stock, outside, 100 * outside / stock))
    L.append("        tier2 utilization if the missing part were added: (%.2f + %.2f) / %.1f = %.2f%%  (published %.1f%%, +%.1f%%p)" % (
        n2, outside, limit50, n2_alt / limit50 * 100, pub2[code]["utilization_pct"], n2_alt / limit50 * 100 - pub2[code]["utilization_pct"]))
    t1_cur = pub1[code]["utilization_pct"]
    legacy_leg = min(l53, item6) / (0.15 * scr) * 100
    new_leg = (pool_other + stock) / cap10 * 100
    L.append("        tier1 now %.1f%% (registry type %s => security %s). Issuer-basis (tier1-type): legacy leg %.1f%%, new-basic leg %.1f%% => display %.1f%%" % (
        t1_cur, s["type"], "excluded from the tier1 numerator" if s["type"] == "tier2" else "counted in the tier1 numerator (the part below the 10% cap is basic capital, the part above it is inside item 47)",
        legacy_leg, new_leg, max(legacy_leg, new_leg)))
    rows.append({"company": label, "stock": round(stock, 2), "cap10": round(cap10, 2), "overflow_inside_item47": round(inside47, 2),
                 "outside_both": round(outside, 2), "tier2_published_pct": pub2[code]["utilization_pct"], "tier2_if_added_pct": round(n2_alt / limit50 * 100, 2),
                 "tier1_published_pct": t1_cur, "tier1_issuer_basis_pct": round(max(legacy_leg, new_leg), 2)})
# time-series fit of the 하나생명 overflow model (other_t must stay >= 0)
c = "KR0097"
kd = json.load(open(ROOT + "/kics_disclosure.json", encoding="utf-8"))
ser = {}
for r in kd:
    if r["원보험사코드"] == c and r["항목번호"] in (13, 14, 49):
        try:
            ser.setdefault(r["공시분기"], {})[r["항목번호"]] = float(str(r.get("값")).replace(",", ""))
        except Exception:
            pass
fit = []
for q in sorted(ser):
    d = ser[q]
    if 13 in d and 49 in d and 14 in d:
        xx = d[13] - d[49]
        ov = max(0.0, 1798.75 - 0.10 * d[14])
        fit.append((q, xx, ov, xx - ov))
L.append("  하나생명 overflow-only model, other_t = X_t - max(0, 1798.75 - 10%% SCR_t): " + "; ".join("%s %.1f" % (q, o) for q, _, _, o in fit))
L.append("        min other_t = %.1f (>= 0 in all %d quarters => overflow-only model feasible); whole-stock model (other = X - 1798.75) is negative in %d of %d quarters" % (
    min(o for *_, o in fit), len(fit), sum(1 for q, xx, ov, o in fit if xx - 1798.75 < -20), len(fit)))

# ---------------------------------------------------------------- 코리안리 / 농협생명 / 푸본현대
L.append("")
L.append("== consistency view of 코리안리 / 농협생명 / 푸본현대 (registry tier2 = issuer tier2?) -- necessary condition only (the sum of deductions is NOT proof)")
for code in ("KR1000", "KR0104", "KR0083"):
    t2 = sum(s["amount_eok"] for s in reg[code]["securities"] if s["type"] == "tier2")
    n2 = pub2[code]["numerator_eok"]
    x = v(code, 13) - v(code, 49)
    l53 = v(code, 53) or 0.0
    L.append("  %s %s: tier2-type amount %.1f ; published N2 (item 47 적용후 basis) %.2f ; X (2026.2Q) %.1f ; legacy 53 %.1f ; N2 - tier2-type = %.1f (other 보완자본 items inside item 47) ; X - 53 - tier2-type = %.1f" % (
        code, inp[code]["name"], t2, n2, x, l53, n2 - t2, x - l53 - t2))
    rows.append({"company": inp[code]["name"], "tier2_type_amount": round(t2, 2), "N2_pub": n2, "X": round(x, 1)})

# ---------------------------------------------------------------- (2) 100%+ closure with the issuer headline
L.append("")
L.append("== (2) 100%+ companies: is the limit really binding in the issuer's own headline?")
for code in sorted(inp):
    p1, p2 = pub1[code].get("utilization_pct"), pub2[code].get("utilization_pct")
    if (p2 or 0) > 100:
        t3 = v(code, 3, "post") if v(code, 3, "post") is not None else v(code, 3)
        z = v(code, 49) or 0.0
        l54 = v(code, 54) or 0.0
        l53 = v(code, 53) or 0.0
        scr = v(code, 14)
        ovf = max(0.0, l53 - 0.15 * scr)
        lim = 0.5 * scr
        L.append("  tier2 %s %s published %.1f%% : headline item3(post) %.2f - item49 %.2f - item54 %.2f - legacy신종 over 15%% %.2f = %.2f vs 50%% limit %.2f (item48 printed %s) => %s ; excess N2 - limit = %.2f (not recognised as 지급여력금액)" % (
            code, inp[code]["name"], p2, t3, z, l54, ovf, t3 - z - l54 - ovf, lim, v(code, 48), "BINDING (closes)" if abs(t3 - z - l54 - ovf - lim) <= 2.0 else "NOT closing", pub2[code]["numerator_eok"] - lim))
    if (p1 or 0) > 100:
        scr = v(code, 14)
        cap10 = 0.10 * scr
        item6 = v(code, 6)
        x = v(code, 13) - v(code, 49)
        L.append("  tier1 %s %s published %.1f%% : item6 %.1f, legacy53 %s, 10%% cap %.1f, 15%% cap %.1f ; X = item13-item49 = %.1f (reclassified inside the issuer table; necessary: X >= overflow) ; i2 post-pre = %s" % (
            code, inp[code]["name"], p1, item6, v(code, 53), cap10, 0.15 * scr, x,
            None if (v(code, 2, "post") is None) else round(v(code, 2, "post") - v(code, 2), 2)))
        if code == "KR0076":
            L.append("        아이엠라이프 TFI step: i2 post - pre = %.2f vs 5%% x SCR_pre = %.2f => the issuer's basic hybrids hit the cap in BOTH worlds (10%% pre, 15%% post)" % (
                v(code, 2, "post") - v(code, 2), 0.05 * scr))

# ---------------------------------------------------------------- (3) tier1 bucket sensitivity
L.append("")
L.append("== (3) tier1: how legacy (15%) and non-legacy (10%) amounts combine is not stated in 별표22 -> sensitivity for companies holding both")
for code in ("KR0002", "KR0005", "KR0071", "KR0083", "KR0008"):
    p = pub1[code]
    leg = p["tier1_legacy_eok"]
    new = p["tier1_basic_new_eok"]
    scr = p["scr_eok"]
    a = max(leg / (0.15 * scr), new / (0.10 * scr)) * 100
    b = (leg + new) / (0.15 * scr) * 100
    cc = (leg + new) / (0.10 * scr) * 100
    d = max(new / (0.10 * scr), (leg + new) / (0.15 * scr)) * 100
    L.append("  %s %s: legacy %.2f new-basic %.2f SCR %.0f | separate buckets (published) max(%.1f%%, %.1f%%) = %.1f%% ; joint 15%% pool %.1f%% ; joint 10%% pool %.1f%% ; max(new/10%%, (legacy+new)/15%%) %.1f%%" % (
        code, inp[code]["name"], leg, new, scr, leg / (0.15 * scr) * 100, new / (0.10 * scr) * 100, a, b, cc, d))
    rows.append({"company": inp[code]["name"], "legacy": leg, "new_basic": new, "pct_separate": round(a, 1), "pct_joint15": round(b, 1), "pct_joint10": round(cc, 1), "pct_max_new10_joint15": round(d, 1)})

open(HERE + "b2_gap_and_regulation" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
allk = []
for r in rows:
    for k in r:
        if k not in allk:
            allk.append(k)
with open(HERE + "b2_gap_and_regulation" + SUF + ".csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=allk)
    w.writeheader()
    w.writerows(rows)
print("\n".join(L))
