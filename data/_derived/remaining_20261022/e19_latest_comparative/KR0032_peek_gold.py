# -*- coding: utf-8 -*-
import json
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
g = json.loads((R / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
L = []
L.append("_doc: " + str(g.get("_doc"))[:600])
L.append("set sample: " + json.dumps(g["set"][-2:], ensure_ascii=False)[:1200])
nd = g["null_dangi"]
L.append("null_dangi _doc: " + str(nd.get("_doc"))[:800])
L.append("null_dangi cells n=%d sample: %s" % (len(nd["cells"]), json.dumps(nd["cells"][-5:], ensure_ascii=False)))
L.append("null_dangi extra keys: " + str([k for k in nd if k not in ("cells",)]))
sd = g["set_dangi"]
L.append("set_dangi _doc: " + str(sd.get("_doc"))[:800])
L.append("set_dangi cells n=%d sample: %s" % (len(sd["cells"]), json.dumps(sd["cells"][-3:], ensure_ascii=False)))
cos = sorted({e["원보험사코드"] for e in g["set"]})
L.append("set companies: " + ",".join(cos))
Path(R / "data/_derived/remaining_20261022/e19_latest_comparative/KR0032_peek_gold.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
