import json, collections
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
h = json.load(open(SP + "/head_PLprov.json", encoding="utf-8"))
c = json.load(open(ROOT + "/PL_breakdown_provenance.json", encoding="utf-8"))
out = ["top keys head %s" % list(h.keys()), "top keys cur %s" % list(c.keys())]
out.append("head cells type %s len %d ; cur len %d" % (type(h["cells"]).__name__, len(h["cells"]), len(c["cells"])))
hc, cc = h["cells"], c["cells"]
if isinstance(hc, list):
    out.append("sample: " + json.dumps(hc[0], ensure_ascii=False)[:400])
    def kf(e): return json.dumps(e, sort_keys=True, ensure_ascii=False)
    hs = collections.Counter(kf(e) for e in hc); cs = collections.Counter(kf(e) for e in cc)
    removed = list((hs - cs).elements()); added = list((cs - hs).elements())
    out.append("removed %d added %d" % (len(removed), len(added)))
    def ident(e):
        return (e.get("원보험사코드") or e.get("code"), e.get("공시분기") or e.get("quarter"), e.get("항목번호") or e.get("item"))
    rm = [json.loads(x) for x in removed]; ad = [json.loads(x) for x in added]
    out.append("removed keys companies %s" % sorted({(ident(e)[0], ident(e)[1]) for e in rm}))
    out.append("added keys companies %s" % sorted({(ident(e)[0], ident(e)[1]) for e in ad}))
    out.append("added sample: " + json.dumps(ad[0], ensure_ascii=False)[:600])
else:
    out.append(json.dumps({k: type(v).__name__ for k, v in hc.items()})[:300])
mn = c.get("merge_note_20261022_e19_latest_comparative")
out.append("merge note: " + json.dumps(mn, ensure_ascii=False)[:800])
open(V + "v10_prov.txt", "w", encoding="utf-8").write("\n".join(out))
