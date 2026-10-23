# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
pl=json.load(open(R+"/PL_breakdown.json",encoding="utf-8"))
M={(r["항목번호"]):r["값"] for r in pl if r["원보험사코드"]=="KR0099" and r["공시분기"]=="2023.4Q"}
for q in ("2023.4Q","2024.4Q"):
    tb=tables(load(XML[q]))
    c=[t for t in tb if "4-2. 포괄손익계산서" in t["pre"][-260:] and len(t["rows"])>30]
    print(q,"candidates",len(c))
    t=c[0]
    print(" header:",[x for x,_ in t["rows"][0]],[x for x,_ in t["rows"][1]],"| ncols row3",len(t["rows"][3]))
    d={}
    for r in t["rows"][2:]:
        cells=[x for x,_ in r]; d.setdefault(cells[0],[]).append(cells[1:])
    def g(lab,occ=0,col=0):
        a=d.get(lab); 
        return None if not a else num(a[occ][col])
    for lab,it in [("보험영업손익",1),("기타사업비용",16),("영업이익",20),("영업외손익",21),("법인세비용차감전순이익",22),("법인세비용",23),("당기순이익(손실)",24),("기타포괄손익",25),("총포괄손익",31),("보험금융손익",19),("투자영업손익",None)]:
        cur=g(lab,0,0); pri=g(lab,0,1) 
        print(f"  {lab}: cur={cur} prior={pri}", f"| master 4Q item{it}={M.get(it)}" if it else "")
