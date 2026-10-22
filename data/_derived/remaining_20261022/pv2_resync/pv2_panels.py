# -*- coding: utf-8 -*-
"""Independent check 2: panel_csm_combo.json / panel_compare.json vs git HEAD copy (leaf diff) + recompute KR0073 values from HEAD masters."""
import json
import subprocess
import sys
from collections import defaultdict

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
sys.stdout.reconfigure(encoding="utf-8")


def gj(rev, path):
    out = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO, capture_output=True, check=True).stdout
    return json.loads(out.decode("utf-8"))


def wj(path):
    with open(REPO + "/" + path, encoding="utf-8") as f:
        return json.load(f)


def leaves(o, p=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, p + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, p + (i,))
    else:
        yield p, o


def leafdiff(a, b):
    da, db = dict(leaves(a)), dict(leaves(b))
    ch = []
    for k in set(da) | set(db):
        if da.get(k, "<absent>") != db.get(k, "<absent>"):
            ch.append((k, da.get(k, "<absent>"), db.get(k, "<absent>")))
    return sorted(ch, key=lambda t: str(t[0]))


# ---------- combo
P = "data/csm_combo/panel_csm_combo.json"
old, new = gj("HEAD", P), wj(P)
d = leafdiff(old, new)
print("combo leaf diffs:", len(d))
for k, x, y in d:
    print("  ", "/".join(map(str, k)), x, "->", y)
print("combo: top-level keys identical", list(old) == list(new), "| meta keys identical", list(old["meta"]) == list(new["meta"]))
print("combo: non-KR0073 leaf diffs:", sum(1 for k, _, _ in d if not (k[0] == "companies" and k[1] == "KR0073") and not (k[:3] == ("meta", "restated", "KR0073"))))

port = gj("HEAD", "insurance_liability_portfolio.json")
bs = gj("HEAD", "IFRS17_BS.json")
side = gj("HEAD", "data/_derived/ilp_restated_comparative.json")
cols = new["meta"]["columns"]
pf = defaultdict(dict)
for r in port:
    if r["원보험사코드"] == "KR0073":
        pf[r["공시분기"]][r["항목번호"]] = float(r["값"]) if r["값"] is not None else None
bs20 = {r["공시분기"]: float(r["값"]) for r in bs if r["원보험사코드"] == "KR0073" and r["항목번호"] == 20}
rest = {c["quarter"]: c for c in side["cells"] if c["company_code"] == "KR0073"}
print("sidecar restated cells for KR0073:", {q: (c["restated_bs_insurance_contract_liability_eok"], c["bs_item20_fy2023_original_eok"]) for q, c in rest.items()})
q = "2023.4Q"
dd = pf[q]
row = new["companies"]["KR0073"]["q"][q]
exp_idx = {
    "lic_total": dd.get(10), "lrc_dart": dd.get(14),
    "bs20": round(rest[q]["restated_bs_insurance_contract_liability_eok"], 2) if q in rest else round(bs20[q] / 100, 1),
    "lic_unsplit": dd.get(13),
}
for name, e in exp_idx.items():
    got = row[cols.index(name)]
    print(f"  combo KR0073 {q} {name}: expected(from masters)={e} panel={got} {'OK' if e is not None and abs(e-got) < 0.006 else 'MISMATCH'}")
print("  bs20 via BS item20/100 =", round(bs20[q] / 100, 2), "(equals sidecar restated?)", abs(bs20[q] / 100 - rest[q]["restated_bs_insurance_contract_liability_eok"]) < 0.006)
print("  meta.restated.KR0073 =", new["meta"]["restated"].get("KR0073"))
# every KR0073 quarter, columns 9 lic_total, 17 lrc_dart vs masters (non-restated quarters must match item10/14)
bad = 0
for qq, r in new["companies"]["KR0073"]["q"].items():
    d2 = pf.get(qq, {})
    for name, it in (("lic_total", 10), ("lrc_dart", 14), ("lic_unsplit", 13)):
        v = r[cols.index(name)]
        e = d2.get(it)
        if qq != "2023.4Q" and name == "lic_unsplit":
            continue  # unsplit may be derived
        if (v is None) != (e is None) or (v is not None and abs(v - e) > 0.006):
            bad += 1
            print("   KR0073", qq, name, "panel", v, "master", e)
print("  KR0073 all-quarter lic_total/lrc_dart consistency issues:", bad)

# ---------- compare
P2 = "data/compare/panel_compare.json"
old2, new2 = gj("HEAD", P2), wj(P2)
d2 = leafdiff(old2, new2)
print("\ncompare leaf diffs:", len(d2))
ids = [m["id"] for m in new2["metrics"]]
for k, x, y in d2:
    mid = ids[k[1]] if k[0] == "metrics" else ""
    print("  ", "/".join(map(str, k)), f"[{mid}]", x, "->", y)
print("compare: leaf diffs not in KR0073 value arrays:", sum(1 for k, _, _ in d2 if not (k[0] == "metrics" and k[2] == "v" and k[3] == "KR0073")))
print("compare top keys:", list(new2)[:12])
quarters = new2.get("quarters") or new2.get("meta", {}).get("quarters")
print("quarters (len):", len(quarters), quarters[:10] if quarters else None)
QI = {q: i for i, q in enumerate(quarters)}

# recompute from masters
pl = gj("HEAD", "PL_breakdown.json")
ni = {r["공시분기"]: float(r["값"]) for r in pl if r["원보험사코드"] == "KR0073" and r["항목번호"] == 24 and r["값"] is not None}
eq = {r["공시분기"]: float(r["값"]) for r in bs if r["원보험사코드"] == "KR0073" and r["항목번호"] == 3}
asset = {r["공시분기"]: float(r["값"]) for r in bs if r["원보험사코드"] == "KR0073" and r["항목번호"] == 1}
m = {x["id"]: x for x in new2["metrics"]}


def put(v):
    return None if v is None else v


print("\nROE recompute KR0073 (own code):")
fails = 0
for qq in quarters:
    y, n = int(qq[:4]), int(qq[5])
    if (y, n) < (2024, 1):
        continue
    e1, e0, n24 = eq.get(qq), eq.get(f"{y-1}.4Q"), ni.get(qq)
    if None in (e1, e0, n24) or e1 <= 0 or e0 <= 0:
        exp = None
    else:
        exp = n24 * 4.0 / n / ((e0 + e1) / 2.0) * 100.0
    got = m["roe"]["v"]["KR0073"][QI[qq]]
    ok = (exp is None and got is None) or (exp is not None and got is not None and abs(round(exp, 1) - got) < 1e-9)
    fails += not ok
    print(f"  {qq}: expected={None if exp is None else round(exp, 3)} panel={got} {'OK' if ok else 'MISMATCH'}")
print("ROE mismatches:", fails)
for mid, src in (("equity", eq), ("assets", asset)):
    f = 0
    for qq in quarters:
        e = src.get(qq)
        got = m[mid]["v"]["KR0073"][QI[qq]]
        exp = None if e is None else e / 100.0
        okk = (exp is None and got is None) or (exp is not None and got is not None and abs(exp - got) < 0.5001)
        # panel may be rounded integer or raw; accept both
        f += not okk
        if not okk:
            print("  MISMATCH", mid, qq, exp, got)
    print(f"{mid} KR0073 all quarters recompute mismatches: {f}; 2023.4Q panel={m[mid]['v']['KR0073'][QI['2023.4Q']]} master/100={None if src.get('2023.4Q') is None else src['2023.4Q']/100}; 2024.4Q panel={m[mid]['v']['KR0073'][QI['2024.4Q']]}")
