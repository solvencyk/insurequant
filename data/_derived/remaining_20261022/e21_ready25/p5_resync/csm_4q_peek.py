# -*- coding: utf-8 -*-
import json, subprocess
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
old = json.loads(subprocess.check_output(["git", "-C", ROOT, "show", "HEAD~1:CSM_waterfall.json"]).decode("utf-8"))
new = json.load(open(ROOT + "/CSM_waterfall.json", encoding="utf-8"))
o = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in old}
for r in new:
    k = (r["원보험사코드"], r["항목번호"], r["공시분기"])
    if k[2].endswith("4Q"):
        p = o[k]
        for f in ("값", "값_당분기"):
            if p[f] != r[f]:
                print(k, f, p[f], "->", r[f])
