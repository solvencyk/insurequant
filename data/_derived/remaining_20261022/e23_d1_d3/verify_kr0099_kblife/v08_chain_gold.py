# -*- coding: utf-8 -*-
"""Single-quarter recompute, identity census, CSM chain, gold classification for KR0099 (read-only)."""
import sys, json, subprocess, csv
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = R + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife/"
out = []


def P(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


def head(rel):
    return json.loads(subprocess.run(["git", "-C", R, "show", "HEAD:" + rel], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))


def live(rel):
    return json.load(open(R + "/" + rel, encoding="utf-8"))


def cm(rows):
    return {(r["항목번호"], r["공시분기"]): (r["값"], r["값_당분기"]) for r in rows if r["원보험사코드"] == "KR0099"}


PLH, PLL = cm(head("PL_breakdown.json")), cm(live("PL_breakdown.json"))
CSH, CSL = cm(head("CSM_waterfall.json")), cm(live("CSM_waterfall.json"))
Q = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]
prev = {q: (Q[i - 1] if i and Q[i - 1][:4] == q[:4] else None) for i, q in enumerate(Q)}

P("=== (5a) PL single-quarter recompute: value_dangi == cum - previous cum of same FY (Q1 = cum), all 32 items, 8 quarters, LIVE")
bad = 0; n = 0; changed_dq = []
for q in Q:
    for it in range(1, 33):
        if (it, q) not in PLL:
            continue
        cum, dq = PLL[(it, q)]
        pc = PLL.get((it, prev[q]), (None, None))[0] if prev[q] else 0.0
        if cum is None or pc is None:
            exp = None
        else:
            exp = cum - pc
        n += 1
        ok = (exp is None and dq is None) or (exp is not None and dq is not None and abs(exp - dq) < 5e-4)
        if not ok:
            bad += 1
            P(f"   MISMATCH {q} item{it} cum={cum} prev={pc} dangi={dq} expected={exp}  head={PLH.get((it, q))}")
        if PLH.get((it, q), (None, None))[1] != dq:
            changed_dq.append((q, it))
P(f"   cells checked {n}, mismatches {bad}")
from collections import Counter
P("   dangi cells changed vs HEAD:", len(changed_dq), dict(Counter(q for q, _ in changed_dq)))
# every changed dangi cell is a cell whose cum changed or whose prev-quarter cum changed
chg_val = {(it, q) for (it, q) in PLL if PLH.get((it, q), (None,))[0] != PLL[(it, q)][0]}
unexpl = [(q, it) for q, it in changed_dq if (it, q) not in chg_val and not (prev[q] and (it, prev[q]) in chg_val)]
P("   changed dangi cells not explained by a changed cum (own or previous quarter):", unexpl)
# conversely: dangi cells that SHOULD change (cum or prev cum changed) but did not
P("   cum-changed 값 cells:", len(chg_val), "by q", dict(Counter(q for it, q in chg_val)))
P("   changed outside 2023.1Q-4Q:", [(q, it) for q, it in changed_dq if q not in Q[:4]])

P("\n=== (5b) CSM single-quarter recompute and chain")
bad = 0
for q in Q:
    for it in range(1, 7):
        cum, dq = CSL[(it, q)]
        if it in (1, 6):
            # stock items: dangi opening == prior closing (within FY), closing dangi == closing cum
            exp = (CSL[(6, prev[q])][0] if prev[q] else cum) if it == 1 else cum
        else:
            exp = cum - (CSL[(it, prev[q])][0] if prev[q] else 0.0)
        if abs(exp - dq) > 0.0501:
            bad += 1; P(f"   CSM MISMATCH {q} item{it} cum={cum} dangi={dq} expected={exp:.2f}")
