# -*- coding: utf-8 -*-
"""CSM roll-forward identity on cumulative and on single-quarter cells for the five companies, live vs HEAD. Read-only."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_final_gates/"
def head(rel):
    b=subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout
    return json.loads(b.decode("utf-8"))
live=json.load(open(R+"/CSM_waterfall.json",encoding="utf-8")); hd=head("CSM_waterfall.json")
FIVE=["KR0099","KR0003","KR0070","KR0009","KR0072"]
lines=[]
def P(*a):
    s=" ".join(str(x) for x in a); lines.append(s); print(s)
def idx(d): return {(r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in d}
for label,d in (("LIVE",live),("HEAD",hd)):
    m=idx(d)
    P("=====",label)
    for co in FIVE:
        for fy in ("2023","2024"):
            for q in ("1Q","2Q","3Q","4Q"):
                qq=f"{fy}.{q}"
                g=lambda it,f="값":(m.get((co,it,qq)) or {}).get(f)
                vals=[g(i) for i in range(1,7)]
                svals=[g(i,"값_당분기") for i in range(1,7)]
                if any(v is None for v in vals): continue
                cres=vals[0]+vals[1]+vals[2]+vals[3]+vals[4]-vals[5]
                sres=None if any(v is None for v in svals) else svals[0]+svals[1]+svals[2]+svals[3]+svals[4]-svals[5]
                flag = (abs(cres)>0.6) or (sres is not None and abs(sres)>0.6)
                if flag or fy=="2023":
                    P(f"{label} {co} {qq} cum_resid={cres:+.2f} single_resid={'NA' if sres is None else format(sres,'+.2f')}", "<-- OFF" if flag else "")
open(OUT+"f03_csm_identity.txt","w",encoding="utf-8").write("\n".join(lines))
