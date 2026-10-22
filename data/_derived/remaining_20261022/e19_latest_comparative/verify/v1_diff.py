import json, sys, collections
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify"
out = []
def P(*a):
    out.append(" ".join(str(x) for x in a))

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

head = load(SP + "/head_PL.json")
cur = load(ROOT + "/PL_breakdown.json")
def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])
hk = {}
for r in head:
    k = key(r)
    assert k not in hk, k
    hk[k] = r
ck = {}
for r in cur:
    k = key(r)
    assert k not in ck, k
    ck[k] = r
P("rows head", len(head), "cur", len(cur))
P("added keys", len(set(ck) - set(hk)), "removed keys", len(set(hk) - set(ck)))
# order preserved?
P("same order", [key(r) for r in head] == [key(r) for r in cur])
changed = []
fieldchg = collections.Counter()
for k in hk:
    if k not in ck:
        continue
    a, b = hk[k], ck[k]
    fl = [f for f in set(a) | set(b) if a.get(f) != b.get(f)]
    if fl:
        changed.append((k, fl))
        for f in fl:
            fieldchg[f] += 1
P("changed rows", len(changed), "field counter", dict(fieldchg))
# by company & quarter
bq = collections.defaultdict(lambda: collections.Counter())
for k, fl in changed:
    for f in fl:
        bq[(k[0], k[2])][f] += 1
for (c, q), cn in sorted(bq.items()):
    P(c, q, dict(cn))
P("companies changed", sorted({k[0] for k, _ in changed}))
P("quarters changed", sorted({k[2] for k, _ in changed}))
P("items changed", sorted({k[1] for k, _ in changed}))
# item set > 32?
bad_items = sorted({k[1] for k, _ in changed if k[1] > 32})
P("changed items >32", bad_items)
# save changed list for later
with open(OUT + "/v1_changed.json", "w", encoding="utf-8") as f:
    json.dump([[list(k), fl] for k, fl in changed], f, ensure_ascii=False)

# provenance diff
hp = load(SP + "/head_PLprov.json")
cp = load(ROOT + "/PL_breakdown_provenance.json")
P("prov type", type(hp).__name__, type(cp).__name__)
def walk_diff(a, b, path, acc):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k not in a:
                acc.append((path + [k], "ADDED"))
            elif k not in b:
                acc.append((path + [k], "REMOVED"))
            else:
                walk_diff(a[k], b[k], path + [k], acc)
    elif isinstance(a, list) and isinstance(b, list):
        if a != b:
            acc.append((path, "LIST_CHANGED len %d->%d" % (len(a), len(b))))
    else:
        if a != b:
            acc.append((path, "CHANGED"))
acc = []
walk_diff(hp, cp, [], acc)
P("prov diff entries", len(acc))
pc = collections.Counter()
for path, what in acc:
    pc[(what.split()[0], tuple(path[:2]) if len(path) >= 2 else tuple(path))] += 1
for k, v in sorted(pc.items(), key=lambda x: str(x)):
    P(" ", k, v)
# prov: which top-level keys / companies
topk = collections.Counter(p[0] for p, _ in acc)
P("prov top-level keys touched", dict(topk))
with open(OUT + "/v1_prov_diff.json", "w", encoding="utf-8") as f:
    json.dump([[list(map(str, p)), w] for p, w in acc], f, ensure_ascii=False)

# gold diff
hg = load(SP + "/head_gold.json")
cg = load(ROOT + "/data/_gold/user_pl_cells.json")
P("gold top keys head", list(hg.keys()), "cur", list(cg.keys()))
for sec in hg:
    if sec == "_doc":
        P("_doc same", hg[sec] == cg.get(sec))
        continue
    P("section", sec, type(hg[sec]).__name__)
hs = hg["set"]; cs = cg["set"]
def gk(e):
    return (e["원보험사코드"], e["항목번호"], e["공시분기"])
hsk = {gk(e): e for e in hs}
csk = {gk(e): e for e in cs}
P("gold set head", len(hs), len(hsk), "cur", len(cs), len(csk))
P("gold existing modified", sum(1 for k in hsk if csk.get(k) != hsk[k]), "removed", len(set(hsk) - set(csk)))
new = [csk[k] for k in csk if k not in hsk]
P("gold new set entries", len(new))
P("new set companies", sorted({e["원보험사코드"] for e in new}))
P("new set quarters", sorted({(e["원보험사코드"], e["공시분기"]) for e in new}))
P("new set items", sorted({e["항목번호"] for e in new}))
P("existing-order prefix preserved", [gk(e) for e in cs[:len(hs)]] == [gk(e) for e in hs])
for sec in ("null_dangi", "set_dangi", "mask", "masks"):
    if sec in hg or sec in cg:
        P("sec", sec, "head", json.dumps(hg.get(sec), ensure_ascii=False)[:100], )
for sec in cg:
    if sec in ("set", "_doc"):
        continue
    h = hg.get(sec); c = cg[sec]
    if isinstance(c, dict) and "cells" in c:
        hc = [tuple(x[:3]) if isinstance(x, list) else x for x in (h or {}).get("cells", [])]
        cc = [x for x in c["cells"]]
        P(sec, "head cells", len(hc), "cur cells", len(cc))
        hs_ = {json.dumps(x, ensure_ascii=False) for x in (h or {}).get("cells", [])}
        newc = [x for x in cc if json.dumps(x, ensure_ascii=False) not in hs_]
        gone = len(hs_ - {json.dumps(x, ensure_ascii=False) for x in cc})
        P(sec, "new", len(newc), "removed", gone)
        with open(OUT + "/v1_gold_new_%s.json" % sec, "w", encoding="utf-8") as f:
            json.dump(newc, f, ensure_ascii=False)
    else:
        P(sec, "other", json.dumps(c, ensure_ascii=False)[:200], "same as head", h == c)
with open(OUT + "/v1_gold_new_set.json", "w", encoding="utf-8") as f:
    json.dump(new, f, ensure_ascii=False)
with open(OUT + "/v1_diff.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
