import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
csm = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))}
o = json.load(open("p3_existing.json", encoding="utf-8"))
n = 0; bad = []
for x in o:
    if x["sheet"] != "CSM" or "raw" not in x: continue
    raw = x["raw"]
    vec = raw.get("vec_exact") or raw.get("vec")
    if isinstance(vec, str): vec = eval(vec)
    if n == 0: print(type(vec), str(raw)[:400])
    n += 1
    for i in range(1, 7):
        try: v = vec[i - 1] if isinstance(vec, (list, tuple)) else vec[str(i)] if str(i) in vec else vec[i]
        except Exception: continue
        m = csm.get((x["code"], str(i), x["q"]))
        if m is None: bad.append((x["code"], x["q"], i, None, v)); continue
        if abs(m - v) > 0.06: bad.append((x["code"], x["q"], i, m, v, round(v - m, 3)))
print("CSM vectors", n, "cells differ >0.06 eok:", len(bad))
for b in bad: print(b)
