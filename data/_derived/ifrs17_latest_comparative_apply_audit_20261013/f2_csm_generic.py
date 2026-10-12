"""CSM waterfall cells (KR0001/KR0069/KR0082/KR0087/KR0104): own table reads + current-period calibration + closing identity."""
import sys, os, re, json, csv, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_dart import *
here = os.path.dirname(os.path.abspath(__file__))
cm = {}
for r in json.load(open(REPO + "/CSM_waterfall.json", encoding="utf-8")):
    cm[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
allapplied = {(r["code"], r["quarter"], int(r["item"])): r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["master"] == "CSM_waterfall"}
out = open(here + "/f2_csm_generic.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/f2_csm_generic.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "quarter", "item", "applied_new", "mine(억)", "post-apply master", "in_plan", "calibration(cur 6)", "verdict", "note"])
def vals_of(row):
    lab, vals = row_vals(row)
    return lab.replace(" ", ""), vals
def read_table(tab, cfg):
    """returns {item: value 백만원} or None. cfg: lab: {item: [regex,...]}, cols: indices (0-based among numerics), occ: {item: n}"""
    d = {}; seen = {}
    for r in tab["rows"]:
        lab, vals = vals_of(r)
        if not vals: continue
        for it, pats in cfg["lab"].items():
            for pat in pats:
                if re.search(pat, lab):
                    seen[(it, pat)] = seen.get((it, pat), 0) + 1
                    need = cfg.get("occ", {}).get(it, 1)
                    if seen[(it, pat)] == need and len(vals) > max(cfg["cols"]):
                        d[(it, pat)] = sum(vals[c] for c in cfg["cols"])
    out_d = {}
    for it, pats in cfg["lab"].items():
        s = [d[(it, p)] for p in pats if (it, p) in d]
        if len(s) == len(pats): out_d[it] = sum(s)
        else: return None
    return out_d
def is_cand(tab, key):
    return tab["rows"] and any(key in " ".join(r) for r in tab["rows"][:3])
CFG = {
 "KR0001": dict(fyq="FY2024_Q3", rc="20241114001986", quarters=[("2023.3Q", "2024.3Q")], key="보험계약마진", win=1,
    cfg=dict(cols=[2, 3, 4], lab={1: [r"^기초순장부금액$"], 2: [r"^신계약효과$"], 3: [r"^순보험금융손익$"], 4: [r"^보험계약마진을조정하는추정치변동$"], 5: [r"^당기서비스관련변동$"], 6: [r"^분기말순장부금액$"]})),
 "KR0069": dict(fyq="FY2024_Q2", rc="20240814004014", quarters=[("2023.2Q", "2024.2Q")], key="보험계약마진", win=3,
    cfg=dict(cols=[2, 3, 4], lab={1: [r"^보험계약순부채\(자산\)\(기초\)$"], 2: [r"^당기최초인식계약$"], 3: [r"^보험계약의순금융손익$", r"^환율변동효과등$"], 4: [r"^보험계약마진추정의변경$"], 5: [r"^제공한서비스에대해인식한보험계약마진$"], 6: [r"^보험계약순부채\(자산\)\(기말\)$"]})),
 "KR0082": dict(fyq="FY2024_Q1", rc="20240514000901", quarters=[("2023.1Q", "2024.1Q")], key="보험계약마진", win=1,
    cfg=dict(cols=[2, 3, 4], lab={1: [r"^(전기초|당기초|기초)보험계약부채$"], 2: [r"^최초인식계약$"], 3: [r"^당기손익인식보험금융비용$"], 4: [r"^보험계약마진에반영된추정치변동$"], 5: [r"^보험계약마진상각$"], 6: [r"^(전분기말|당분기말|분기말|반기말)보험계약부채$"]})),
 "KR0087": dict(fyq="FY2024_Q1", rc="20240516001580", quarters=[("2023.1Q", "2024.1Q")], key="보험계약마진", win=1,
    cfg=dict(cols=[5], lab={1: [r"발행한보험계약부채포트폴리오"], 2: [r"해당기간에처음인식한계약의효과"], 3: [r"^보험금융비용\(수익\)당기손익$"], 4: [r"보험계약마진을조정하는추정치의변동"], 5: [r"서비스이전을반영하기위해당기손익으로인식한보험계약마진금액"], 6: [r"발행한보험계약부채포트폴리오"]}, occ={6: 2})),
 "KR0104": dict(fyq="FY2024_Q1", rc="20240514001371", quarters=[("2023.1Q", "2024.1Q")], key="보험계약마진", win=1,
    cfg=dict(cols=[5], lab={1: [r"기초보험계약부채$"], 2: [r"최초인식계약"], 3: [r"보험금융손익당기손익인식"], 4: [r"보험계약마진을조정하는변동"], 5: [r"보험계약마진상각"], 6: [r"기말보험계약부채$"]})),
}
for code, C in CFG.items():
    p = find_xml(code, C["fyq"], C["rc"])[0]
    tabs = load_tables(p)
    cands = []
    for t in tabs:
        if not is_cand(t, C["key"]): continue
        d = read_table(t, C["cfg"])
        if d: cands.append((t["idx"], d))
    out.write(f"== {code} {C['fyq']}: candidate tables {[i for i, _ in cands]}\n")
    for q, cq in C["quarters"]:
        mc = {it: float(cm[(code, cq, it)]["값"]) for it in range(1, 7) if (code, cq, it) in cm}
        mp = {it: float(cm[(code, q, it)]["값"]) for it in range(1, 7)}
        # windows
        w = C["win"]
        found = {}
        for a in range(len(cands) - w + 1):
            ws = cands[a:a + w]
            # require consecutive table indices (step 2 typical)
            tot = {it: sum(x[1][it] for x in ws) / 100.0 for it in range(1, 7)}
            sc_cur = sum(1 for it in mc if abs(mc[it] - tot[it]) <= 0.15)
            sc_pri = sum(1 for it in mp if abs(mp[it] - tot[it]) <= 0.15)
            out.write(f"   window {[x[0] for x in ws]}: vs master {cq} (cur) {sc_cur}/{len(mc)} ; vs master {q} post-apply (prior) {sc_pri}/6 ; vals {[round(tot[i],1) for i in range(1,7)]}\n")
            if sc_pri >= 4: found[tuple(x[0] for x in ws)] = (tot, sc_cur)
        # best calibration: any window with >=5 cur matches exists?
        cur_ok = any(True for _ in [0])
        for key, (tot, sc_cur) in found.items():
            # closing identity with mine
            resid = tot[1] + tot[2] + tot[3] + tot[4] + tot[5] - tot[6]
            for it in range(1, 7):
                ap = allapplied.get((code, q, it))
                note = ""
                v = tot[it]
                tol = 0.15 if it == 4 else 0.06
                ok = abs(mp[it] - v) <= tol
                if it == 4 and code in ("KR0087", "KR0104"):
                    # residual convention
                    r4 = tot[6] - tot[1] - tot[2] - tot[3] - tot[5]
                    note = f"printed adj row {v:.2f}; residual {r4:.2f}"
                    ok = abs(mp[it] - r4) <= 0.15 or ok
                res.writerow([code, q, it, ap["new"] if ap else "", round(v, 2), mp[it], "Y" if ap else "N", f"{sc_cur}/{len(mc)}", "MATCH" if ok else "DIFF", note + f" closure resid {resid:.2f}"])
                out.write(f"      item{it}: mine={v:.2f} master={mp[it]} {'APPLIED new='+ap['new'] if ap else ''} {'OK' if ok else 'DIFF'} {note}\n")
            out.write(f"      closing identity residual (mine) {resid:.2f}억\n")
