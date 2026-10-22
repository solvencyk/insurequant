# -*- coding: utf-8 -*-
"""Read-only dump of KR0104 PL_breakdown master cells (all fields) + gold overlay for KR0104."""
import json, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
rows = json.loads((ROOT/"PL_breakdown.json").read_text(encoding="utf-8"))
k = [r for r in rows if r["원보험사코드"] == "KR0104"]
out = []
out.append("keys of a row: " + json.dumps(sorted(k[0].keys()), ensure_ascii=False))
qs = sorted({r["공시분기"] for r in k})
out.append("quarters: " + ",".join(qs))
names = {}
for r in k: names[r["항목번호"]] = r["항목명"]
byk = {(r["공시분기"], r["항목번호"]): r for r in k}
for q in qs:
    if q[:4] not in ("2023","2024"): continue
    out.append("=== %s" % q)
    for i in range(1, 33):
        r = byk.get((q, i))
        if r is None:
            out.append("  %2d %s: <no row>" % (i, names.get(i))); continue
        extra = {a: b for a, b in r.items() if a not in ("원보험사코드","원보험사명","항목번호","항목명","공시분기","값","값_당분기")}
        out.append("  %2d %s: 값=%s 당분기=%s %s" % (i, r["항목명"], r.get("값"), r.get("값_당분기"), json.dumps(extra, ensure_ascii=False)))
g = json.loads((ROOT/"data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
out.append("gold type %s" % type(g).__name__)
def walk(o, path=""):
    if isinstance(o, dict):
        for kk, v in o.items():
            if "KR0104" in str(kk): out.append("GOLD %s/%s: %s" % (path, kk, json.dumps(v, ensure_ascii=False)[:3000]))
            else: walk(v, path+"/"+str(kk))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, dict) and v.get("원보험사코드") == "KR0104": out.append("GOLD[%d] %s" % (i, json.dumps(v, ensure_ascii=False)))
            else: walk(v, path+"[%d]" % i)
walk(g)
(HERE/"KR0104_master_dump.txt").write_text("\n".join(out)+"\n", encoding="utf-8", newline="\n")
print(len(out))
