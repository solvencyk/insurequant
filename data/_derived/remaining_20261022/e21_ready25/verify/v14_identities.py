# -*- coding: utf-8 -*-
"""v14: independent identity closure on the master for all buckets of the 9 companies (HEAD vs working tree)."""
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
HERE = R + "data/_derived/remaining_20261022/e21_ready25/verify/"
NINE = ["KR0104","KR0083","KR0070","KR0079","KR0010","KR0099","KR0003","KR0001","KR0068"]
QS = ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"]

def load(p):
    d = collections.defaultdict(dict)
    for r in json.load(open(p, encoding="utf-8")):
        d[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]
    return d
new = load(R + "PL_breakdown.json"); old = load(HERE + "head/PL_breakdown.json")

def S(m, *its):
    vs = [m.get(i) for i in its]
    return None if any(v is None for v in vs) else sum(vs)

def checks(m):
    res = {}
    g = m.get
    def eq(name, lhs, rhs, tol):
        if lhs is None or rhs is None: res[name] = ("SKIP", None); return
        d = rhs - lhs
        res[name] = ("OK" if abs(d) <= tol else "FAIL", round(d, 3))
    eq("2=3+8", g(2), S(m,3,8), 1.001)
    eq("3=4+5+6+7", g(3), S(m,4,5,6,7), 0.01)
    eq("8=9+10+11+12", g(8), S(m,9,10,11,12), 0.01)
    # item1 dual form: bare / adj
    lob = [g(2), g(13), g(14)]
    if g(1) is not None and all(v is not None for v in lob):
        bare = sum(lob); cands = [bare]
        if g(15) is not None and g(16) is not None: cands.append(bare + g(15) - g(16))
        d = min((c - g(1) for c in cands), key=abs)
        tol = max(0.001 * abs(g(1)), 200 * 1e-6 * 1e6 / 1e6 * 0.2)  # >=0.2 mn floor
        tol = max(0.001 * abs(g(1)), 0.2)
        res["1=2+13+14(+15-16)"] = ("OK" if abs(d) <= tol else "FAIL", round(d, 3))
    else:
        res["1=2+13+14(+15-16)"] = ("SKIP", None)
    eq("17=18+19", g(17), S(m,18,19), 0.01)
    eq("20=1+17", g(20), S(m,1,17), max(1.001, 0.001*abs(g(20) or 0)))
    eq("22=20+21", g(22), S(m,20,21), 0.01)
    eq("24=22-23", g(24), None if g(22) is None or g(23) is None else g(22)-g(23), 0.01)
    eq("31=24+25", g(31), S(m,24,25), max(1.001, 0.0))
    eq("25=26+27+28+29+30+32", g(25), S(m,26,27,28,29,30,32), 1.001)
    return res

out = []
tot = collections.Counter()
for tag, M in (("HEAD", old), ("NEW", new)):
    fails = []
    for c in NINE:
        for q in QS:
            m = M.get((c, q))
            if not m: continue
            r = checks(m)
            for k, (st, d) in r.items():
                tot[(tag, st)] += 1
                if st == "FAIL": fails.append((c, q, k, d))
    print(tag, "FAIL list:", len(fails))
    for f in fails: print("   ", f)
print(dict(tot))
# differences between head and new fails
