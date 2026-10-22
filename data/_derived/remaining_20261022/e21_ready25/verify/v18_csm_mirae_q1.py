# -*- coding: utf-8 -*-
import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
master={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"CSM_waterfall.json",encoding="utf-8"))}
head={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(HERE+"head/CSM_waterfall.json",encoding="utf-8"))}
f="data/dart/FY2025_Q1/raw/KR0079_미래에셋생명/20250515001717.xml"
d=xmlrd.get(R+f)
starts=[42459,43126,43793,44457,45121]
def trailing(cs,n=7):
    vals=[]
    for x in cs:
        v=xmlrd.parse_num(x)
        if v is None and x.strip()=="-": v=0.0
        vals.append(v)
    t=vals[-n:]
    return t if len(t)==n and all(v is not None for v in t) else None
tot={"open":0,"new":0,"int":0,"amort":0,"close":0,"adjrow":0}
for s in starts:
    ti,t=d.table_at_line(s); assert t["start"]==s,(s,t["start"])
    # locate '전분기' block: rows after the row whose cells contain '전분기'
    inprior=False; got={}
    hdr_ok = any("보험계약마진" in c["t"] for r in t["rows"][:6] for c in r["cells"])
    for r in t["rows"]:
        cs=[c["t"] for c in r["cells"]]
        if "전분기" in cs[:2]: inprior=True; continue
        if "당분기" in cs[:2] and inprior: inprior=False
        if not inprior: continue
        tl=trailing(cs)
        if tl is None: continue
        csm=tl[5]       # CSM 소계 (index 5 of 7)
        lab="".join(cs[:2]).replace(" ","")
        if lab.startswith("기초잔액") or "기초잔액" in lab: got.setdefault("open",csm)
        elif "처음인식한계약의효과" in lab: got["new"]=csm
        elif "당기손익인식보험금융손익" in lab: got["int"]=csm
        elif "보험계약마진의당기인식분" in lab: got["amort"]=csm
        elif "기말잔액" in lab: got["close"]=csm
        elif "보험계약마진을조정하는변" in lab: got["adjrow"]=csm
    print("table",s,"unit",d.unit_before(t),"CSM-subtotal header present",hdr_ok,got)
    for k,v in got.items(): tot[k]+=v
print("TOTAL (mn)",tot)
op,nw,it,am,cl=tot["open"],tot["new"],tot["int"],tot["amort"],tot["close"]
adj=cl-(op+nw+it+am)
e={1:op/100,2:nw/100,3:it/100,4:adj/100,5:am/100,6:cl/100}
for k in (1,2,3,4,5,6):
    m=master[("KR0079","2024.1Q",k)]; h=head[("KR0079","2024.1Q",k)]
    print(" item",k,"eok",round(e[k],3),"master",m,"head",h,"" if abs(e[k]-m)<=0.051 else "  <== DIFF")
