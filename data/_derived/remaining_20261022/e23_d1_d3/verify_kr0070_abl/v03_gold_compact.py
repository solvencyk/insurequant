import json, subprocess, collections
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
CO = "KR0070"
def head(path):
    r = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + path], capture_output=True)
    return json.loads(r.stdout.decode("utf-8"))
def work(path):
    return json.load(open(ROOT + "/" + path, encoding="utf-8"))
def flat(d):
    out = []
    for sec, v in d.items():
        if isinstance(v, list):
            for e in v: out.append((sec, e))
        elif isinstance(v, dict):
            for sub, vv in v.items():
                if isinstance(vv, list):
                    for e in vv: out.append((sec + "." + sub, e))
    return out
def D(e):
    return e if isinstance(e, dict) else {"공시분기": e[1], "항목번호": e[2], "값": e[3:] }
def isco(e):
    if isinstance(e, dict): return e.get("원보험사코드") == CO
    if isinstance(e, list) and e: return e[0] == CO
    if isinstance(e, dict) and "cells" in e: return False
    return False
L = []
for g in ("data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json"):
    h = head(g); w = work(g)
    # null_dangi / set_dangi structure
    for sec in ("null_dangi", "set_dangi"):
        if sec in w:
            L.append("%s %s: head type %s keys %s" % (g, sec, type(h.get(sec)).__name__, list(h.get(sec, {}).keys()) if isinstance(h.get(sec), dict) else None))
            if isinstance(w[sec], dict) and "cells" in w[sec]:
                a = [c for c in h.get(sec, {}).get("cells", []) if c[0] == CO]
                b = [c for c in w[sec]["cells"] if c[0] == CO]
                L.append("  KR0070 %s cells head %d work %d; equal=%s" % (sec, len(a), len(b), a == b))
                allh = h.get(sec, {}).get("cells", []); allw = w[sec]["cells"]
                L.append("  total head %d work %d" % (len(allh), len(allw)))
    fh = [(s, e) for s, e in flat(h) if isco(e)]
    fw = [(s, e) for s, e in flat(w) if isco(e)]
    hs = {json.dumps([s, e], ensure_ascii=False, sort_keys=True): (s, e) for s, e in fh}
    ws = {json.dumps([s, e], ensure_ascii=False, sort_keys=True): (s, e) for s, e in fw}
    L.append("== %s: KR0070 entries head %d work %d, removed %d, added %d" % (g, len(fh), len(fw), len(set(hs) - set(ws)), len(set(ws) - set(hs))))
    for k in sorted(set(hs) - set(ws)):
        s, e = hs[k]; e = D(e); L.append("REMOVED/CHANGED-OLD %s %s q=%s it=%s 값=%s was=%s | %s" % (g.split("/")[-1], s, e.get("공시분기"), e.get("항목번호"), e.get("값"), e.get("was"), (e.get("note") or e.get("why") or "")[:400]))
    for k in sorted(set(ws) - set(hs)):
        s, e = ws[k]; e = D(e); L.append("ADDED/CHANGED-NEW %s %s q=%s it=%s 값=%s was=%s | %s" % (g.split("/")[-1], s, e.get("공시분기"), e.get("항목번호"), e.get("값"), e.get("was"), (e.get("note") or e.get("why") or "")[:260]))
    # which head entries are KR0070 for items in set
    L.append("-- unchanged KR0070 entries (carry-over): %d" % len(set(hs) & set(ws)))
    for k in sorted(set(hs) & set(ws)):
        s, e = hs[k]; e = D(e); L.append("   KEEP %s q=%s it=%s 값=%s" % (s, e.get("공시분기"), e.get("항목번호"), e.get("값")))
open(OUT + "v03_gold_compact.txt", "w", encoding="utf-8").write("\n".join(L))
