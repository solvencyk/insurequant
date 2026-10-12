# -*- coding: utf-8 -*-
"""b1: INDEPENDENT 47-company recomputation of the 기본자본 / 보완자본 소진율 (2026.2Q), then comparison with the
published kics_tier1_utilization.json / kics_tier2_utilization.json.

Independence: reads kics_disclosure.json (through a2_inputs_2026_2Q.json = my own dump), the registry/census final CSV
(only for the per-security tier2-type amounts) and the per-bond ledger. It does NOT import anything from scripts/ or src/
(no capital_utilization_rules, apply_disclosure_utilization, forward_capital_simulation, kics_json_rules).

Definitions are taken from the ticket text and re-read from the regulation (research/新지급여력제도(K-ICS) 해설서.pdf):
  tier1 (기본자본 소진율) = 기본자본 자본증권 / 인정한도.
        분자 출발점 = item 6 (자본항목 중 보통주 이외의 자본증권), 보완자본형으로 확정된 증권만 제외.
        한도 = 총요구자본(경과조치 적용 전, item 14 값) x 10%; 2022년 이전 기발행(item 53)은 x 15%  (별표22 Ⅲ.2.다.(1)②, Ⅵ.1.가.(1)).
        두 갈래(기발행 / 신규 기본자본형) 중 한도에 먼저 차는 쪽 = max of the two ratios.
  tier2 (보완자본 소진율) = (item 47 적용후, 발행사 인쇄 관행 정규화) - item 49 - (item 53 + item 54) over item 14 x 50%
        (별표22 Ⅲ.2.마, Ⅵ.1.가.(2)(3), Ⅵ.1.라).

Three tier2 routes:
  A  literal ticket definition (item 47 + my own print-convention normalisation)            -> t2_*_mine
  B  closure through the issuer's own headline 보완자본 (item 3), independent of item 47      -> t2_closure_*
  V  vintage sensitivity: legacy 후순위 taken from the per-bond ledger (issued before 2023-01-01)
     instead of the issuer-printed item 54                                                   -> t2_*_vintage  (sensitivity only)

Outputs (this folder): b1_recompute_47.csv / .json / b1_summary.txt
"""
import csv
import json
import math
from datetime import date

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
TOL = 2.0          # 억원: two rounded cells
PCT_TOL = 0.1      # %p, ticket tolerance
AS_OF = date(2026, 6, 30)

import sys
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

assert audit_io.worktree_equals_head("kics_disclosure.json"), "master kics_disclosure.json differs from HEAD - a2 dump is not the committed state"
assert audit_io.worktree_equals_head("data/bonds/capital_securities_fy2026h1.json"), "ledger differs from HEAD"
PIN = "rev=%s registry=%s tier1=%s tier2=%s forward=%s" % (
    audit_io.resolved_rev(), audit_io.sha12("data/bonds/capital_tier_registry.json"), audit_io.sha12("kics_tier1_utilization.json"),
    audit_io.sha12("kics_tier2_utilization.json"), audit_io.sha12("kics_forward_capital.json"))

inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
reg = audit_io.load_json("data/bonds/capital_tier_registry.json")["companies"]
census = list(csv.DictReader(open(ROOT + "/data/_derived/capital_securities_classification_census_20261012/census_securities_final.csv",
                                  encoding="utf-8-sig")))
pub1 = {r["code"]: r for r in audit_io.load_json("kics_tier1_utilization.json")["results"]}
pub2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}
ledger = {c["code"]: c for c in json.load(open(ROOT + "/data/bonds/capital_securities_fy2026h1.json", encoding="utf-8"))["companies"]}


def v(r, k, col="pre"):
    return r.get("i%d_%s" % (k, col))


def pp(r, k):
    """post if present else pre"""
    x = v(r, k, "post")
    return x if x is not None else v(r, k, "pre")


def z(x):
    return 0.0 if x is None else x


# ----------------------------------------------------------------------------------------------------------------
# tier1
# ----------------------------------------------------------------------------------------------------------------
def tier2type_amounts(code):
    """excluded (tier2-type) amounts: registry current type / census-final type / issuer-basis type (issuer_type wins when present)"""
    secs = reg.get(code, {}).get("securities", [])
    cur = sum(s["amount_eok"] for s in secs if s["type"] == "tier2")
    iss = sum(s["amount_eok"] for s in secs if (s.get("issuer_type") or s["type"]) == "tier2")
    cen = sum(float(c["outstanding_eok"]) for c in census if c["code"] == code and c["type"] == "tier2")
    return cur, cen, iss


