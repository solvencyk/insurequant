# -*- coding: utf-8 -*-
"""v01: cell-level diff of PL_breakdown / CSM_waterfall (+provenance) vs git HEAD. Read-only."""
import json, sys, collections
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
HEAD = ROOT + "data/_derived/remaining_20261022/e21_ready25/verify/head/"
NINE = {"KR0104": "농협생명", "KR0083": "푸본현대", "KR0070": "ABL", "KR0079": "미래에셋", "KR0010": "KB손보",
        "KR0099": "KB라이프", "KR0003": "롯데손보", "KR0001": "메리츠", "KR0068": "한화생명"}
QS = {"2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def keyrows(rows):
    d = {}
    dup = 0
    for i, r in enumerate(rows):
        k = (r["원보험사코드"], r["공시분기"], r["항목번호"])
        if k in d:
            dup += 1
        d[k] = r
    return d, dup


out = []


def P(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


for name in ("PL_breakdown", "CSM_waterfall"):
    old = load(HEAD + name + ".json")
    new = load(ROOT + name + ".json")
    od, d1 = keyrows(old)
    nd, d2 = keyrows(new)
    P(f"== {name}: rows old={len(old)} new={len(new)} dupkeys old={d1} new={d2}")
    P("  added keys", len(set(nd) - set(od)), "removed keys", len(set(od) - set(nd)))
    # order check
    ok_order = [(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in old] == [(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in new]
    P("  same row order:", ok_order)
    fieldchg = collections.Counter()
    percq = collections.defaultdict(lambda: collections.Counter())
    outside = []
    itemset = collections.defaultdict(set)
    details = []
    for k in od:
        if k not in nd:
            continue
        a, b = od[k], nd[k]
        keys = set(a) | set(b)
        for f in keys:
            if a.get(f) != b.get(f):
                if f in ("값", "값_당분기"):
                    # tolerate float repr equality
                    av, bv = a.get(f), b.get(f)
                    if av is not None and bv is not None and abs(av - bv) < 1e-9:
                        continue
                fieldchg[f] += 1
                percq[(k[0], k[1])][f] += 1
                itemset[(k[0], k[1])].add(k[2])
                details.append((k, f, a.get(f), b.get(f)))
                if k[0] not in NINE or k[1] not in QS:
                    outside.append((k, f))
    P("  fields changed:", dict(fieldchg))
    P("  changes outside 9 companies/2023.1Q-2024.4Q:", len(outside), outside[:10])
    per_co = collections.Counter()
    for (c, q), cn in sorted(percq.items()):
        P(f"   {c} {NINE.get(c,'?')} {q}: 값={cn.get('값',0)} 값_당분기={cn.get('값_당분기',0)} items={sorted(itemset[(c,q)])}")
        per_co[c] += cn.get("값", 0)
    P("  값 changes per company:", {c + NINE.get(c, ""): n for c, n in per_co.items()}, "total 값", sum(per_co.values()))
    json.dump([[list(k), f, a, b] for k, f, a, b in details], open(HEAD + f"../v01_{name}_cells.json", "w", encoding="utf-8"), ensure_ascii=False)
    # added rows detail
    for k in sorted(set(nd) - set(od)):
        P("  ADDED", k, nd[k])
    for k in sorted(set(od) - set(nd)):
        P("  REMOVED", k, od[k])

# provenance
for name, rootkey in (("PL_breakdown_provenance", None), ("CSM_waterfall_provenance", None)):
    old = load(HEAD + name + ".json")
    new = load(ROOT + name + ".json")
    P(f"== {name}")
    # top-level keys
    for k in sorted(set(old) | set(new)):
        if k == "cells":
            continue
        if old.get(k) != new.get(k):
            P("  top-level key changed:", k, "(old len %s new len %s)" % (len(str(old.get(k))), len(str(new.get(k)))))
    oc, nc = old["cells"], new["cells"]
    P("  cells old", len(oc), "new", len(nc))
    def ck(c):
        return (c["company_code"], c["quarter"], c["item_block"])
    od = {ck(c): c for c in oc}
    nd = {ck(c): c for c in nc}
    P("  added", len(set(nd) - set(od)), "removed", len(set(od) - set(nd)), "order same:", [ck(c) for c in oc] == [ck(c) for c in nc])
    chg = []
    for k in od:
        if k in nd and od[k] != nd[k]:
            chg.append(k)
    P("  changed blocks:", len(chg))
    outside = [k for k in chg if k[0] not in NINE or k[1] not in QS]
    P("  outside scope:", outside)
    bycq = collections.defaultdict(list)
    for k in chg:
        bycq[(k[0], k[1])].append(k[2])
    for (c, q), bl in sorted(bycq.items()):
        P(f"   {c} {NINE.get(c)} {q}: {bl}")
    # what fields changed
    fch = collections.Counter()
    for k in chg:
        a, b = od[k], nd[k]
        for f in set(a) | set(b):
            if a.get(f) != b.get(f):
                fch[f] += 1
    P("  fields changed within blocks:", dict(fch))
    json.dump([[list(k), od[k], nd[k]] for k in chg], open(HEAD + f"../v01_{name}_blocks.json", "w", encoding="utf-8"), ensure_ascii=False)

open(HEAD + "../v01_diff.txt", "w", encoding="utf-8").write("\n".join(out))