P("   CSM single-quarter mismatches (tol 0.05 eok for 1dp rounding):", bad)
P("   CSM cum identity open+new+int+adj+amort = close (eok), LIVE vs HEAD")
for q in Q:
    for lab, S in (("LIVE", CSL), ("HEAD", CSH)):
        o, nb, it_, adj, am, cl = [S[(i, q)][0] for i in range(1, 7)]
        r = o + nb + it_ + adj + am - cl
        P(f"   {q} {lab}: {o} + {nb} + {it_} + {adj} + {am} = {o+nb+it_+adj+am:.1f} vs close {cl}  resid {r:+.2f}")
P("   Opening drift within FY2023 (cum opening of each quarter):", {q: CSL[(1, q)][0] for q in Q[:4]}, "HEAD:", {q: CSH[(1, q)][0] for q in Q[:4]})
P("   Opening drift within FY2024:", {q: CSL[(1, q)][0] for q in Q[4:]})
P("   FY2023 -> FY2024 boundary: 2023.4Q close", CSL[(6, "2023.4Q")][0], "vs 2024.1Q open", CSL[(1, "2024.1Q")][0], "diff", round(CSL[(6, "2023.4Q")][0] - CSL[(1, "2024.1Q")][0], 2), "| HEAD", CSH[(6, "2023.4Q")][0], CSH[(1, "2024.1Q")][0])
P("   quarter-to-quarter closing -> next single-quarter opening (dangi) is checked above; 2024 Q-to-Q: ", [(Q[i], CSL[(6, Q[i])][0], Q[i + 1], CSL[(1, Q[i + 1])][1]) for i in range(4, 7)])

P("\n=== (5c) PL block identities per quarter (LIVE vs HEAD), residual in 백만원 (None = leg missing)")
ids = [
    ("1 = 2 + 15 - 16", lambda g: g(1) - (g(2) + g(15) - g(16))),
    ("2 = 3 + 8", lambda g: g(2) - (g(3) + g(8))),
    ("3 = 4+5+6+7", lambda g: g(3) - (g(4) + g(5) + g(6) + g(7))),
    ("8 = 9+10+11+12", lambda g: g(8) - (g(9) + g(10) + g(11) + g(12))),
    ("17 = 18 + 19", lambda g: g(17) - (g(18) + g(19))),
    ("20 = 1 + 17", lambda g: g(20) - (g(1) + g(17))),
    ("22 = 20 + 21", lambda g: g(22) - (g(20) + g(21))),
    ("24 = 22 - 23", lambda g: g(24) - (g(22) - g(23))),
    ("25 = 26+27+28+29+30+32", lambda g: g(25) - (g(26) + g(27) + g(28) + g(29) + g(30) + g(32))),
    ("31 = 24 + 25", lambda g: g(31) - (g(24) + g(25))),
]
for q in Q[:5]:
    for lab, S in (("LIVE", PLL), ("HEAD", PLH)):
        res = []
        for name, f in ids:
            try:
                g = lambda i: (S[(i, q)][0] if S[(i, q)][0] is not None else (_ for _ in ()).throw(KeyError(i)))
                v = f(g)
                res.append(f"{name}:{v:+.0f}")
            except KeyError:
                res.append(f"{name}:None")
        P(f"   {q} {lab}: " + " | ".join(res))
P("\n   PL vs CSM cross: PL item4 (CSM amort, 백만원) vs CSM item5 (억원)")
for q in Q:
    p4 = PLL[(4, q)][0]; c5 = CSL[(5, q)][0]
    P(f"   {q}: PL4={p4} CSM5={c5} PL4/100+CSM5={p4/100 + c5:+.2f} eok")

