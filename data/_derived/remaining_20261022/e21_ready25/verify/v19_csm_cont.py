# -*- coding: utf-8 -*-
import sys,json,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
def load(p):
    d=collections.defaultdict(dict)
    for r in json.load(open(p,encoding="utf-8")): d[(r["원보험사코드"],r["공시분기"])][r["항목번호"]]=r["값"]
    return d
new=load(R+"CSM_waterfall.json"); old=load(HERE+"head/CSM_waterfall.json")
NINE=["KR0104","KR0083","KR0070","KR0079","KR0010","KR0099","KR0003","KR0001","KR0068"]
Q=[f"{y}.{q}Q" for y in (2023,2024,2025) for q in (1,2,3,4)]
def vec(m): return [m.get(i) for i in range(1,7)]
for tag,M in (("HEAD",old),("NEW",new)):
    print("=====",tag)
    for c in NINE:
        qs=[q for q in Q if (c,q) in M]
        if not qs: print(c,"no CSM rows"); continue
        line=[]
        for q in qs:
            v=vec(M[(c,q)])
            ident=None
            if all(x is not None for x in v):
                ident=round(v[0]+v[1]+v[2]+v[3]+v[4]-v[5],2)
            line.append((q,v[0],v[5],ident))
        print(c)
        for q,o,cl,idn in line: print("   ",q,"open",o,"close",cl,"closing-identity resid(억)",idn)