def tier1(code, excl):
    r = inp[code]
    scr = v(r, 14)
    item6 = z(pp(r, 6))
    l53 = z(v(r, 53))
    legacy = min(l53, max(item6, 0.0))
    new = max(0.0, item6 - legacy - excl)
    p_leg = legacy / (0.15 * scr) * 100 if scr else 0.0
    p_new = new / (0.10 * scr) * 100 if scr else 0.0
    return {"scr": scr, "item6": item6, "legacy": legacy, "new_basic": new, "excl_t2": excl,
            "pct_legacy15": p_leg, "pct_new10": p_new, "pct": max(p_leg, p_new),
            "binding": None if max(p_leg, p_new) == 0 else ("legacy_15" if p_leg >= p_new else "basic_10")}


# ----------------------------------------------------------------------------------------------------------------
# tier2
# ----------------------------------------------------------------------------------------------------------------
def tier2_literal(code):
    """Route A: ticket definition read literally; my own implementation of the issuer print-convention normalisation.
    Returns N2 (clamped at 0), N2_raw (unclamped), rule, scope, limit."""
    r = inp[code]
    scr = v(r, 14)
    limit = 0.5 * scr
    t3p, t3q = v(r, 3), v(r, 3, "post")
    t3_post = t3q if t3q is not None else t3p
    e_pre, e_post = v(r, 47), v(r, 47, "post")
    a49 = z(v(r, 49))
    l53, l54 = z(v(r, 53)), z(v(r, 54))
    base = {"limit": limit}
    if t3_post is not None and abs(t3_post) <= TOL and (t3p is None or abs(t3p) <= TOL):
        return dict(base, N2=0.0, N2_raw=0.0, N2_pre=0.0, rule="R0", scope="-")
    if e_pre is None and e_post is None:
        return dict(base, N2=None, N2_raw=None, N2_pre=None, rule="NA", scope="-")
    incl = (e_pre is not None and t3p is not None and abs(e_pre - t3p) <= TOL and a49 > TOL)
    adj = a49 if incl else 0.0
    b_pre = None if e_pre is None else e_pre - adj
    b_post = None if e_post is None else e_post - adj
    scope = "INCL" if incl else "EXCL"
    if b_pre is None:
        return dict(base, N2=max(0.0, b_post), N2_raw=b_post, N2_pre=None, rule="R5", scope=scope)
    if b_post is None:
        return dict(base, N2=max(0.0, b_pre), N2_raw=b_pre, N2_pre=max(0.0, b_pre), rule="R-nopost", scope=scope, note="47 적용후 미인쇄 -> 적용전 값")
    if abs(b_post - (b_pre - l53 - l54)) <= TOL:
        return dict(base, N2=max(0.0, b_post), N2_raw=b_post, N2_pre=max(0.0, b_pre), rule="R2", scope=scope)
    if l54 > TOL and abs(b_post - (b_pre - l53)) <= TOL:
        raw = b_post - l54
        return dict(base, N2=max(0.0, raw), N2_raw=raw, N2_pre=max(0.0, b_pre), rule="R4", scope=scope)
    if abs(b_post - b_pre) <= TOL:
        raw = b_pre - l53 - l54
        return dict(base, N2=max(0.0, raw), N2_raw=raw, N2_pre=max(0.0, b_pre), rule="R3", scope=scope)
    return dict(base, N2=max(0.0, b_post), N2_raw=b_post, N2_pre=max(0.0, b_pre), rule="R5", scope=scope)


def closure(code):
    """Route B: independent of item 47.  Issuer headline 보완자본 (item 3, after the limit):
         post world:  3post = min(N2, limit) + item49 + item54 + max(0, item53 - 15% x SCR)
         pre  world:  3pre  = min(N2pre, limit) + item49           (N2pre contains item 53 and item 54)
       => N2 candidates (valid when the limit does not bind; when it binds the identity returns the limit itself)."""
    r = inp[code]
    scr = v(r, 14)
    t3p, t3q = v(r, 3), v(r, 3, "post")
    a49 = z(v(r, 49))
    l53, l54 = z(v(r, 53)), z(v(r, 54))
    ovf15 = max(0.0, l53 - 0.15 * scr)
    c_post = None if t3q is None else t3q - a49 - l54 - ovf15
    c_pre = None if t3p is None else t3p - a49 - l53 - l54
    return {"c_post": c_post, "c_pre": c_pre}