P("\n=== (3) Owner gold: KR0099")
GH = head("data/_gold/user_pl_cells.json"); GL = live("data/_gold/user_pl_cells.json")
CH_ = head("data/_gold/user_csm_cells.json"); CL = live("data/_gold/user_csm_cells.json")
kf = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])
pl_head = {kf(e): e for e in GH["set"] if e["원보험사코드"] == "KR0099"}
pl_live = {kf(e): e for e in GL["set"] if e["원보험사코드"] == "KR0099"}
cs_head = {kf(e): e for e in CH_["set"] if e["원보험사코드"] == "KR0099"}
cs_live = {kf(e): e for e in CL["set"] if e["원보험사코드"] == "KR0099"}
P("PL gold KR0099: HEAD", len(pl_head), "LIVE", len(pl_live), "added", len(set(pl_live) - set(pl_head)), "removed", len(set(pl_head) - set(pl_live)), "changed", sum(1 for k in pl_head if k in pl_live and pl_head[k] != pl_live[k]))
P("CSM gold KR0099: HEAD", len(cs_head), "LIVE", len(cs_live), "added", len(set(cs_live) - set(cs_head)), "removed", len(set(cs_head) - set(cs_live)), "changed", sum(1 for k in cs_head if k in cs_live and cs_head[k] != cs_live[k]))
P("CSM gold KR0099 HEAD entries (kept, unchanged):", [(k, cs_head[k]["값"], cs_head[k].get("was")) for k in cs_head])
# value vs master, was vs HEAD master
badg = 0
for k, e in pl_live.items():
    m = PLL[(k[1], k[2])][0]; h = PLH.get((k[1], k[2]), (None, None))[0]
    if abs(e["값"] - m) > 5e-4 or (e.get("was") is None) != (h is None) or (h is not None and e.get("was") is not None and abs(e["was"] - h) > 5e-4):
        badg += 1; P("   PL gold mismatch", k, e["값"], m, e.get("was"), h)
for k, e in cs_live.items():
    if k in cs_head:
        continue
    m = CSL[(k[1], k[2])][0]; h = CSH.get((k[1], k[2]), (None, None))[0]
    if abs(e["값"] - m) > 5e-4 or (e.get("was") is None) != (h is None) or (h is not None and e.get("was") is not None and abs(e["was"] - h) > 5e-4):
        badg += 1; P("   CSM gold mismatch", k, e["값"], m, e.get("was"), h)
P("new gold entries vs master value / was vs HEAD master mismatches:", badg)
P("all new PL gold entries (key, old master -> new): was==None (blank filled):", sum(1 for e in pl_live.values() if e.get("was") is None), "| value changed:", sum(1 for e in pl_live.values() if e.get("was") is not None))
P("   classification of replaced OWNER gold entries: HEAD had 0 PL gold and 2 CSM gold (2024.4Q) entries for KR0099; none was replaced/removed => class (original-vintage / wrong-basis / chain-forced) replaced count = 0")
# approved list
rows = list(csv.DictReader(open(R + "/data/_derived/remaining_20261022/e20_held_and_remaining/measure/gold_cells_replaced.csv", encoding="utf-8-sig")))
sc = Counter((r["scenario"], r["code"]) for r in rows)
P("gold_cells_replaced.csv scenarios involving KR0099:", {k: v for k, v in sc.items() if k[1] == "KR0099"})
P("   rows with KR0099 and scenario N2*/B:", [r for r in rows if r["code"] == "KR0099" and "_B" in r["scenario"]])
# other-company gold diffs: confirm nothing else of KR0099 touched, list other companies touched in same file (not scope)
for nm, H, L in (("PL", GH, GL), ("CSM", CH_, CL)):
    hd = {kf(e): e for e in H["set"]}; ld = {kf(e): e for e in L["set"]}
    P(nm, "gold other-company changes (not my scope):", dict(Counter(k[0] for k in ld if k not in hd and k[0] != "KR0099")), "removed", [k for k in hd if k not in ld], "changed", [k for k in hd if k in ld and hd[k] != ld[k]])
for sect in ("null_dangi", "set_dangi"):
    for nm, H, L in (("PL", GH, GL),):
        hh = json.dumps(H[sect], ensure_ascii=False); ll = json.dumps(L[sect], ensure_ascii=False)
        P(nm, sect, "contains KR0099 in HEAD:", "KR0099" in hh, "in LIVE:", "KR0099" in ll)
open(OUT + "v08_chain_gold.txt", "w", encoding="utf-8").write("\n".join(out))
