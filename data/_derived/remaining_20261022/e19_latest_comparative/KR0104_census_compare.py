# -*- coding: utf-8 -*-
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
p = json.loads((HERE/"plan_KR0104.json").read_text(encoding="utf-8"))
v = json.loads((HERE/"KR0104_verify.json").read_text(encoding="utf-8"))
out = []
for c, k in zip(p["cells"], v["cells_check"]):
    out.append("i%2d %-22s cls=%-14s old=%s new=%s mine=%s census_new=%s census_cand=%s  new-census=%s" % (c["item"], c["item_name"], c["cls"], c["old"], c["new"], round(k["new_mine"], 6), c.get("census_new"), c.get("census_candidate_new"),
        None if c.get("census_new") is None else round(c["new"] - c["census_new"], 6)))
(HERE/"KR0104_census_compare.txt").write_text("\n".join(out)+"\n", encoding="utf-8", newline="\n")
print("\n".join(out))
