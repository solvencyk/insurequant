"""a16_life_probe: for each life READY bucket print the master note items 4,5,6,9,10,11 and the candidate cells 2,3,7,8,12,4 -- to design the independent life derivation (READ-ONLY)"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/cands_READY_all.json", encoding="utf-8").read())
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(R + "PL_breakdown.json", encoding="utf-8").read())}
cand = {(c["code"], c["q"], c["item"]): (c["old"], c["new"]) for c in d["pl_cells"]}
for code, qs in (("KR0104", ("2023.1Q", "2023.2Q")), ("KR0068", ("2023.1Q", "2023.2Q", "2023.3Q")), ("KR0079", ("2024.1Q", "2024.2Q", "2024.3Q")), ("KR0099", ("2024.1Q",))):
    for q in qs:
        m = {i: pl.get((code, i, q)) for i in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15)}
        c = {i: cand.get((code, q, i)) for i in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15) if cand.get((code, q, i))}
        print(code, q, "master:", {i: v for i, v in m.items()})
        print("      cand(old->new):", c)
