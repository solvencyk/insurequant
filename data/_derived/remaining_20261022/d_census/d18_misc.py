# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
rows = json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8")); disp = json.loads((OUT / "d9_disposition.json").read_text(encoding="utf-8"))
a = [r for r in rows if r["scope"] == "A51"]
L = []
def P(s): L.append(s); print(s)
P("2026-10-12 PL verdict of the 51: " + str(Counter(r["pl_verdict_1012"] for r in a)))
own = [r for r in a if disp[f"{r['code']}|{r['q']}"]["disposition"] == "OWNER"]
g = [(r["name"], r["q"], r["gold_in_block"]) for r in own if r["gold_in_block"]]
P(f"OWNER 19: block-level gold present (held by the 2026-10-12 block rule, free under the cell-level rule): {len(g)} -> {g}")
P("OWNER 19 by company: " + str(Counter(r["name"] for r in own)))
P("A51 by company: " + str(Counter(r["name"] for r in a)))
# displayed headline moves for the 19
for it in (24, 17):
    xs = [x for r in own for x in r["disp"] if x["item"] == it]
    P(f"item {it}: n={len(xs)} abs>=20eok: {sum(1 for x in xs if abs(x['delta_eok']) >= 20)}; rel>=5%: {sum(1 for x in xs if x['rel'] is not None and abs(x['rel']) >= 0.05)}; rel>=10%: {sum(1 for x in xs if x['rel'] is not None and abs(x['rel']) >= 0.10)}")
# sensitivity of the SAFE count to the materiality threshold
def small_at(abs_t, rel_t):
    n = 0
    for r in own:
        ok = True
        for x in r["disp"]:
            if str(x["panel"]) == "download-only": continue
            if abs(x["delta_eok"] or 0) >= abs_t: ok = False
            if x["item"] in (1, 17, 24) and x["rel"] is not None and abs(x["rel"]) >= rel_t: ok = False
        n += ok
    return n
for t in ((20, 0.05), (50, 0.10), (100, 0.20), (10, 0.01)):
    P(f"closing buckets whose displayed moves are all below {t[0]} eok and {int(t[1]*100)}% (headline items): {small_at(*t)} of {len(own)}")
(OUT / "d18_misc.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
