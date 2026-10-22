import json, sys
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(M + "cands_READY_all.json", encoding="utf-8").read())
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(R + "PL_breakdown.json", encoding="utf-8").read())}
for q in ("2023.4Q",):
    new = {c["item"]: c["new"] for c in d["pl_cells"] if c["code"] == "KR0010" and c["q"] == q}
    vec = {i: new.get(i, pl.get(("KR0010", i, q))) for i in range(25, 33)}
    print(q, vec, "I5 resid", vec[25] - sum(vec[i] for i in (26, 27, 28, 29, 30, 32)))
