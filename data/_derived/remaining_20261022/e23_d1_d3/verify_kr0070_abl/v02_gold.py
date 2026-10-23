import json, subprocess, collections
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
CO = "KR0070"
lines = []
def P(s=""):
    lines.append(s)
def head(path):
    r = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + path], capture_output=True)
    return json.loads(r.stdout.decode("utf-8"))
def work(path):
    return json.load(open(ROOT + "/" + path, encoding="utf-8"))
def flat(d):
    """yield (section, entry)"""
    out = []
    for sec, v in d.items():
        if isinstance(v, list):
            for e in v: out.append((sec, e))
        elif isinstance(v, dict):
            for sub, vv in v.items():
                if isinstance(vv, list):
                    for e in vv: out.append((sec + "." + sub, e))
    return out
def isco(e):
    if isinstance(e, dict): return e.get("원보험사코드") == CO
    if isinstance(e, list): return CO in e[:1] or (e and e[0] == CO)
    return False
for g in ("data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json"):
    h = head(g); w = work(g)
    P("=== %s  top keys head=%s work=%s" % (g, [k for k in h], [k for k in w]))
    fh = [(s, e) for s, e in flat(h) if isco(e)]
    fw = [(s, e) for s, e in flat(w) if isco(e)]
    P("KR0070 entries head %d work %d" % (len(fh), len(fw)))
    def kk(s, e):
        if isinstance(e, dict): return (s, e.get("공시분기"), e.get("항목번호"))
        return (s, e[1], e[2])
    dh = collections.defaultdict(list); dw = collections.defaultdict(list)
    for s, e in fh: dh[kk(s, e)].append(e)
    for s, e in fw: dw[kk(s, e)].append(e)
    for k in sorted(set(dh) | set(dw), key=str):
        a = dh.get(k); b = dw.get(k)
        if a == b: continue
        P("CHANGED %s" % (k,))
        P("   HEAD: %s" % json.dumps(a, ensure_ascii=False))
        P("   WORK: %s" % json.dumps(b, ensure_ascii=False))
    # same-count check of non-KR0070 changes: report counts by company of changed entries
    allh = collections.Counter(); allw = collections.Counter()
    sh = set(json.dumps(e, ensure_ascii=False, sort_keys=True) + s for s, e in flat(h))
    sw = set(json.dumps(e, ensure_ascii=False, sort_keys=True) + s for s, e in flat(w))
    P("entries only in HEAD: %d ; only in WORK: %d" % (len(sh - sw), len(sw - sh)))
    # by company
    def co(e):
        if isinstance(e, dict): return e.get("원보험사코드")
        return e[0] if isinstance(e, list) and e else None
    ch = collections.Counter(); cw = collections.Counter()
    fhs = {json.dumps(e, ensure_ascii=False, sort_keys=True) + s: e for s, e in flat(h)}
    fws = {json.dumps(e, ensure_ascii=False, sort_keys=True) + s: e for s, e in flat(w)}
    for k in set(fhs) - set(fws): ch[co(fhs[k])] += 1
    for k in set(fws) - set(fhs): cw[co(fws[k])] += 1
    P("only-HEAD by company %s" % dict(ch)); P("only-WORK by company %s" % dict(cw))
    # non-entry top-level differences
    for k in set(h) | set(w):
        if not isinstance(h.get(k), (list, dict)) and h.get(k) != w.get(k): P("top-level scalar changed: %s" % k)
open(OUT + "v02_gold.txt", "w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines)[:100])
