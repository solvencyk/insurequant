import json, subprocess, sys
sys.path.insert(0, ".")
import vmaster
R = vmaster.ROOT
CO = "KR0009"
out = []
def P(s=""):
    out.append(s)
def key(e): return (e["원보험사코드"], e["공시분기"], e["항목번호"])
for n in ("user_pl_cells", "user_csm_cells"):
    h = vmaster.head("data/_gold/%s.json" % n); w = vmaster.work("data/_gold/%s.json" % n)
    P("=== %s" % n)
    P("top keys head %s" % list(h)); P("top keys work %s" % list(w))
    for sec in ("set",):
        hs = {key(e): e for e in h[sec] if e["원보험사코드"] == CO}
        ws = {key(e): e for e in w[sec] if e["원보험사코드"] == CO}
        P("set entries KR0009: head %d work %d (all companies head %d work %d)" % (len(hs), len(ws), len(h[sec]), len(w[sec])))
        dup_h = len([e for e in h[sec] if e["원보험사코드"] == CO]) - len(hs)
        dup_w = len([e for e in w[sec] if e["원보험사코드"] == CO]) - len(ws)
        P("dup keys head %d work %d" % (dup_h, dup_w))
        added = sorted(k for k in ws if k not in hs); removed = sorted(k for k in hs if k not in ws)
        changed = sorted(k for k in ws if k in hs and ws[k] != hs[k])
        P("ADDED %d, REMOVED %d, CHANGED %d, unchanged %d" % (len(added), len(removed), len(changed), len([k for k in ws if k in hs and ws[k] == hs[k]])))
        for k in removed:
            P("REMOVED %s: %s" % (k, json.dumps(hs[k], ensure_ascii=False)))
        for k in changed:
            P("CHANGED %s:\n   old %s\n   new %s" % (k, json.dumps(hs[k], ensure_ascii=False), json.dumps(ws[k], ensure_ascii=False)))
        for k in added:
            P("ADDED %s: %s" % (k, json.dumps(ws[k], ensure_ascii=False)))
    # other sections
    for sec in w:
        if sec in ("set", "_doc"): continue
        hv = h.get(sec); wv = w[sec]
        if hv != wv:
            P("SECTION %s differs: head=%s work=%s" % (sec, json.dumps(hv, ensure_ascii=False)[:1500], json.dumps(wv, ensure_ascii=False)[:3500]))
    for sec in h:
        if sec not in w: P("SECTION %s REMOVED" % sec)
    # whole-file other-company diff
    other_h = [e for e in h["set"] if e["원보험사코드"] != CO]; other_w = [e for e in w["set"] if e["원보험사코드"] != CO]
    P("non-KR0009 set entries: head %d work %d" % (len(other_h), len(other_w)))
open("v05_gold.txt", "w", encoding="utf-8").write("\n".join(out))
