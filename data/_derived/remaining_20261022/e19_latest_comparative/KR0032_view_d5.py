# -*- coding: utf-8 -*-
import json
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
b = json.loads((R / "data/_derived/remaining_20261022/d_census/d5_buckets.json").read_text(encoding="utf-8"))
L = []
for x in b:
    if x.get("code") != "KR0032":
        continue
    L.append("== " + x["q"] + " keys=" + ",".join(x.keys()))
    for k, v in x.items():
        if k == "its":
            for it, d in sorted(v.items(), key=lambda t: int(t[0])):
                L.append(f"   it{it}: {json.dumps(d, ensure_ascii=False)}")
        else:
            L.append(f"   {k}: {json.dumps(v, ensure_ascii=False)[:600]}")
Path(R / "data/_derived/remaining_20261022/e19_latest_comparative/KR0032_d5_view.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
