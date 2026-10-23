import json, subprocess, sys, collections
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0009_hyundai/"
CO = "KR0009"
def head(path):
    r = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + path], capture_output=True)
    return json.loads(r.stdout.decode("utf-8"))
def work(path):
    with open(ROOT + "/" + path, encoding="utf-8") as f:
        return json.load(f)
lines = []
def P(s=""):
    print(s); lines.append(s)
for m in ("PL_breakdown", "CSM_waterfall"):
    h = head(m + ".json"); w = work(m + ".json")
    P("== %s: HEAD rows %d  WORK rows %d" % (m, len(h), len(w)))
    def idx(rows):
        d = {}; dup = 0
        for r in rows:
            k = (r["원보험사코드"], r["공시분기"], r["항목번호"])
            if k in d: dup += 1
            d[k] = r
        return d, dup
    hi, hd = idx(h); wi, wd = idx(w)
    P("dups head %d work %d" % (hd, wd))
    added = [k for k in wi if k not in hi]; removed = [k for k in hi if k not in wi]
    P("added keys all companies: %d, removed: %d" % (len(added), len(removed)))
    P("added by company: %s" % dict(collections.Counter(k[0] for k in added)))
    P("removed by company: %s" % dict(collections.Counter(k[0] for k in removed)))
    # changed by company
    chg_co = collections.Counter()
    for k in wi:
        if k in hi and hi[k] != wi[k]: chg_co[k[0]] += 1
    P("changed rows by company: %s" % dict(chg_co))
    # KR0009
    ch = []
    fields = collections.Counter()
    for k in sorted(set(hi) | set(wi), key=lambda t: (str(t[0]), str(t[1]), str(t[2]))):
        if k[0] != CO: continue
        a = hi.get(k); b = wi.get(k)
        if a == b: continue
        if a is None or b is None:
            ch.append((k, "ADDED/REMOVED", a, b)); continue
        for f in set(a) | set(b):
            if a.get(f) != b.get(f):
                ch.append((k, f, a.get(f), b.get(f))); fields[f] += 1
    P("KR0009 changed field-cells: %d; by field %s" % (len(ch), dict(fields)))
    byq = collections.defaultdict(lambda: collections.Counter())
    for k, f, a, b in ch: byq[k[1]][f] += 1
    for q in sorted(byq): P("  %s %s" % (q, dict(byq[q])))
    P("  by item: %s" % dict(sorted(collections.Counter(k[2] for k, f, a, b in ch).items())))
    with open(OUT + "v01_%s_changes.tsv" % m, "w", encoding="utf-8") as f:
        f.write("quarter\titem\tname\tfield\told\tnew\n")
        for k, fld, a, b in ch:
            nm = (b or a or {}).get("항목명") if isinstance(b or a, dict) else ""
            f.write("%s\t%s\t%s\t%s\t%r\t%r\n" % (k[1], k[2], (wi.get(k) or hi.get(k) or {}).get("항목명"), fld, a if not isinstance(a, dict) else "ROW", b if not isinstance(b, dict) else "ROW"))
    # other-field/row differences in non-KR0009 are not ours
    json.dump([[list(k), f, a, b] for k, f, a, b in ch], open(OUT + "v01_%s_changes.json" % m, "w", encoding="utf-8"), ensure_ascii=False, default=str)
# provenance
for m in ("PL_breakdown_provenance", "CSM_waterfall_provenance"):
    h = head(m + ".json"); w = work(m + ".json")
    P("== %s" % m)
    def cells(d):
        return d["cells"] if isinstance(d, dict) else d
    hc = cells(h); wc = cells(w)
    P("cells head %d work %d" % (len(hc), len(wc)))
    def key(c): return (c["company_code"], c["quarter"], c["item_block"])
    hk = {key(c): c for c in hc}; wk = {key(c): c for c in wc}
    P("added %d removed %d" % (len([k for k in wk if k not in hk]), len([k for k in hk if k not in wk])))
    dif = collections.Counter(); abl = []
    for k in wk:
        if k in hk and hk[k] != wk[k]:
            dif[k[0]] += 1
            if k[0] == CO: abl.append((k, hk[k], wk[k]))
    P("changed cells by company: %s" % dict(dif))
    top_h = {a: b for a, b in h.items() if a != "cells"} if isinstance(h, dict) else {}
    top_w = {a: b for a, b in w.items() if a != "cells"} if isinstance(w, dict) else {}
    P("top-level meta differs: %s" % (top_h != top_w))
    for k, a, b in abl:
        P("  HD %s" % (k,))
        P("    old %s" % json.dumps(a, ensure_ascii=False)[:1500])
        P("    new %s" % json.dumps(b, ensure_ascii=False)[:1500])
open(OUT + "v01_diff.txt", "w", encoding="utf-8").write("\n".join(lines))
