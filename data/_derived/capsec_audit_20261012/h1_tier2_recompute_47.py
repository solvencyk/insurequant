# -*- coding: utf-8 -*-
"""h1: INDEPENDENT 47-company recomputation of the 보완자본 소진율 under the NEW owner rule (2026-10-12 night + coordinator correction 2026-10-13).

Spec used (taken from the coordinator's message and TODO.md, not from the implementation):
   numerator = 항목 47 (적용 전 열; 발행사 인쇄 관행은 R0~R5 로 정규화하되 숫자는 같다) - 항목 49 (인쇄 47 이 49 를 포함하는 INCL 일 때)
               - 채권원장 신종 - 채권원장 후순위
   채권원장 차감액 = 2026.2Q 분자 기준일 현재 잔액(outstanding) 중  issue_date <= 2022-12-31  AND  past_call_outstanding = false  인 증권,
                    신종(hybrid)·후순위(subordinated) 따로.  인쇄 항목 53·54 는 차감에 쓰지 않는다(*_printed_eok 로만 보존).
   분모 = 항목 14 값(경과조치 적용 전) x 50%.  R0: 항목 3(보완자본)=0 이면 0.  항목 47~54 원문 부재(NA)면 null.
Independence: reads only my own dump of kics_disclosure.json (a2_inputs_2026_2Q.json, regenerated from the pinned revision) and the pinned ledger /
published JSON.  Imports nothing from scripts/ or src/.

Sensitivity variants (reported, not used for the verdict):
   date : past-call decided by me at the numerator date 2026-06-30 (first call date < 2026-06-30 and still outstanding) instead of the ledger flag
          (the flag is relative to each bond's own as_of, which is 2025-12-31 for the 22 stale ledger rows)
   min  : the first owner wording (2026-10-12 night, TODO.md) min(printed 53/54, ledger pre-2023 stock)
   rec  : ledger legacy 후순위 with the 잔존만기 체감 (Ⅲ.3.다.(2)) instead of plain outstanding
Output: h1_tier2_recompute_47_<rev>.csv / .json / h1_tier2_summary_<rev>.txt
"""
import csv
import json
import math
import sys
from datetime import date

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

REV = audit_io.resolved_rev()
TOL = 2.0              # 억원, two rounded cells
PCT_TOL = 0.1          # %p (coordinator)
AS_OF = date(2026, 6, 30)
CUT = "2022-12-31"

inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
pub2 = {r["code"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}
ledger = {c["code"]: c for c in audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]}
PIN = "rev=%s master=%s ledger=%s tier2=%s" % (REV, audit_io.sha12("kics_disclosure.json"), audit_io.sha12("data/bonds/capital_securities_fy2026h1.json"),
                                              audit_io.sha12("kics_tier2_utilization.json"))


def v(r, k, col="pre"):
    return r.get("i%d_%s" % (k, col))


def z(x):
    return 0.0 if x is None else x


def scoped_47(code):
    """my own normalisation of the printed 항목 47: returns dict(rule, scope, b_pre, b_post, limit).  INCL = the issuer's printed 47 is the total supplementary
    capital incl. the 해약환급금 부족분 초과분 (항목 49), i.e. 47 ~ 항목 3 while 49 > 0."""
    r = inp[code]
    scr = v(r, 14)
    limit = 0.5 * scr
    t3p, t3q = v(r, 3), v(r, 3, "post")
    t3_post = t3q if t3q is not None else t3p
    e_pre, e_post = v(r, 47), v(r, 47, "post")
    a49 = z(v(r, 49))
    base = {"limit": limit, "scr": scr, "a49": a49}
    if t3_post is not None and abs(t3_post) <= TOL and (t3p is None or abs(t3p) <= TOL):
        return dict(base, rule="R0", scope="-", b_pre=0.0, b_post=0.0)
    if e_pre is None and e_post is None:
        return dict(base, rule="NA", scope="-", b_pre=None, b_post=None)
    incl = (e_pre is not None and t3p is not None and abs(e_pre - t3p) <= TOL and a49 > TOL)
    adj = a49 if incl else 0.0
    b_pre = None if e_pre is None else e_pre - adj
    b_post = None if e_post is None else e_post - adj
    scope = "INCL" if incl else "EXCL"
    return dict(base, rule="?", scope=scope, b_pre=b_pre, b_post=b_post)


def first_call_passed(b, mode):
    """past-call at the numerator date (mode 'date'); the ledger flag otherwise"""
    if mode == "flag":
        return bool(b.get("past_call_outstanding"))
    cd = b.get("call_date")
    if not cd:
        return False
    y, m, d = (int(x) for x in cd.split("-"))
    return date(y, m, d) < AS_OF


def rec_rate(b):
    mat = b.get("legal_maturity")
    if not mat:
        return 1.0
    y, m, d = (int(x) for x in mat.split("-"))
    yrs = (date(y, m, d) - AS_OF).days / 365.25
    return 1.0 if yrs >= 5 else (0.0 if yrs <= 0 else max(0.0, 1.0 - 0.20 * math.ceil(5 - yrs)))


