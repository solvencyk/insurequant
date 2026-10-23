# -*- coding: utf-8 -*-
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_final_gates/"
def head(rel):
    b=subprocess.run(["git","-C",R,"show","HEAD:"+rel],capture_output=True,stdin=subprocess.DEVNULL).stdout
    return json.loads(b.decode("utf-8"))
def idx(d): return {(r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in d}
PLl=idx(json.load(open(R+"/PL_breakdown.json",encoding="utf-8"))); PLh=idx(head("PL_breakdown.json"))
CSl=idx(json.load(open(R+"/CSM_waterfall.json",encoding="utf-8"))); CSh=idx(head("CSM_waterfall.json"))
NAMES={"KR0099":"KB라이프","KR0003":"롯데손보","KR0070":"ABL생명","KR0009":"현대해상","KR0072":"KDB생명"}
PLITEMS=[(1,"보험손익"),(17,"투자손익"),(24,"당기순이익"),(25,"OCI"),(31,"총포괄손익")]
lines=[]
def P(s): lines.append(s); print(s)
P("누계(값) 억원 = 백만원/100. HEAD -> LIVE (Δ, Δ%). single(당분기) 변화는 별도 표.")
flag=[]
for co,nm in NAMES.items():
    P(f"== {nm} {co}")
    for q in [f"2023.{i}Q" for i in (1,2,3,4)]:
        row=[]
        for it,lab in PLITEMS:
            a=(PLh.get((co,it,q)) or {}).get("값"); b=(PLl.get((co,it,q)) or {}).get("값")
            if a==b: continue
            ea=None if a is None else a/100; eb=None if b is None else b/100
            if ea is None or eb is None: row.append(f"{lab} {ea}->{eb}"); continue
            d=eb-ea; pc=(d/abs(ea)*100) if ea else float('inf')
            row.append(f"{lab} {ea:,.1f}->{eb:,.1f} ({d:+,.1f}; {pc:+.1f}%)")
            if abs(d)>=50 and (abs(pc)>=15): flag.append((nm,q,lab,ea,eb,d,pc))
            if a is not None and b is not None and a*b<0: flag.append((nm,q,lab+" SIGNFLIP",ea,eb,d,pc))
        a=(CSh.get((co,6,q)) or {}).get("값"); b=(CSl.get((co,6,q)) or {}).get("값")
        if a!=b: row.append(f"CSM기말 {a:,.1f}->{b:,.1f} ({b-a:+,.1f}; {(b-a)/abs(a)*100:+.2f}%)")
        a0=(CSh.get((co,1,q)) or {}).get("값"); b0=(CSl.get((co,1,q)) or {}).get("값")
        if a0!=b0: row.append(f"CSM기초 {a0}->{b0} ({b0-a0:+,.1f})")
        P(f"  {q}: "+(" | ".join(row) if row else "(no headline change)"))
P("\n== flagged: |Δ|>=50억 and |Δ%|>=15 or sign flip")
for f in flag: P("  FLAG %s %s %s %.1f -> %.1f (Δ %+.1f, %+.1f%%)"%f)
P("\n== 단일분기 headline (값_당분기, 억원) HEAD -> LIVE where changed")
for co,nm in NAMES.items():
    for q in [f"2023.{i}Q" for i in (1,2,3,4)]:
        row=[]
        for it,lab in PLITEMS:
            a=(PLh.get((co,it,q)) or {}).get("값_당분기"); b=(PLl.get((co,it,q)) or {}).get("값_당분기")
            if a==b: continue
            f=lambda x:"공란" if x is None else f"{x/100:,.1f}"
            row.append(f"{lab} {f(a)}->{f(b)}")
        if row: P(f"  {nm} {q}: "+" | ".join(row))
open(OUT+"f04_headline.txt","w",encoding="utf-8").write("\n".join(lines))
