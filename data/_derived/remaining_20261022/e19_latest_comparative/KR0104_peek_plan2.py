# -*- coding: utf-8 -*-
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
p = json.loads((HERE/"plan_KR0104.json").read_text(encoding="utf-8"))
out = []
def sh(o, ind=0, depth=0):
    pad = " "*ind
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)) and depth < 3:
                out.append("%s%s: %s(%d)" % (pad, k, type(v).__name__, len(v)))
                sh(v, ind+2, depth+1)
            else:
                out.append("%s%s: %s" % (pad, k, json.dumps(v, ensure_ascii=False)[:300]))
    elif isinstance(o, list):
        for i, v in enumerate(o[:2]):
            out.append("%s[%d]:" % (pad, i))
            sh(v, ind+2, depth+1)
sh(p)
(HERE/"KR0104_peek_plan2.txt").write_text("\n".join(out)+"\n", encoding="utf-8", newline="\n")