def ledger_status_and_legacy(code):
    """vintage-based legacy 후순위: issued before 2023-01-01, outstanding, face and 잔존만기 체감 (20%p per year from 5y remaining)."""
    c = ledger.get(code)
    if not c:
        return None
    face = rec = unk = 0.0
    stale = False
    n_sub = 0
    for b in c.get("bonds", []):
        if b.get("tier") != "subordinated":
            continue
        n_sub += 1
        out = (b.get("outstanding_mn") or 0) / 100.0
        if (b.get("as_of") or "") < "2026-06-30":
            stale = True
        iss = b.get("issue_date") or ""
        if not iss:
            unk += out
            continue
        if iss >= "2023-01-01":
            continue
        face += out
        mat = b.get("legal_maturity")
        rate = 1.0
        if mat:
            y, m, d = (int(x) for x in mat.split("-"))
            yrs = (date(y, m, d) - AS_OF).days / 365.25
            rate = 1.0 if yrs >= 5 else (0.0 if yrs <= 0 else max(0.0, 1.0 - 0.20 * math.ceil(5 - yrs)))
        rec += out * rate
    if n_sub == 0:
        status = "no_subordinated_in_ledger"
    elif unk > 0:
        status = "unknown_vintage_bond"
    elif stale:
        status = "stale_ledger_2025-12-31"
    else:
        status = "ok"
    return {"face": face, "rec": rec, "unk": unk, "status": status}


rows = []
for code in sorted(inp):
    r = inp[code]
    cur, cen, iss = tier2type_amounts(code)
    t1_cur, t1_cen, t1_iss = tier1(code, cur), tier1(code, cen), tier1(code, iss)
    p1 = pub1[code]
    a = tier2_literal(code)
    b = closure(code)
    p2 = pub2[code]
    lim = a["limit"]
    pct_a = None if a["N2"] is None else a["N2"] / lim * 100 if lim else None
    e48p, e48q = v(r, 48), v(r, 48, "post")
    # closure verdict: published N2 (capped at the limit) must equal one of the two closure candidates
    n2p = p2.get("numerator_eok")
    cl_ok = None
    cl_used = None
    if n2p is not None:
        tgt = min(n2p, lim)
        for name in ("c_post", "c_pre"):
            if b[name] is not None and abs(b[name] - tgt) <= TOL:
                cl_ok, cl_used = True, name
                break
        else:
            cl_ok = False
    led = ledger_status_and_legacy(code)
    l54 = z(v(r, 54))
    removed54 = l54 if a["rule"] in ("R2", "R3", "R4") else 0.0
    n2_v = pct_v = None
    if led is not None and a["N2_raw"] is not None and led["status"] in ("ok", "stale_ledger_2025-12-31"):
        n2_v = max(0.0, a["N2_raw"] + removed54 - led["rec"])
        pct_v = n2_v / lim * 100 if lim else None
    row = {
        "code": code, "name": r["name"],
        "t1_scr": t1_cur["scr"], "t1_item6": t1_cur["item6"], "t1_legacy53_mine": round(t1_cur["legacy"], 2),
        "t1_legacy53_pub": p1.get("tier1_legacy_eok"),
        "t1_excl_t2_registry": cur, "t1_excl_t2_census": cen, "t1_excl_t2_issuerbasis": iss,
        "t1_new_basic_mine": round(t1_cur["new_basic"], 2), "t1_new_basic_pub": p1.get("tier1_basic_new_eok"),
        "t1_pct_mine": round(t1_cur["pct"], 3), "t1_pct_pub": p1.get("utilization_pct"),
        "t1_diff": None if p1.get("utilization_pct") is None else round(t1_cur["pct"] - p1["utilization_pct"], 3),
        "t1_match": p1.get("utilization_pct") is not None and abs(t1_cur["pct"] - p1["utilization_pct"]) <= PCT_TOL + 0.05,
        "t1_pct_census_type": round(t1_cen["pct"], 3), "t1_pct_issuer_basis": round(t1_iss["pct"], 3),
        "t1_binding_mine": t1_cur["binding"], "t1_binding_pub": p1.get("binding_leg"),
        "t1_overflow_mine": round(max(0.0, t1_cur["legacy"] - 0.15 * t1_cur["scr"]) + max(0.0, t1_cur["new_basic"] - 0.10 * t1_cur["scr"]), 2),
        "t1_overflow_pub_tier1json": p1.get("tier1_hybrid_overflow_eok"),
        "t1_overflow_pub_tier2json": p2.get("tier1_overflow_into_tier2_eok"),
        "t2_rule_mine": a["rule"], "t2_scope_mine": a["scope"],
        "t2_N2_mine": None if a["N2"] is None else round(a["N2"], 2),
        "t2_N2_raw_mine": None if a["N2_raw"] is None else round(a["N2_raw"], 2),
        "t2_limit_mine": round(lim, 2), "t2_limit_pub": p2.get("tier2_limit_eok"),
        "t2_pct_mine": None if pct_a is None else round(pct_a, 3),
        "t2_rule_pub": p2.get("rule"), "t2_scope_pub": p2.get("item47_scope"), "t2_N2_pub": n2p, "t2_pct_pub": p2.get("utilization_pct"),
        "t2_diff": None if (pct_a is None or p2.get("utilization_pct") is None) else round(pct_a - p2["utilization_pct"], 3),
        "t2_match": (pct_a is None and p2.get("utilization_pct") is None) or (
            pct_a is not None and p2.get("utilization_pct") is not None and abs(pct_a - p2["utilization_pct"]) <= PCT_TOL + 0.05),
        "t2_pct_tfi_off_mine": None if (a.get("N2_pre") is None or not lim) else round(a["N2_pre"] / lim * 100, 3),
        "t2_pct_tfi_off_pub": p2.get("utilization_pct_tfi_off"),
        "t2_closure_post": None if b["c_post"] is None else round(b["c_post"], 2),
        "t2_closure_pre": None if b["c_pre"] is None else round(b["c_pre"], 2),
        "t2_closure_ok": cl_ok, "t2_closure_used": cl_used,
        "t2_i48_pre_minus_half_scr": None if e48p is None else round(e48p - lim, 2),
        "t2_i48_post_minus_half_scr": None if e48q is None else round(e48q - lim, 2),
        "t2_item54_printed": l54, "t2_item54_removed_by_literal_rule": removed54,
        "t2_ledger_status": None if led is None else led["status"],
        "t2_ledger_legacy_sub_face": None if led is None else round(led["face"], 1),
        "t2_ledger_legacy_sub_rec": None if led is None else round(led["rec"], 1),
        "t2_ledger_unknown_vintage_sub": None if led is None else round(led["unk"], 1),
        "t2_N2_vintage": None if n2_v is None else round(n2_v, 2),
        "t2_pct_vintage": None if pct_v is None else round(pct_v, 3),
        "t2_pct_vintage_minus_pub": None if (pct_v is None or p2.get("utilization_pct") is None) else round(pct_v - p2["utilization_pct"], 2),
    }
    rows.append(row)

