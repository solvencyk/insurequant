import json, os, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(REPO + "/data/compare/panel_compare.json", encoding="utf-8"))
Q = P["meta"]["quarters"]
def load(f): return json.load(open(REPO + "/" + f, encoding="utf-8"))
pl = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in load("PL_breakdown.json")}
bs = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in load("IFRS17_BS.json")}
cs = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in load("CSM_waterfall.json")}
nb = {(r["원보험사코드"], r["공시분기"]): r for r in load("NB_CSM_multiple.json")}
kp = {}; kq = {}
for r in load("kics_disclosure.json"):
    kp[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r.get("값"); kq[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r.get("값_적용후")
def f(x):
    try: return None if x in (None, "") else float(x)
    except Exception: return None
def rnd(x, dec): return None if x is None else round(x, dec)
out = open(here + "/j6_compare_check.txt", "w", encoding="utf-8")
M = {m["id"]: m for m in P["metrics"]}
def check(mid, fn, key="v", dec=None):
    m = M[mid]; dec = m["dec"] if dec is None else dec
    bad = 0; n = 0
    for c, arr in m[key].items():
        for qi, got in enumerate(arr):
            q = Q[qi]
            exp = fn(c, q)
            exp = rnd(exp, dec) if exp is not None else None
            n += 1
            same = (got is None and exp is None) or (got is not None and exp is not None and abs(got - exp) <= 10 ** -dec * 0.51)
            if not same:
                bad += 1; out.write(f"  {mid}/{key} {c} {q}: panel {got} vs master {exp}\n")
    out.write(f"{mid}/{key}: {n} leaves checked, {bad} differ\n")
    return bad
tot = 0
tot += check("kics_basic", lambda c, q: f(kq.get((c, q, 28))) if f(kq.get((c, q, 28))) is not None else f(kp.get((c, q, 28))), "v")
tot += check("kics_basic", lambda c, q: f(kp.get((c, q, 28))), "v_pre")
tot += check("csm_closing", lambda c, q: f(cs.get((c, q, 6))))
tot += check("nb_multiple", lambda c, q: (nb.get((c, q)) or {}).get("신계약CSM배수_연누계"))
tot += check("ins_profit", lambda c, q: None if f(pl.get((c, q, 1))) is None else f(pl.get((c, q, 1))) / 100.0)
tot += check("net_income", lambda c, q: None if f(pl.get((c, q, 24))) is None else f(pl.get((c, q, 24))) / 100.0)
tot += check("kics_avail", lambda c, q: f(kq.get((c, q, 1))) if f(kq.get((c, q, 1))) is not None else f(kp.get((c, q, 1))), "v")
tot += check("kics_avail", lambda c, q: f(kp.get((c, q, 1))), "v_pre")
tot += check("nb_csm", lambda c, q: f(cs.get((c, q, 2))))
tot += check("inv_profit", lambda c, q: None if f(pl.get((c, q, 17))) is None else f(pl.get((c, q, 17))) / 100.0)
tot += check("equity", lambda c, q: None if f(bs.get((c, q, 3))) is None else f(bs.get((c, q, 3))) / 100.0)
tot += check("assets", lambda c, q: None if f(bs.get((c, q, 1))) is None else f(bs.get((c, q, 1))) / 100.0)
out.write(f"TOTAL differing leaves: {tot}\n")
# ROE
roe = M["roe"]; bad = 0; n = 0
fac = {"1Q": 4.0, "2Q": 2.0, "3Q": 4.0 / 3.0, "4Q": 1.0}
for c, arr in roe["v"].items():
    for qi, got in enumerate(arr):
        q = Q[qi]; y = int(q[:4]); k = q[5:]
        ni = f(pl.get((c, q, 24))); eq = f(bs.get((c, q, 3))); eq0 = f(bs.get((c, f"{y-1}.4Q", 3)))
        exp = None
        if ni is not None and eq is not None and eq0 is not None and (eq0 + eq) > 0 and y >= 2024:
            exp = round((ni * fac[k]) / ((eq0 + eq) / 2.0) * 100.0, 1)
        n += 1
        if (got is None) != (exp is None) or (got is not None and abs(got - exp) > 0.11):
            bad += 1; out.write(f"  roe {c} {q}: panel {got} vs mine {exp}\n")
out.write(f"roe/v: {n} leaves, {bad} differ (tolerance 0.1pt; clip/negative-equity rules not replicated)\n")
