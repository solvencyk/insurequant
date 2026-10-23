# -*- coding: utf-8 -*-
import json, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant"
gj = lambda p: json.loads(subprocess.run(["git","-C",R,"show","HEAD:"+p],capture_output=True).stdout.decode("utf-8"))
h = gj("data/_gold/user_pl_cells.json"); pl = gj("PL_breakdown.json")
M = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r.get("값") for r in pl}
for e in h["set"]:
    k=(e["원보험사코드"], e["공시분기"], str(e["항목번호"]))
    mv=M.get(k)
    if e["값"] is None or mv is None or abs(mv-e["값"])>1e-6:
        if k[0] in ("KR0072","KR0087"): print("HEAD gold!=HEAD master", k, e["값"], mv)
