import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
M = R + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
d = json.loads(open(M + "cands_READY_all.json", encoding="utf-8").read())
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads(open(R + "PL_breakdown.json", encoding="utf-8").read())}
cs = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads(open(R + "CSM_waterfall.json", encoding="utf-8").read())}
src = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads(open(R + "data/dart/viz/pl_breakdown_master.json", encoding="utf-8").read())}
miss = [(c["code"], c["q"], c["item"]) for c in d["pl_cells"] if (c["code"], c["item"], c["q"]) not in pl]
miss_src = [(c["code"], c["q"], c["item"]) for c in d["pl_cells"] if (c["code"], c["item"], c["q"]) not in src]
print("PL cells without a row in PL_breakdown.json:", len(miss), miss[:10])
print("PL cells without a row in data/dart/viz/pl_breakdown_master.json (builder SRC):", len(miss_src), miss_src[:10])
print("CSM cells without a row:", [(c["code"], c["q"], c["item"]) for c in d["csm_cells"] if (c["code"], c["item"], c["q"]) not in cs])
# gold existing keys
g = json.loads(open(R + "data/_gold/user_pl_cells.json", encoding="utf-8").read())
gk = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in g["set"]}
print("PL gold keys already present for candidate cells:", [(c["code"], c["q"], c["item"]) for c in d["pl_cells"] if (c["code"], c["item"], c["q"]) in gk])
gc = json.loads(open(R + "data/_gold/user_csm_cells.json", encoding="utf-8").read())
print(list(gc.keys()), len(gc["set"]))
gck = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gc["set"]}
print("CSM gold keys present for candidate cells:", [(c["code"], c["q"], c["item"], gck[(c["code"], c["item"], c["q"])]["값"], c["new"]) for c in d["csm_cells"] if (c["code"], c["item"], c["q"]) in gck])
print("PL gold top-level:", list(g.keys()), {k: (len(v["cells"]) if isinstance(v, dict) and "cells" in v else None) for k, v in g.items() if isinstance(v, dict)})
print("sample gold set entry:", json.dumps(g["set"][-1], ensure_ascii=False)[:500])
print("sample csm gold entry:", json.dumps(gc["set"][-1], ensure_ascii=False)[:500])
