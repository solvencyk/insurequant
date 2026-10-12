import sys, os, re, json, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_dart import *
here = os.path.dirname(os.path.abspath(__file__))
code = "KR0008"
cm = {}
for r in json.load(open(REPO + "/CSM_waterfall.json", encoding="utf-8")):
    cm[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
applied = {(r["quarter"], int(r["item"])): r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["code"] == code and r["master"] == "CSM_waterfall"}
out = open(here + "/f1_csm_kr0008.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/f1_csm_kr0008.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "quarter", "item", "applied_new", "mine(억)", "post-apply master", "in_plan", "cur-calibration", "verdict"])
LAB = {1: r"^기초순?보험계약부채$", 2: r"^손실부담계약을제외한집합$", 3: r"^이자비용$", 4: r"^보험계약마진금액을조정하는변동$", 5: r"^보험계약마진상각$", 6: r"^(분기|반기|3분기|\d분기)말순보험계약부채$"}
def read(tab):
    """CSM column = index of '보험계약마진' in header; returns {item: value(백만원)} using first occurrence"""
    hdr = tab["rows"][0]
    names = [c.replace(" ", "") for c in hdr]
    if not any("보험계약마진" in n for n in names): return None
    k = [i for i, n in enumerate(names) if "보험계약마진" in n][0]  # position among header cells incl. '구분' at 0
    d = {}
    for r in tab["rows"][1:]:
        lab, vals = row_vals(r)
        l = lab.replace(" ", "")
        for it, pat in LAB.items():
            if it not in d and re.match(pat, l) and len(vals) >= k:
                d[it] = vals[k - 1]
    return d if len(d) == 6 else None
for fyq, q, cq in (("FY2024_Q1", "2023.1Q", "2024.1Q"), ("FY2024_Q2", "2023.2Q", "2024.2Q"), ("FY2024_Q3", "2023.3Q", "2024.3Q")):
    p = find_xml(code, fyq)[0]
    tabs = load_tables(p)
    found = [(t["idx"], read(t)) for t in tabs if t["rows"] and read(t)]
    out.write(f"{fyq}: candidate CSM tables {[i for i, _ in found]}\n")
    # current = those whose values reproduce master cur; prior = same layout, not matching
    for idx, d in found:
        vals = {it: d[it] / 100.0 for it in d}
        calib = sum(1 for it in range(1, 7) if abs(float(cm[(code, cq, it)]["값"]) - vals[it]) <= 0.06) if all((code, cq, it) in cm for it in range(1, 7)) else None
        pr = sum(1 for it in range(1, 7) if abs(float(cm[(code, q, it)]["값"]) - vals[it]) <= 0.06)
        out.write(f"   table {idx}: vs master {cq} (cur) {calib}/6 ; vs master {q} post-apply (prior) {pr}/6 ; vals {[round(vals[i],1) for i in range(1,7)]}\n")
        if pr >= 5 or True:
            for it in range(1, 7):
                ap = applied.get((q, it))
                mm = float(cm[(code, q, it)]["값"])
                res.writerow([code, q, it, ap["new"] if ap else "", round(vals[it], 2), mm, "Y" if ap else "N", f"{calib}/6", "MATCH" if abs(mm - vals[it]) <= 0.06 else "DIFF"])
