# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
rows = json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8")); disp = json.loads((OUT / "d9_disposition.json").read_text(encoding="utf-8"))
a = [r for r in rows if r["scope"] == "A51"]
lines = []
def P(s): lines.append(s); print(s)
P(f"A51 buckets: {len(a)}; companies: {len({r['code'] for r in a})}")
P("kind: " + str(Counter(r["kind"] for r in a)))
own = [r for r in a if disp[f"{r['code']}|{r['q']}"]["disposition"] == "OWNER"]
P(f"OWNER (closing, no gold overlap): {len(own)}; companies {sorted({r['name'] for r in own})}")
def dd(r, item):
    for x in r["disp"]:
        if x["item"] == item: return x
for item, nm in ((17, "투자손익"), (24, "당기순이익"), (25, "기타포괄손익"), (1, "보험손익")):
    xs = [(dd(r, item), r) for r in own if dd(r, item)]
    if xs:
        dl = [x["delta_eok"] for x, r in xs]; rel = [x["rel"] for x, r in xs if x["rel"] is not None]
        P(f"  item {item} {nm}: {len(xs)} buckets; delta eok min {min(dl):+.1f} max {max(dl):+.1f}; rel min {min(rel)*100:+.1f}% max {max(rel)*100:+.1f}%")
P("sum delta item 24 (eok) over OWNER: %+.1f ; item 17: %+.1f" % (sum(dd(r, 24)["delta_eok"] for r in own if dd(r, 24)), sum(dd(r, 17)["delta_eok"] for r in own if dd(r, 17))))
big = [(r["name"], r["q"]) for r in own if disp[f"{r['code']}|{r['q']}"]["screen"] == "small"]
P("small-screen OWNER buckets: " + str(big))
nc = [r for r in a if disp[f"{r['code']}|{r['q']}"].get("closing") is False]
cat = Counter()
for r in nc:
    why = disp[f"{r['code']}|{r['q']}"]["why_not_closing"]
    tags = []
    if any("Tier-2 legs" in w for w in why): tags.append("LOB bridge breaks (item 1 moves)")
    if any("CSM waterfall restated" in w for w in why): tags.append("CSM restated")
    if any("could not be extracted" in w for w in why): tags.append("CSM prior column unreadable")
    if any("gold" in w for w in why): tags.append("CSM gold conflict")
    cat[tuple(tags)] += 1
P("not closing (22) by reason combination:")
for k, v in cat.most_common(): P(f"  {v:2d}  {' + '.join(k)}")
P("not-closing companies: " + str(Counter(r["name"] for r in nc)))
g = [r for r in a if disp[f"{r['code']}|{r['q']}"].get("closing") and r["gold_overlap"]]
P("closing but gold overlap: " + str([(r["name"], r["q"], r["gold_overlap"]) for r in g]))
noop = [r for r in a if disp[f"{r['code']}|{r['q']}"].get("closing") is None]
P("no-op: " + str([(r["name"], r["q"], r["kind"]) for r in noop]))
(OUT / "d15_stats.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
