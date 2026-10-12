# -*- coding: utf-8 -*-
"""h2: INDEPENDENT re-check of the 기본자본 소진율 (tier1) at the new pin.

Spec (unchanged definition + the 2026-10-13 change):
   tier1 % = max( 항목 53 인정(legacy) / (SCR_pre x 15%) , 신규 기본자본형 / (SCR_pre x 10%) ),
             legacy = min(item53, item6), 신규 기본자본형 = max(0, item6 - legacy - 보완자본형 신종(등재부 type=tier2 의 합))
   printed limit tier1_hybrid_limit_eok: binding leg = legacy_15 -> SCR x 15% ; basic_10 -> SCR x 10% ; NO binding leg (no legacy, no new basic) -> SCR x 10% (changed 2026-10-13)
   overflow = max(0, legacy - 15% SCR) + max(0, new - 10% SCR)  (also the value of tier2 JSON tier1_overflow_into_tier2_eok)
Checks also: utilization_pct identical to the previous pin (dbbffcb5), 하나생명 238.2, 교보 70.1, DB손보 151.6 (owner decision: stays tier1; not flagged again).
Independent: my own dump of the master (a2) + pinned registry + pinned JSON; nothing imported from scripts/ or src/.   Output h2_tier1_check_<rev>.txt"""
import json
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

REV = audit_io.resolved_rev()
OLD = "dbbffcb5"
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
reg = audit_io.load_json("data/bonds/capital_tier_registry.json")["companies"]
pub1 = {r["code"]: r for r in audit_io.load_json("kics_tier1_utilization.json")["results"]}
old1 = {r["code"]: r for r in audit_io.load_json("kics_tier1_utilization.json", OLD)["results"]}
pub2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}


def z(x):
    return 0.0 if x is None else x


def pp(r, k):
    x = r.get("i%d_post" % k)
    return x if x is not None else r.get("i%d_pre" % k)


L = ["PIN rev=%s registry=%s tier1=%s tier2=%s" % (REV, audit_io.sha12("data/bonds/capital_tier_registry.json"), audit_io.sha12("kics_tier1_utilization.json"),
                                                    audit_io.sha12("kics_tier2_utilization.json"))]
bad_pct, bad_lim, bad_ovf1, bad_ovf2, bad_legs, bad_old = [], [], [], [], [], []
noleg = []
rows = {}
for code in sorted(inp):
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
    lim_expect = 0.15 * scr if binding == "legacy_15" else 0.10 * scr
    ovf = max(0.0, legacy - 0.15 * scr) + max(0.0, new - 0.10 * scr)
    p = pub1[code]
    rows[code] = (pct, binding, lim_expect, ovf)
    if p.get("utilization_pct") is None or abs(pct - p["utilization_pct"]) > 0.15:
        bad_pct.append((code, r["name"], round(pct, 3), p.get("utilization_pct")))
    if p.get("tier1_hybrid_limit_eok") is None or abs(lim_expect - p["tier1_hybrid_limit_eok"]) > 0.6:
        bad_lim.append((code, r["name"], binding, round(lim_expect, 1), p.get("tier1_hybrid_limit_eok"), p.get("binding_leg")))
    if (p.get("binding_leg") or None) != binding:
        bad_legs.append((code, r["name"], binding, p.get("binding_leg")))
    for key, want in (("tier1_legacy_limit_eok", 0.15 * scr), ("tier1_basic_new_limit_eok", 0.10 * scr)):
        if p.get(key) is None or abs(p[key] - want) > 0.6:
            bad_legs.append((code, r["name"], key, round(want, 1), p.get(key)))
    if abs(ovf - z(p.get("tier1_hybrid_overflow_eok"))) > 0.6:
        bad_ovf1.append((code, r["name"], round(ovf, 1), p.get("tier1_hybrid_overflow_eok")))
    if abs(ovf - z(pub2[code].get("tier1_overflow_into_tier2_eok"))) > 0.6:
        bad_ovf2.append((code, r["name"], round(ovf, 1), pub2[code].get("tier1_overflow_into_tier2_eok")))
    if p.get("utilization_pct") != old1[code].get("utilization_pct"):
        bad_old.append((code, r["name"], old1[code].get("utilization_pct"), p.get("utilization_pct")))
    if binding is None:
        noleg.append((code, r["name"], round(0.10 * scr, 1), p.get("tier1_hybrid_limit_eok"), round(0.15 * scr, 1)))
L.append("utilization_pct mine vs published: %d / %d within 0.15 pp (rounding of the one-decimal field)" % (len(inp) - len(bad_pct), len(inp)))
for x in bad_pct:
    L.append("   MISMATCH %s %s mine %s pub %s" % x)
L.append("printed limit tier1_hybrid_limit_eok (legacy_15 -> 15%% SCR, basic_10 -> 10%%, no binding leg -> 10%%): %d / %d equal" % (len(inp) - len(bad_lim), len(inp)))
for x in bad_lim:
    L.append("   MISMATCH %s %s binding %s expected %s published %s (published binding_leg %s)" % x)
L.append("binding_leg / legacy-limit / new-limit fields: %d mismatches" % len(bad_legs))
for x in bad_legs:
    L.append("   MISMATCH %s" % (x,))
L.append("overflow: tier1 JSON tier1_hybrid_overflow_eok %d / %d equal ; tier2 JSON tier1_overflow_into_tier2_eok %d / %d equal" % (
    len(inp) - len(bad_ovf1), len(inp), len(inp) - len(bad_ovf2), len(inp)))
for x in bad_ovf1 + bad_ovf2:
    L.append("   MISMATCH %s" % (x,))
L.append("no-legacy / no-binding companies (limit must now be 10%% x SCR): %d" % len(noleg))
n_ok = sum(1 for x in noleg if x[3] is not None and abs(x[3] - x[2]) <= 0.6)
L.append("   of which printed limit == SCR x 10%%: %d ; still printing SCR x 15%%: %d" % (n_ok, sum(1 for x in noleg if x[3] is not None and abs(x[3] - x[4]) <= 0.6 and abs(x[3] - x[2]) > 0.6)))
L.append("utilization_pct unchanged vs the previous pin %s : %d / %d unchanged%s" % (OLD, len(inp) - len(bad_old), len(inp), "" if not bad_old else "  CHANGED: %s" % bad_old))
for code, nm in (("KR0097", "하나생명"), ("KR0073", "교보"), ("KR0011", "DB손보")):
    L.append("   %s %s: mine %.1f published %s (previous pin %s) binding %s limit printed %s" % (
        code, nm, rows[code][0], pub1[code]["utilization_pct"], old1[code]["utilization_pct"], pub1[code].get("binding_leg"), pub1[code].get("tier1_hybrid_limit_eok")))
open(HERE + "h2_tier1_check_%s.txt" % REV, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
