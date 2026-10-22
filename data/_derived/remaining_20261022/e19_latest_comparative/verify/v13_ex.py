import json
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
head = json.load(open(SP + "/head_PL.json", encoding="utf-8"))
cur = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
H = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in head}
C = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cur}
o = []
for co, q, it in (("KR0104", "2023.4Q", 24), ("KR0104", "2023.4Q", 17), ("KR0005", "2023.4Q", 24), ("KR0032", "2023.4Q", 24), ("KR0032", "2023.4Q", 25), ("KR0087", "2023.4Q", 24), ("KR0087", "2023.4Q", 25)):
    k = (co, it, q)
    o.append("%s %s item %d dangi head=%s cur=%s (eok head=%s cur=%s)" % (co, q, it, H[k].get("값_당분기"), C[k].get("값_당분기"),
        None if H[k].get("값_당분기") is None else round(H[k]["값_당분기"] / 100, 1), None if C[k].get("값_당분기") is None else round(C[k]["값_당분기"] / 100, 1)))
# 3Q->4Q single-quarter mixture at HEAD: 4Q (annual, restated) minus 3Q old
open(V + "v13_ex.txt", "w", encoding="utf-8").write("\n".join(o))
