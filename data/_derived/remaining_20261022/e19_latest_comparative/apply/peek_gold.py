import json, sys
sys.stdout.reconfigure(encoding="utf-8")
g = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_gold/user_pl_cells.json", encoding="utf-8"))
out = [str(list(g.keys())), json.dumps(g["_doc"], ensure_ascii=False)[:600]]
for k in ("null_dangi", "set_dangi"):
    d = g[k]
    out.append(f"{k} {list(d.keys())} {len(d['cells'])}")
    for kk, v in d.items():
        if kk != "cells":
            out.append(f"   {kk} -> {str(v)[:500]}")
    out.append(f"  first cells: {d['cells'][:2]} last: {d['cells'][-1]}")
out.append(json.dumps(g["set"][0], ensure_ascii=False)[:500]); out.append(json.dumps(g["set"][-1], ensure_ascii=False)[:900])
open("peek_gold.txt", "w", encoding="utf-8").write("\n".join(out))
