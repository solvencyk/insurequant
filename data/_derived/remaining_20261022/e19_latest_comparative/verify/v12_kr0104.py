import json
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
head = json.load(open(SP + "/head_PL.json", encoding="utf-8"))
cur = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
H = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in head}
C = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cur}
o = []
for co, q, pq in (("KR0104", "2023.3Q", "2023.2Q"), ("KR0082", "2023.3Q", "2023.2Q"), ("KR0005", "2023.3Q", "2023.2Q")):
    o.append("== %s %s" % (co, q))
    for it in (1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32):
        k = (co, it, q); kp = (co, it, pq)
        if k not in C: continue
        o.append("  %2d cum3Q head=%s cur=%s | cum2Q=%s | dangi head=%s cur=%s | 3Q-2Q(cur)=%s" % (
            it, H[k]["값"], C[k]["값"], C[kp]["값"] if kp in C else None, H[k].get("값_당분기"), C[k].get("값_당분기"),
            None if (kp not in C or C[kp]["값"] is None or C[k]["값"] is None) else round(C[k]["값"] - C[kp]["값"], 6)))
open(V + "v12_seam_first.txt", "w", encoding="utf-8").write("\n".join(o))
