# -*- coding: utf-8 -*-
import json
from pathlib import Path
D = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census")
c = json.loads((D/"cand_pl_cells.json").read_text(encoding="utf-8"))
L=[type(c).__name__, str(list(c.keys())[:10]) if isinstance(c,dict) else str(len(c))]
if isinstance(c,dict):
    for k,v in c.items():
        if "KR0083" in k or "KR0083" in json.dumps(v,ensure_ascii=False)[:200]:
            L.append(k+" "+json.dumps(v,ensure_ascii=False)[:1500])
else:
    for x in c:
        if "KR0083" in json.dumps(x,ensure_ascii=False): L.append(json.dumps(x,ensure_ascii=False))
Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/KR0083_peek_cand.txt").write_text("\n".join(L)+"\n",encoding="utf-8")
