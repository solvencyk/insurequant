# -*- coding: utf-8 -*-
"""e7: the three downloadable sheets that the designer's 496d359e put back into the download list (기본자본소진율 / 보완자본소진율 / 자본비율전망) must say
what the screen says.  Invariant: the file the gate checks = the file the user gets.
Compares public_exports/<sheet>.json with the root JSON files for all 47 companies:
   기본자본소진율  '기본자본 소진율'        == kics_tier1_utilization.json utilization_pct
   보완자본소진율  '보완자본 소진율'        == kics_tier2_utilization.json utilization_pct   (blank when the JSON is null)
   자본비율전망    '지급여력비율 전망' / '기본자본비율 전망' per year == kics_forward_capital.json projections (46 ok companies x 5 years)
   manifest.json build_id and the three sheet names are listed
Run with AUDIT_REV=HEAD (public_exports changed in 24a3dd6c, the JSON in dbbffcb5).   Output e7_public_sheets_vs_json_<rev>.txt
"""
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
t1 = {r["company"]: r for r in audit_io.load_json("kics_tier1_utilization.json")["results"]}
t2 = {r["company"]: r for r in audit_io.load_json("kics_tier2_utilization.json")["results"]}
fw = {r["insurer_name"]: r for r in audit_io.load_json("kics_forward_capital.json")}
s1 = audit_io.load_json("public_exports/기본자본소진율.json")
s2 = audit_io.load_json("public_exports/보완자본소진율.json")
s3 = audit_io.load_json("public_exports/자본비율전망.json")
man = audit_io.load_json("public_exports/manifest.json")
L = ["PIN rev=%s  manifest build_id=%s" % (audit_io.resolved_rev(), man.get("build_id"))]
L.append("manifest lists: " + ", ".join(s for s in ("기본자본소진율", "보완자본소진율", "자본비율전망") if s in (man.get("sheets") or [])) or "none")
bad = []


def alias(name):
    """sheet company names are display names; JSON rows use their own - match by exact name, then by the longer containing the shorter"""
    return name


def find(d, name):
    if name in d:
        return d[name]
    for k, v in d.items():
        if k.replace("MG_", "") == name or name in k or k in name:
            return v
    return None


# --- sheet 1
rows1 = [r for r in s1 if r["항목명"] == "기본자본 소진율"]
n1 = 0
for r in rows1:
    j = find(t1, r["원수사명"])
    if j is None:
        bad.append(("sheet1 company not in JSON", r["원수사명"]))
        continue
    n1 += 1
    if r["값"] is None or abs(r["값"] - j["utilization_pct"]) > 0.051:
        bad.append(("sheet1 value", r["원수사명"], r["값"], j["utilization_pct"]))
# --- sheet 2
rows2 = [r for r in s2 if r["항목명"] == "보완자본 소진율"]
n2 = 0
for r in rows2:
    j = find(t2, r["원수사명"])
    if j is None:
        bad.append(("sheet2 company not in JSON", r["원수사명"]))
        continue
    n2 += 1
    jv = j["utilization_pct"]
    if (r["값"] is None) != (jv is None) or (jv is not None and abs(r["값"] - jv) > 0.051):
        bad.append(("sheet2 value", r["원수사명"], r["값"], jv))
# --- sheet 3
n3 = 0
for r in s3:
    if r["항목명"] not in ("지급여력비율 전망", "기본자본비율 전망"):
        continue
    j = find(fw, r["원수사명"])
    if j is None or j.get("status") != "ok":
        bad.append(("sheet3 company not ok in JSON", r["원수사명"], r["공시분기"]))
        continue
    p = next((x for x in j["projections"] if str(x["year"]) == str(r["공시분기"])), None)
    if p is None:
        bad.append(("sheet3 year missing in JSON", r["원수사명"], r["공시분기"]))
        continue
    n3 += 1
    jv = p["ratio_pct"] if r["항목명"] == "지급여력비율 전망" else p["basic_ratio_pct"]
    if r["값"] is None or abs(r["값"] - jv) > 0.0051:
        bad.append(("sheet3 value", r["원수사명"], r["공시분기"], r["항목명"], r["값"], jv))
# --- sheets vs MY OWN recompute (h1 tier2, regenerated for this pin): numerator and the two deducted ledger amounts; tier1 limits
import json as _json
_h1 = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/h1_tier2_recompute_47_%s.json" % audit_io.resolved_rev()
try:
    mine = {x["name"]: x for x in _json.load(open(_h1, encoding="utf-8"))}
except FileNotFoundError:
    mine = {}
