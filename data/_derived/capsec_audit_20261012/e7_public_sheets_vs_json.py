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
# --- coverage in the other direction
cov1 = {r["원수사명"] for r in rows1}
cov2 = {r["원수사명"] for r in rows2}
cov3 = {r["원수사명"] for r in s3 if r["항목명"] == "지급여력비율 전망"}
L.append("sheet 기본자본소진율: %d company rows checked (JSON has %d), sheet 보완자본소진율: %d (JSON %d), sheet 자본비율전망: %d year-points of %d companies (JSON ok companies %d)" % (
    n1, len(t1), n2, len(t2), n3, len(cov3), sum(1 for v in fw.values() if v.get("status") == "ok")))
L.append("mismatches: %d" % len(bad))
for b in bad:
    L.append("   " + " | ".join(str(x) for x in b))
# the clamped forward rows - what the downloaded sheet says about them
for nm in ("예별손해보험", "MG_예별손해보험", "롯데손해보험"):
    for r in s3:
        if r["원수사명"] == nm and r["공시분기"] in ("2026", "2030") and r["항목명"] in ("지급여력비율 전망", "기본자본비율 전망"):
            L.append("   sheet row: %s %s %s = %s | 비고: %s" % (nm, r["공시분기"], r["항목명"], r["값"], (r["비고"] or "")[:90]))
open(HERE + "e7_public_sheets_vs_json" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
