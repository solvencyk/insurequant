import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify")
import vstmt
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
head = json.load(open(SP + "/head_PL.json", encoding="utf-8"))
cur = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
H = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in head}
C = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cur}
out = []
for co in ("KR0087", "KR0070", "KR0032", "KR0083", "KR0082", "KR0005"):
    a = vstmt.read_separate_stmt(co, "2024.4Q"); b = vstmt.read_separate_stmt(co, "2025.4Q")
    ac = vstmt.item_values(a, "cur")[0]; bp = vstmt.item_values(b, "prior")[0]
    out.append("== %s 2024.4Q: master cum vs FY2024 annual cur vs FY2025 annual prior" % co)
    for it in sorted(set(ac) | set(bp)):
        m = C.get((co, it, "2024.4Q"))
        if not m: continue
        mv = m["값"]; x = ac.get(it); y = bp.get(it)
        if mv is None or x is None or y is None: 
            out.append("  item %2d master=%s annual24=%s annual25prior=%s" % (it, mv, x, y)); continue
        flag = "" if abs(x - y) < 0.51 else "  <-- FY2024 annual != FY2025 prior (restated again)"
        out.append("  item %2d master=%.3f annual24=%.3f annual25prior=%.3f dangi=%s%s" % (it, mv, x, y, m.get("값_당분기"), flag))
open(V + "v9_q4.txt", "w", encoding="utf-8").write("\n".join(out))