def ledger_deduction(code, mode="flag", haircut=False):
    c = ledger.get(code)
    out = {"hybrid": 0.0, "subordinated": 0.0, "unknown_vintage": 0.0, "excluded_pastcall": [], "n_pre2023": 0, "stale": False, "as_of": None, "has_row": c is not None}
    if not c:
        return out
    out["as_of"] = c.get("as_of")
    for b in c.get("bonds", []):
        o = (b.get("outstanding_mn") or 0) / 100.0
        if o <= 0:
            continue
        iss = b.get("issue_date") or ""
        if not iss:
            out["unknown_vintage"] += o
            continue
        if iss > CUT:
            continue
        out["n_pre2023"] += 1
        if (b.get("as_of") or "") < "2026-06-30":
            out["stale"] = True
        if first_call_passed(b, mode):
            out["excluded_pastcall"].append((b.get("name", "")[:30], iss, b.get("call_date"), round(o, 2), b["tier"]))
            continue
        amt = o * (rec_rate(b) if (haircut and b["tier"] == "subordinated") else 1.0)
        out[b["tier"]] += amt
    return out


def numerator(code, mode="flag", haircut=False, minrule=False):
    s = scoped_47(code)
    if s["rule"] == "NA":
        return dict(s, N2=None, D_h=None, D_s=None)
    if s["rule"] == "R0":
        return dict(s, N2=0.0, D_h=0.0, D_s=0.0, N2_raw=0.0)
    d = ledger_deduction(code, mode, haircut)
    dh, ds = d["hybrid"], d["subordinated"]
    if minrule:
        dh = min(dh, z(v(inp[code], 53)))
        ds = min(ds, z(v(inp[code], 54)))
    base = s["b_pre"] if s["b_pre"] is not None else s["b_post"]
    raw = base - dh - ds
    return dict(s, N2=max(0.0, raw), N2_raw=raw, D_h=dh, D_s=ds, led=d)


rows = []
for code in sorted(inp):
    r = inp[code]
    p = pub2[code]
    a = numerator(code)                       # the spec
    b_date = numerator(code, mode="date")
    b_min = numerator(code, minrule=True)
    b_rec = numerator(code, haircut=True)
    lim = a["limit"]
    pct = None if a["N2"] is None else a["N2"] / lim * 100
    pct_date = None if b_date["N2"] is None else b_date["N2"] / lim * 100
    pct_min = None if b_min["N2"] is None else b_min["N2"] / lim * 100
    pct_rec = None if b_rec["N2"] is None else b_rec["N2"] / lim * 100
    pub_pct = p.get("utilization_pct")
    pub_num = p.get("numerator_eok")
    led = a.get("led") or {}
    tfi_off_mine = None if a["b_pre"] is None else max(0.0, a["b_pre"])
    row = {
        "code": code, "name": r["name"], "rule_mine": a["rule"], "scope_mine": a["scope"], "rule_pub": p.get("rule"), "scope_pub": p.get("item47_scope"),
        "limit_mine": round(lim, 2), "limit_pub": p.get("tier2_limit_eok"),
        "b_pre": None if a["b_pre"] is None else round(a["b_pre"], 2), "item49": a["a49"],
        "ledger_hybrid_mine": None if a["D_h"] is None else round(a["D_h"], 2), "ledger_sub_mine": None if a["D_s"] is None else round(a["D_s"], 2),
        "ledger_hybrid_pub": p.get("grandfathered_hybrid_eok"), "ledger_sub_pub": p.get("grandfathered_subordinated_eok"),
        "printed53_pub": p.get("grandfathered_hybrid_printed_eok"), "printed54_pub": p.get("grandfathered_subordinated_printed_eok"),
        "printed53_master": v(r, 53), "printed54_master": v(r, 54),
        "N2_mine": None if a["N2"] is None else round(a["N2"], 2), "N2_raw_mine": None if a.get("N2_raw") is None else round(a["N2_raw"], 2), "N2_pub": pub_num,
        "pct_mine": None if pct is None else round(pct, 3), "pct_pub": pub_pct,
        "diff_pp": None if (pct is None or pub_pct is None) else round(pct - pub_pct, 3),
        "match": (pct is None and pub_pct is None) or (pct is not None and pub_pct is not None and abs(pct - pub_pct) <= PCT_TOL + 0.05),
        "N2_diff": None if (a["N2"] is None or pub_num is None) else round(a["N2"] - pub_num, 2),
        "tfi_off_mine": None if tfi_off_mine is None else round(tfi_off_mine, 2), "tfi_off_pub": p.get("numerator_tfi_off_eok"),
        "tfi_off_pct_mine": None if (tfi_off_mine is None or not lim) else round(tfi_off_mine / lim * 100, 3), "tfi_off_pct_pub": p.get("utilization_pct_tfi_off"),
        "pct_variant_date": None if pct_date is None else round(pct_date, 3), "pct_variant_min": None if pct_min is None else round(pct_min, 3),
        "pct_variant_haircut": None if pct_rec is None else round(pct_rec, 3),
        "ledger_stale": led.get("stale"), "ledger_as_of": led.get("as_of"), "ledger_unknown_vintage_sub_or_hyb": None if not led else round(led["unknown_vintage"], 2),
        "pastcall_excluded": "; ".join("%s %s call %s %.0f %s" % x for x in (led.get("excluded_pastcall") or [])),
    }
    rows.append(row)

