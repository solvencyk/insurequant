# -*- coding: utf-8 -*-
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
p = json.loads((HERE/"plan_KR0104.json").read_text(encoding="utf-8"))
out = ["top keys: " + ",".join(p.keys())]
for k in p:
    if k in ("cells","buckets"): continue
    out.append("--- "+k)
    out.append(json.dumps(p[k], ensure_ascii=False, indent=1)[:7000])
(HERE/"KR0104_peek_plan3.txt").write_text("\n".join(out)+"\n", encoding="utf-8", newline="\n")
