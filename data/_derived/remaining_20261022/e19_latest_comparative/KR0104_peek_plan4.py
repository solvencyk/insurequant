# -*- coding: utf-8 -*-
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
p = json.loads((HERE/"plan_KR0104.json").read_text(encoding="utf-8"))
out=[]
for k in ("verification","apply_contract","neighbour_effects"):
    out.append("--- "+k)
    out.append(json.dumps(p[k], ensure_ascii=False, indent=1)[:9000])
out.append("--- buckets[2] (2023.3Q) keys: " + ",".join(p["buckets"][2].keys()))
out.append("--- bucket 2023.4Q: " + json.dumps(p["buckets"][3], ensure_ascii=False)[:2500])
(HERE/"KR0104_peek_plan4.txt").write_text("\n".join(out)+"\n", encoding="utf-8", newline="\n")
