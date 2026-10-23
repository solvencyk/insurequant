# -*- coding: utf-8 -*-
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
S1 = ROOT + "/data/_derived/remaining_20261022/e25_followups/sweep_neighbors/"
plr = json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in plr}
csmr = json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))
csm = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in csmr}
t = json.load(open(S1 + "s01_touched.json", encoding="utf-8"))
cq = sorted({tuple(k.split("|")) for v in t.values() for k in v})
cqset = set(cq)
s1 = json.load(open(S1 + "p1_stmt.json", encoding="utf-8"))
g = json.load(open(S1 + "p2_generic.json", encoding="utf-8"))
p3 = json.load(open(S1 + "p3_existing.json", encoding="utf-8"))
p5 = json.load(open(S1 + "p5_hd.json", encoding="utf-8"))
def lq(q): return f"{int(q[:4]) + 1}.{q[5:]}"
compared = set()
ART = {("KR0009", i) for i in ("16", "23", "18", "19")}
for k, v in sorted(s1.items()):
    c, q = k.split("|")
    if not v["prior"]: continue
    for i, d in v["prior"].items():
        if not isinstance(d, dict) or (c, i) in ART: continue
        m = pl.get((c, i, q))
        if m is None:
            if abs(d["val"]) >= 0.5 and not d.get("absent"): compared.add((c, q, i))
            continue
        compared.add((c, q, i))
for x in p3:
    if x["sheet"] == "PL" and "latest" in x: compared.add((x["code"], x["q"], x["item"]))
SKIP_GENERIC = {"KR0001", "KR0003", "KR0010", "KR0009", "KR0099"}
for k, rec in sorted(g.items()):
    c, q = k.split("|")
    if c in SKIP_GENERIC or "prior" not in rec: continue
    for it in ("4", "5", "9", "10"):
        pr = rec["prior"].get(it); cu = rec.get("cur", {}).get(it); ml = pl.get((c, it, lq(q)))
        if not pr: continue
        j = None
        if cu and ml is not None:
            for idx, x in enumerate(cu):
                if abs(abs(x["val"]) - abs(ml)) < 0.5: j = idx; break
        if j is not None and j < len(pr): pass
        elif len(pr) == 1: pass
        else: continue
        if (c, it) in {("KR0070", "5")}: continue
        compared.add((c, q, it))
seen = {}
for q, it, sect, m, v, d, ln, ts in p5:
    seen[(q, it)] = seen.get((q, it), 0) + 1
    ii = it if seen[(q, it)] == 1 else (9 if it == 4 else 10)
    compared.add(("KR0009", q, str(ii)))
for x in p3:
    if x["sheet"] == "CSM" and "raw" in x:
        for i in range(1, 7): compared.add((x["code"], x["q"], "CSM" + str(i)))
master_cells = {(c, q, i) for (c, i, q), v in pl.items() if (c, q) in cqset and v is not None and i.isdigit()}
csm_cells = {(c, q, "CSM" + i) for (c, i, q), v in csm.items() if (c, q) in cqset and v is not None and i.isdigit()}
allc = master_cells | csm_cells
comp = {x for x in compared if x in allc}
print("all", len(allc), "compared", len(comp), "uncovered", len(allc - comp))
unc = sorted(allc - comp)
json.dump(unc, open("uncovered.json", "w", encoding="utf-8"))
byc = collections.defaultdict(lambda: collections.defaultdict(list))
for c, q, i in unc: byc[c][q].append(i)
for c in sorted(byc):
    n = sum(len(v) for v in byc[c].values())
    print(c, n)
    for q in sorted(byc[c]): print("   ", q, sorted(byc[c][q], key=lambda x: (len(x), x)))
