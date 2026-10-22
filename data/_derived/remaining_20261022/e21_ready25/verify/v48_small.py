import json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
rows=json.load(open("v30_rows.json",encoding="utf-8"))
OUT={("KR0099",q) for q in ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"]}|{("KR0070",q) for q in ["2023.1Q","2023.2Q","2023.3Q","2023.4Q"]}|{("KR0003","2023.4Q")}
res=[]
for code,q,it,mv,hv,pv,ok,okold in rows:
    if (code,q) in OUT or mv is None or pv is None: continue
    d=mv-pv
    if abs(d)>0.55: res.append((code,q,it,round(mv,3),round(pv,3),round(d,3)))
print(len(res))
for r in res: print(r)