inp = _json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/a2_inputs_2026_2Q.json", encoding="utf-8"))
scr = {v["name"]: v["i14_pre"] for v in inp.values()}
bad_mine = []
n_mine = 0
if mine:
    wanted = (("보완자본 인정한도 소진 분자", "N2_mine"), ("경과조치 인정 신종자본증권(레거시)", "ledger_hybrid_mine"), ("경과조치 인정 후순위채무(레거시)", "ledger_sub_mine"))
    for r in s2:
        for item, key in wanted:
            if r["항목명"] == item and r["공시분기"] == "2026.2Q":
                m = find(mine, r["원수사명"])
                if m is None:
                    bad_mine.append(("sheet2 company not in my recompute", r["원수사명"]))
                    continue
                n_mine += 1
                ref = m[key]
                if ref is None and key != "N2_mine" and r["값"] == 0.0:
                    continue          # 교보라이프플래닛 (항목 47~54 원문 부재, numerator null): the ledger has no bonds, the sheet states 0.0 - true
                if (r["값"] is None) != (ref is None) or (ref is not None and abs(r["값"] - ref) > 0.06):
                    bad_mine.append(("sheet2 vs my recompute", r["원수사명"], item, r["값"], ref))
    # the two 「기발행 ...」 stock rows = ALL pre-2023 ledger bonds still outstanding (past-call ones included; the deducted amount is the 「레거시」 row above)
    _led_code = {c["code"]: c for c in audit_io.load_json("data/bonds/capital_securities_fy2026h1.json")["companies"]}
    _led = {v["name"]: _led_code[k] for k, v in inp.items() if k in _led_code}      # sheet names are the master names
    for r in s2:
        if r["항목명"] in ("기발행 신종자본증권(보완자본 재분류분)", "기발행 후순위채무") and r["공시분기"] == "2026.2Q":
            tier = "hybrid" if "신종" in r["항목명"] else "subordinated"
            c = find(_led, r["원수사명"])
            if c is None:
                bad_mine.append(("sheet2 stock row: company not in ledger", r["원수사명"]))
                continue
            ref = sum((b.get("outstanding_mn") or 0) for b in c.get("bonds", []) if b["tier"] == tier and b.get("issue_date") and b["issue_date"] <= "2022-12-31") / 100.0
            n_mine += 1
            if r["값"] is None or abs(r["값"] - ref) > 0.06:
                bad_mine.append(("sheet2 stock row vs my ledger sum", r["원수사명"], r["항목명"], r["값"], round(ref, 2)))
    for r in s1:
        if r["항목명"] in ("기본자본 인정한도(SCR x 15%)", "기본자본 인정한도(엄격, SCR x 10%)") and r["공시분기"] == "2026.2Q":
            f = 0.15 if "15%" in r["항목명"] else 0.10
            s = find(scr, r["원수사명"])
            n_mine += 1
            if s is None or abs(r["값"] - f * s) > 0.06:
                bad_mine.append(("sheet1 limit vs my SCR", r["원수사명"], r["항목명"], r["값"], None if s is None else round(f * s, 2)))
L_mine = "sheets vs my own recompute (tier2 numerator / deducted hybrid / deducted subordinated, tier1 15%% and 10%% limits): %d cells checked, %d mismatches" % (n_mine, len(bad_mine))
# --- coverage in the other direction
cov1 = {r["원수사명"] for r in rows1}
cov2 = {r["원수사명"] for r in rows2}
cov3 = {r["원수사명"] for r in s3 if r["항목명"] == "지급여력비율 전망"}
L.append("sheet 기본자본소진율: %d company rows checked (JSON has %d), sheet 보완자본소진율: %d (JSON %d), sheet 자본비율전망: %d year-points of %d companies (JSON ok companies %d)" % (
    n1, len(t1), n2, len(t2), n3, len(cov3), sum(1 for v in fw.values() if v.get("status") == "ok")))
L.append("mismatches (sheet vs published JSON): %d" % len(bad))
L.append(L_mine)
for b in bad_mine:
    L.append("   " + " | ".join(str(x) for x in b))
for b in bad:
    L.append("   " + " | ".join(str(x) for x in b))
# the clamped forward rows - what the downloaded sheet says about them
for nm in ("예별손해보험", "MG_예별손해보험", "롯데손해보험"):
    for r in s3:
        if r["원수사명"] == nm and r["공시분기"] in ("2026", "2030") and r["항목명"] in ("지급여력비율 전망", "기본자본비율 전망"):
            L.append("   sheet row: %s %s %s = %s | 비고: %s" % (nm, r["공시분기"], r["항목명"], r["값"], (r["비고"] or "")[:90]))
open(HERE + "e7_public_sheets_vs_json" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
