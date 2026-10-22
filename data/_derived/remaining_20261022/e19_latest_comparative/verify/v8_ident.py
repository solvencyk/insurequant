import json, random, collections
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
head = json.load(open(SP + "/head_PL.json", encoding="utf-8"))
cur = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
gold = json.load(open(ROOT + "/data/_gold/user_pl_cells.json", encoding="utf-8"))
H = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in head}
C = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cur}
B = {"KR0082": ["2023.3Q"], "KR0032": ["2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"], "KR0104": ["2023.3Q"],
     "KR0087": ["2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"], "KR0070": ["2024.1Q", "2024.2Q", "2024.3Q"],
     "KR0083": ["2024.1Q", "2024.2Q"], "KR0005": ["2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]}
out = []
def g(M, c, i, q):
    r = M.get((c, i, q))
    return None if r is None or r["값"] is None else r["값"]
def z(x): return 0.0 if x is None else x
ID = {
 "20=1+17": lambda M, c, q: g(M,c,20,q) - (g(M,c,1,q) + g(M,c,17,q)),
 "17=18+19": lambda M, c, q: g(M,c,17,q) - (g(M,c,18,q) + g(M,c,19,q)),
 "22=20+21": lambda M, c, q: g(M,c,22,q) - (g(M,c,20,q) + g(M,c,21,q)),
 "|22-24|-|23|": lambda M, c, q: abs(g(M,c,22,q) - g(M,c,24,q)) - abs(g(M,c,23,q)),
 "31=24+25": lambda M, c, q: g(M,c,31,q) - (g(M,c,24,q) + g(M,c,25,q)),
 "LOB 1=2+13+14+15-16": lambda M, c, q: g(M,c,1,q) - (z(g(M,c,2,q)) + z(g(M,c,13,q)) + z(g(M,c,14,q)) + z(g(M,c,15,q)) - z(g(M,c,16,q))),
 "25=26..30+32": lambda M, c, q: g(M,c,25,q) - sum(z(g(M,c,i,q)) for i in (26,27,28,29,30,32)),
}
worst = collections.defaultdict(lambda: [0, None])
worstH = collections.defaultdict(lambda: [0, None])
rows = []
for c, qs in B.items():
    for q in qs:
        line = []
        for name, f in ID.items():
            try:
                r = f(C, c, q); rh = f(H, c, q)
            except Exception as e:
                r = rh = None
            line.append((name, rh, r))
            if r is not None and abs(r) > worst[name][0]:
                worst[name] = [abs(r), (c, q)]
            if rh is not None and abs(rh) > worstH[name][0]:
                worstH[name] = [abs(rh), (c, q)]
        out.append("%s %s: " % (c, q) + "; ".join("%s head=%s cur=%s" % (n, None if a is None else round(a, 4), None if b is None else round(b, 4)) for n, a, b in line))
out.append("WORST residual after (million won): " + json.dumps({k: [round(v[0], 4), v[1]] for k, v in worst.items()}))
out.append("WORST residual head: " + json.dumps({k: [round(v[0], 4), v[1]] for k, v in worstH.items()}))
# NI/OCI/TCI deltas
out.append("DELTAS (million won): bucket dNI(24) dOCI(25) dTCI(31) | dNI+dOCI | d17 d19 d1")
for c, qs in B.items():
    for q in qs:
        d = lambda i: g(C,c,i,q) - g(H,c,i,q)
        dni, doc, dtc = d(24), d(25), d(31)
        out.append("  %s %s dNI=%.3f dOCI=%.3f dTCI=%.3f sum(NI+OCI)=%.3f | d17=%.3f d19=%.3f d1=%.3f d16=%.3f" % (c, q, dni, doc, dtc, dni + doc, d(17), d(19), d(1), d(16)))
# dangi recompute
nd = {tuple(x[:3]) for x in gold["null_dangi"]["cells"]}
sd = {(x[0], x[1], x[2]): x[3] for x in gold["set_dangi"]["cells"]}
def prevq(q):
    y, r = q.split("."); r = int(r[0])
    return None if r == 1 else "%s.%dQ" % (y, r - 1)
def expect(M, nulls, sets, c, it, q):
    k = (c, q, it)
    if k in nulls: return ("null", None)
    if k in sets: return ("set", sets[k])
    v = g(M, c, it, q)
    pq = prevq(q)
    if pq is None: return ("derive", v)
    pv = g(M, c, it, pq)
    if v is None or pv is None: return ("derive", None)
    return ("derive", v - pv)
cos = list(B)
mm = []; tot = 0
cells = []
for (c, it, q), r in C.items():
    if c not in cos or q > "2025.4Q": continue
    cells.append((c, it, q))
random.seed(20261022)
changed_d = [k for k in C if C[k].get("값_당분기") != H[k].get("값_당분기")]
sample = random.sample(changed_d, max(1, len(changed_d) // 4))
nullsH = {tuple(x[:3]) for x in json.load(open(SP + "/head_gold.json", encoding="utf-8"))["null_dangi"]["cells"]}
def check(keys, label):
    bad = []
    for (c, it, q) in keys:
        kind, e = expect(C, nd, sd, c, it, q)
        a = C[(c, it, q)].get("값_당분기")
        if (e is None) != (a is None) or (e is not None and abs(e - a) > 1e-6):
            bad.append((c, it, q, kind, e, a))
    out.append("%s: checked %d, mismatches %d" % (label, len(keys), len(bad)))
    for b in bad[:15]:
        out.append("     MISMATCH %s" % (b,))
    return bad
check(changed_d, "ALL changed 값_당분기 cells (recomputed from final masters + null/set_dangi)")
check(sample, "random 25%% sample of changed 값_당분기 (seed 20261022, n=%d)" % len(sample))
bad_all = check(cells, "ALL cells of the 7 companies 2023.1Q-2025.4Q")
# same on HEAD for baseline
bh = []
for (c, it, q) in cells:
    kind, e = expect(H, nullsH, {(x[0], x[1], x[2]): x[3] for x in json.load(open(SP + "/head_gold.json", encoding="utf-8"))["set_dangi"]["cells"]}, c, it, q)
    a = H[(c, it, q)].get("값_당분기")
    if (e is None) != (a is None) or (e is not None and abs(e - a) > 1e-6):
        bh.append((c, it, q))
out.append("baseline HEAD: mismatches over same cells %d" % len(bh))
open(V + "v8_ident.txt", "w", encoding="utf-8").write("\n".join(out))
