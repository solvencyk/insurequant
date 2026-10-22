"""a19_pl4_master: master PL item 4 (+ CSM item 5) and the candidate PL4/CSM5 for the CSM-paired buckets (READ-ONLY)"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/cands_READY_all.json", encoding="utf-8").read())
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(R + "PL_breakdown.json", encoding="utf-8").read())}
csm = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(R + "CSM_waterfall.json", encoding="utf-8").read())}
cp = {(c["code"], c["q"], c["item"]): c for c in d["pl_cells"]}
cc = {(c["code"], c["q"], c["item"]): c for c in d["csm_cells"]}
for code, qs in (("KR0003", ("2023.1Q", "2023.2Q", "2024.1Q", "2024.2Q", "2024.3Q")), ("KR0079", ("2024.1Q", "2024.2Q", "2024.3Q")), ("KR0001", ("2023.1Q", "2023.2Q")), ("KR0068", ("2023.1Q", "2023.2Q", "2023.3Q"))):
    for q in qs:
        c4 = cp.get((code, q, 4)); c5 = cc.get((code, q, 5))
        print(code, q, "PL4 master", pl.get((code, 4, q)), "cand", None if c4 is None else c4["new"], "| CSM5 master", csm.get((code, 5, q)), "cand", None if c5 is None else c5["new"],
              "| ratio PL4/CSM5 master", None if pl.get((code, 4, q)) is None or csm.get((code, 5, q)) is None else round(pl[(code, 4, q)] / csm[(code, 5, q)], 3))
