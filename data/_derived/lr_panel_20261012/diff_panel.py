import json
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
old = json.load(open(R/"data/_derived/lr_panel_20261012/bak/panel_loss_ratio.json", encoding="utf-8"))
new = json.load(open(R/"data/loss_ratio/panel_loss_ratio.json", encoding="utf-8"))
oc, nc = old["companies"], new["companies"]
same = diff = 0
dd = []
for k in oc:
    a = json.dumps(oc[k], ensure_ascii=False, separators=(",", ":"))
    b = json.dumps(nc.get(k), ensure_ascii=False, separators=(",", ":"))
    if a == b: same += 1
    else: diff += 1; dd.append(k)
print("old companies", len(oc), "byte-identical in new", same, "different", diff, dd)
added = sorted(set(nc) - set(oc))
print("added", added, [nc[k]["n"] for k in added], {k: sorted(nc[k]["q"]) for k in added})
print("old top keys", list(old), "new top keys", list(new))
for k in old["meta"]:
    if old["meta"][k] != new["meta"][k]: print("meta changed:", k, "|", str(old["meta"][k])[:80], "->", str(new["meta"][k])[:80])
ae = new["ae"]
n = sum(len(rs) for c in ae.values() for rs in c["q"].values())
print("ae companies", len(ae), "rows", n, "in companies:", sum(1 for k in ae if k in nc), "missing:", [k for k in ae if k not in nc])
print(json.dumps(ae["KR1000"], ensure_ascii=False)[:600])
# value equality with master
src = json.load(open(R/"data/loss_ratio/claims_ae_ratio.json", encoding="utf-8"))
bad = 0
for r in src:
    rs = ae[r["원보험사코드"]]["q"][r["공시분기"]]
    hit = [x for x in rs if x[0]==r["기준연도"] and x[1]==(r.get("사업구분") or "")]
    if len(hit)!=1 or hit[0][2:5]!=[r["예상손해율"],r["실제손해율"],r["예실차비율"]]: bad += 1
print("ae mismatches vs master:", bad, "of", len(src))