cols = list(rows[0].keys())
with open(HERE + "h1_tier2_recompute_47_%s.csv" % REV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
json.dump(rows, open(HERE + "h1_tier2_recompute_47_%s.json" % REV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

L = ["PIN %s" % PIN]
n_ok = sum(1 for x in rows if x["match"])
L.append("tier2 utilization, new rule, mine vs published (tolerance %.1f pp): match %d / %d" % (PCT_TOL, n_ok, len(rows)))
for x in rows:
    if not x["match"]:
        L.append("  MISMATCH %s %s mine=%s pub=%s (diff %s pp) | rule mine %s / pub %s scope %s / %s | N2 mine %s pub %s | ledger h/s mine %s/%s pub %s/%s" % (
            x["code"], x["name"], x["pct_mine"], x["pct_pub"], x["diff_pp"], x["rule_mine"], x["rule_pub"], x["scope_mine"], x["scope_pub"], x["N2_mine"], x["N2_pub"],
            x["ledger_hybrid_mine"], x["ledger_sub_mine"], x["ledger_hybrid_pub"], x["ledger_sub_pub"]))
bad_led = [x for x in rows if x["ledger_hybrid_mine"] is not None and x["ledger_hybrid_pub"] is not None and
           (abs(x["ledger_hybrid_mine"] - x["ledger_hybrid_pub"]) > 0.06 or abs(x["ledger_sub_mine"] - x["ledger_sub_pub"]) > 0.06)]
L.append("ledger deduction amounts (hybrid / subordinated) vs published grandfathered_*_eok: %d companies differ" % len(bad_led))
for x in bad_led:
    L.append("  %s %s mine %s/%s pub %s/%s" % (x["code"], x["name"], x["ledger_hybrid_mine"], x["ledger_sub_mine"], x["ledger_hybrid_pub"], x["ledger_sub_pub"]))
bad_pr = [x for x in rows if (x["printed53_pub"] is not None and x["printed53_master"] is not None and abs(x["printed53_pub"] - x["printed53_master"]) > 0.06) or
          (x["printed54_pub"] is not None and x["printed54_master"] is not None and abs(x["printed54_pub"] - x["printed54_master"]) > 0.06)]
L.append("printed 53/54 kept as *_printed_eok vs the master cells: %d companies differ" % len(bad_pr))
for x in bad_pr:
    L.append("  %s %s pub %s/%s master %s/%s" % (x["code"], x["name"], x["printed53_pub"], x["printed54_pub"], x["printed53_master"], x["printed54_master"]))
bad_tfi = [x for x in rows if x["tfi_off_pct_mine"] is not None and x["tfi_off_pct_pub"] is not None and abs(x["tfi_off_pct_mine"] - x["tfi_off_pct_pub"]) > PCT_TOL + 0.05]
L.append("적용 전 열 (TFI-off) utilization vs published utilization_pct_tfi_off: %d / %d differ" % (len(bad_tfi), len(rows)))
for x in bad_tfi:
    L.append("  %s %s mine %s pub %s" % (x["code"], x["name"], x["tfi_off_pct_mine"], x["tfi_off_pct_pub"]))
L.append("limit (item14 x 50%%): %d / %d equal" % (sum(1 for x in rows if x["limit_pub"] is not None and abs(x["limit_mine"] - x["limit_pub"]) <= 0.06), len(rows)))
L.append("rule marks: mine uses INCL/EXCL scope; published item47_scope equal for %d / %d (R-name is the issuer-convention marker, numbers do not depend on it)" % (
    sum(1 for x in rows if x["scope_mine"] == x["scope_pub"] or x["scope_mine"] == "-"), len(rows)))
L.append("")
L.append("sensitivity (companies whose pct moves by > 0.1 pp under the variant):")
for key, nm in (("pct_variant_date", "past-call decided at 2026-06-30 instead of the ledger flag"), ("pct_variant_min", "min(printed 53/54, ledger) (first owner wording)"),
                ("pct_variant_haircut", "ledger legacy 후순위 with 잔존만기 체감")):
    mv = [x for x in rows if x[key] is not None and x["pct_mine"] is not None and abs(x[key] - x["pct_mine"]) > 0.1]
    L.append("  %s: %d companies" % (nm, len(mv)))
    for x in mv:
        L.append("      %s %s spec %.1f -> %.1f (published %s)" % (x["code"], x["name"], x["pct_mine"], x[key], x["pct_pub"]))
unk = [x for x in rows if x["ledger_unknown_vintage_sub_or_hyb"]]
L.append("ledger bonds without an issue_date (cannot be placed before/after 2023, not deducted): %d companies" % len(unk))
for x in unk:
    L.append("      %s %s %s eok" % (x["code"], x["name"], x["ledger_unknown_vintage_sub_or_hyb"]))
open(HERE + "h1_tier2_summary_%s.txt" % REV, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
