# -*- coding: utf-8 -*-
import json, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant"
h = json.loads(subprocess.run(["git","-C",R,"show","HEAD:data/_gold/user_pl_cells.json"],capture_output=True).stdout.decode("utf-8"))
w = json.load(open(R+"/data/_gold/user_pl_cells.json", encoding="utf-8"))
pl = json.load(open(R+"/PL_breakdown.json", encoding="utf-8"))
M = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): (r.get("값"), r.get("값_당분기")) for r in pl}
hk = {(e["원보험사코드"], e["공시분기"], str(e["항목번호"])) for e in h["set"]}
bad = 0; n = 0
for e in w["set"]:
    k = (e["원보험사코드"], e["공시분기"], str(e["항목번호"]))
    if k in hk and k != ("KR0070","2025.3Q","7"): continue
    n += 1
    mv = M[k][0]
    ok = mv is not None and abs(mv - e["값"]) < 1e-6
    bad += (not ok)
    if not ok: print("GOLD != MASTER", k, e["값"], mv)
    # derived 7/12 formula
    if k[0]=="KR0070" and k[2] in ("7","12"):
        if k[2]=="7": f = M[(k[0],k[1],"3")][0]-(M[(k[0],k[1],"4")][0]+M[(k[0],k[1],"5")][0]+M[(k[0],k[1],"6")][0])
        else: f = M[(k[0],k[1],"8")][0]-(M[(k[0],k[1],"9")][0]+M[(k[0],k[1],"10")][0]+M[(k[0],k[1],"11")][0])
        print("derived", k, "gold", e["값"], "formula", round(f,6), "OK" if abs(f-e["값"])<1e-6 else "MISMATCH")
        bad += abs(f-e["값"])>=1e-6
print("new/changed gold cells checked", n, "mismatches", bad)
# any gold set entry (whole file) that disagrees with master now?
dis = [(e["원보험사코드"], e["공시분기"], e["항목번호"], e["값"], M.get((e["원보험사코드"], e["공시분기"], str(e["항목번호"])), (None,))[0]) for e in w["set"] if M.get((e["원보험사코드"], e["공시분기"], str(e["항목번호"])), (None,))[0] is None or abs(M[(e["원보험사코드"], e["공시분기"], str(e["항목번호"]))][0]-e["값"])>1e-6]
print("whole gold set disagreeing with master:", len(dis), dis[:10])
# null_dangi cells must have 값_당분기 None in master
for c in w["null_dangi"]["cells"]:
    k=(c[0],c[1],str(c[2]))
    v=M.get(k)
    if v is None or v[1] is not None: print("null_dangi cell with non-null single or missing row:", k, v)
print("null_dangi count", len(w["null_dangi"]["cells"]))
