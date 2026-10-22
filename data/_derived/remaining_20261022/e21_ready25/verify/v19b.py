import re,sys,json,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
def load(p):
    d=collections.defaultdict(dict)
    for r in json.load(open(p,encoding="utf-8")): d[(r["원보험사코드"],r["공시분기"])][r["항목번호"]]=r["값"]
    return d
new=load(R+"CSM_waterfall.json"); old=load(HERE+"head/CSM_waterfall.json")
NINE=["KR0104","KR0083","KR0070","KR0079","KR0010","KR0099","KR0003","KR0001","KR0068"]
def analyze(M,tag):
    print("=====",tag)
    for c in NINE:
        qs=sorted(q for (cc,q) in M if cc==c)
        if not qs: print(c,"no CSM rows"); continue
        for q in qs:
            m=M[(c,q)]
            v=[m.get(i) for i in range(1,7)]
            if all(x is not None for x in v):
                resid=v[0]+v[1]+v[2]+v[3]+v[4]-v[5]
                tol=max(0.5*1,0.005*abs(v[5]))   # 억
                if abs(resid)>0.15: print("  ",c,q,"closing identity resid",round(resid,2),"억 (close",v[5],")", "FAIL" if abs(resid)>tol else "ok-within-tol")
        # within-FY drift and FY boundary
        for y in (2023,2024,2025):
            opens={q:M[(c,q)].get(1) for q in qs if q.startswith(str(y))}
            vals=[v for v in opens.values() if v is not None]
            if len(vals)>1 and (max(vals)-min(vals))>0.15: print("  ",c,y,"within-FY opening drift:",opens)
        for y in (2024,2025):
            prev=M.get((c,f"{y-1}.4Q"),{}).get(6)
            for q in qs:
                if q.startswith(str(y)):
                    o=M[(c,q)].get(1)
                    if prev is not None and o is not None and abs(o-prev)>max(2.0,0.005*abs(prev)):
                        print("  ",c,q,"FY boundary break: open",o,"vs prev 4Q close",prev,"diff",round(o-prev,1),"(",round((o-prev)/prev*100,2),"%)")
analyze(old,"HEAD"); analyze(new,"NEW")