SUF = "_" + audit_io.resolved_rev()
cols = list(rows[0].keys())
with open(HERE + "b1_recompute_47" + SUF + ".csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
json.dump(rows, open(HERE + "b1_recompute_47" + SUF + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- summary
L = ["PIN: " + PIN]
n1 = sum(1 for x in rows if x["t1_match"])
n2 = sum(1 for x in rows if x["t2_match"])
nl = sum(1 for x in rows if x["t2_limit_pub"] is not None and abs(x["t2_limit_pub"] - x["t2_limit_mine"]) <= 0.51)
L.append("== b1 summary (2026.2Q, tolerance %.1f%%p) ==" % PCT_TOL)
L.append("tier1 pct match %d/47 ; legacy-leg amount match %d ; new-basic amount match %d" % (
    n1, sum(1 for x in rows if abs((x["t1_legacy53_pub"] or 0) - x["t1_legacy53_mine"]) <= 0.05),
    sum(1 for x in rows if abs((x["t1_new_basic_pub"] or 0) - x["t1_new_basic_mine"]) <= 0.06)))
for x in rows:
    if not x["t1_match"]:
        L.append("  tier1 MISMATCH %s %s mine=%s pub=%s" % (x["code"], x["name"], x["t1_pct_mine"], x["t1_pct_pub"]))
L.append("tier2 limit (item14 x 50%%) match %d/47" % nl)
ovf1 = [x for x in rows if x["t1_overflow_pub_tier1json"] is not None and abs(x["t1_overflow_mine"] - x["t1_overflow_pub_tier1json"]) <= 0.06]
ovf2 = [x for x in rows if x["t1_overflow_pub_tier2json"] is not None and abs(x["t1_overflow_mine"] - x["t1_overflow_pub_tier2json"]) <= 0.06]
L.append("tier1_overflow (legacy over 15%% SCR + new basic over 10%% SCR): tier1 JSON field match %d/47 ; tier2 JSON tier1_overflow_into_tier2_eok match %d/47" % (len(ovf1), len(ovf2)))
for x in rows:
    if x not in ovf2:
        L.append("  tier2-json overflow MISMATCH %s %s mine=%s pub=%s" % (x["code"], x["name"], x["t1_overflow_mine"], x["t1_overflow_pub_tier2json"]))
    if x not in ovf1:
        L.append("  tier1-json overflow MISMATCH %s %s mine=%s pub=%s" % (x["code"], x["name"], x["t1_overflow_mine"], x["t1_overflow_pub_tier1json"]))
nz = [(x["code"], x["name"][:6], x["t1_overflow_mine"]) for x in rows if x["t1_overflow_mine"] > 0]
L.append("  non-zero overflow companies (mine): " + ", ".join("%s %s %.1f" % t for t in nz))
L.append("tier2 literal-definition pct match %d/47" % n2)
for x in rows:
    if not x["t2_match"]:
        L.append("  tier2 MISMATCH %s %s mine=%s(%s raw N2=%s) pub=%s(%s N2=%s)" % (
            x["code"], x["name"], x["t2_pct_mine"], x["t2_rule_mine"], x["t2_N2_raw_mine"], x["t2_pct_pub"], x["t2_rule_pub"], x["t2_N2_pub"]))
off_ok = [x for x in rows if x["t2_pct_tfi_off_pub"] is not None and x["t2_pct_tfi_off_mine"] is not None and abs(x["t2_pct_tfi_off_mine"] - x["t2_pct_tfi_off_pub"]) <= PCT_TOL + 0.05]
off_n = [x for x in rows if x["t2_pct_tfi_off_pub"] is not None]
L.append("tier2 TFI-off (적용 전) pct match %d/%d" % (len(off_ok), len(off_n)))
for x in off_n:
    if x not in off_ok:
        L.append("  TFI-off MISMATCH %s %s mine=%s pub=%s" % (x["code"], x["name"], x["t2_pct_tfi_off_mine"], x["t2_pct_tfi_off_pub"]))
cl_known = [x for x in rows if x["t2_closure_ok"] is not None]
L.append("closure via issuer headline item 3: confirms published N2 for %d/%d companies with a numerator" % (
    sum(1 for x in cl_known if x["t2_closure_ok"]), len(cl_known)))
for x in cl_known:
    if not x["t2_closure_ok"]:
        L.append("  closure NOT closing: %s %s pub N2=%s closure_post=%s closure_pre=%s limit=%s" % (
            x["code"], x["name"], x["t2_N2_pub"], x["t2_closure_post"], x["t2_closure_pre"], x["t2_limit_mine"]))
L.append("item 48 (issuer-printed 보완자본 한도) minus 0.5 x item14(pre), |diff| > 1, companies with a 보완자본:")
for x in rows:
    if x["t2_N2_pub"] in (None, 0, 0.0) and x["t2_pct_pub"] in (None, 0.0) and (inp[x["code"]].get("i3_pre") or 0) <= 2:
        continue
    for k in ("t2_i48_pre_minus_half_scr", "t2_i48_post_minus_half_scr"):
        if x[k] is not None and abs(x[k]) > 1.0:
            L.append("  %s %s %s = %s" % (x["code"], x["name"], k, x[k]))
L.append("")
L.append("vintage sensitivity (ledger legacy 후순위 instead of the printed item 54), |pct diff| >= 0.5%p; ledger status shown:")
for x in rows:
    d = x["t2_pct_vintage_minus_pub"]
    if d is not None and abs(d) >= 0.5:
        L.append("  %s %s pub=%s%% vintage=%s%% (%+.1f)  print54=%s ledger_legacy_face=%s rec=%s status=%s" % (
            x["code"], x["name"], x["t2_pct_pub"], x["t2_pct_vintage"], d, x["t2_item54_printed"], x["t2_ledger_legacy_sub_face"],
            x["t2_ledger_legacy_sub_rec"], x["t2_ledger_status"]))
L.append("")
L.append("tier1 variants differing from the published state (registry vs census-final type vs issuer-basis type):")
for x in rows:
    if abs(x["t1_pct_mine"] - x["t1_pct_census_type"]) > 0.05 or abs(x["t1_pct_mine"] - x["t1_pct_issuer_basis"]) > 0.05:
        L.append("  %s %s registry=%s census=%s issuer_basis=%s published=%s" % (
            x["code"], x["name"], x["t1_pct_mine"], x["t1_pct_census_type"], x["t1_pct_issuer_basis"], x["t1_pct_pub"]))
open(HERE + "b1_summary" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
