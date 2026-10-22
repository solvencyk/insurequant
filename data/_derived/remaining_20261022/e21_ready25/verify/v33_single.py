# -*- coding: utf-8 -*-
"""v33: stored 값_당분기 vs cum_q - cum_{q-1} (same FY) for the 9 companies, HEAD vs NEW; classify against set_dangi/null_dangi registry."""
import json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
NINE=["KR0104","KR0083","KR0070","KR0079","KR0010","KR0099","KR0003","KR0001","KR0068"]
def load(p):
    d={}
    for r in json.load(open(p,encoding="utf-8")): d[(r["원보험사코드"],r["공시분기"],r["항목번호"])]=r
    return d
def reg(p):
    g=json.load(open(p,encoding="utf-8"))
    nd={tuple(x[:3]) for x in g.get("null_dangi",{}).get("cells",[])}
    sd={tuple(x[:3]):x[3] for x in g.get("set_dangi",{}).get("cells",[])}
    return nd,sd
for tag,mp,gp in (("HEAD",HERE+"head/PL_breakdown.json",HERE+"head/user_pl_cells.json"),("NEW",R+"PL_breakdown.json",R+"data/_gold/user_pl_cells.json")):
    M=load(mp); nd,sd=reg(gp)
    cnt=collections.Counter(); bad=[]
    for (c,q,it),r in M.items():
        if c not in NINE or q[:4] not in ("2023","2024"): continue
        qn=int(q[5])
        cum=r.get("값"); st=r.get("값_당분기")
        if qn==1:
            exp=cum
        else:
            prev=M.get((c,f"{q[:4]}.{qn-1}Q",it))
            pc=None if prev is None else prev.get("값")
            exp=None if (cum is None or pc is None) else cum-pc
        key=(c,q,it)
        if key in sd:
            cnt["set_dangi"]+=1
            if st is None or abs(st-sd[key])>1e-6: bad.append((key,"set_dangi value not honoured",st,sd[key]))
            continue
        if key in nd:
            cnt["null_dangi"]+=1
            if st is not None: bad.append((key,"null_dangi but stored not null",st))
            continue
        if exp is None and st is None: cnt["both-blank"]+=1; continue
        if exp is None and st is not None: cnt["stored-without-cum-pair"]+=1; bad.append((key,"stored without derivable pair",st,cum)); continue
        if st is None: cnt["stored-blank-though-derivable"]+=1; bad.append((key,"stored blank though derivable",exp)); continue
        if abs(st-exp)<=1e-4: cnt["derived-ok"]+=1
        else: cnt["MISMATCH"]+=1; bad.append((key,"stored != cum diff",st,round(exp,6)))
    print(tag,dict(cnt),"| registry sizes null/set:",len(nd),len(sd))
    nb=collections.Counter(b[1] for b in bad); print("   problems:",dict(nb))
    if tag=="NEW":
        for b in bad[:40]: print("   ",b)
