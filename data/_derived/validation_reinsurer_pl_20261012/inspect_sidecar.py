# -*- coding: utf-8 -*-
import json, collections
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
side = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
print(side.keys() if isinstance(side, dict) else type(side))
cells = side["cells"]
print(len(cells))
hows = collections.Counter()
ex = {}
for c in cells:
    for sf in c.get("source_files") or []:
        k = (sf.get("how"), c.get("item_block"), c.get("resolution"))
        hows[k] += 1
        ex.setdefault(k, (c, sf))
for k, v in hows.most_common():
    print(v, k)
for k, (c, sf) in ex.items():
    if k[0] and "reinsurer" in str(k[0]):
        print(json.dumps(c, ensure_ascii=False, indent=1)[:2500])
