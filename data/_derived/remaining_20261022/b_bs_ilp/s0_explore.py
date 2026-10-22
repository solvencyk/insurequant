import json, sys
sys.stdout.reconfigure(encoding="utf-8")
for f in ["IFRS17_BS.json","insurance_liability_portfolio.json"]:
    d=json.load(open(f,encoding="utf-8"))
    print(f,type(d), (list(d.keys())[:10] if isinstance(d,dict) else len(d)))
    rows = d if isinstance(d,list) else None
    if rows is None:
        for k,v in d.items():
            if isinstance(v,list):
                print(" key",k,len(v)); rows=v; break
            else: print(" key",k,str(v)[:200])
    print(json.dumps(rows[0],ensure_ascii=False)[:600])
    kr=[r for r in rows if "KR0073" in json.dumps(r,ensure_ascii=False)[:200]]
    print("KR0073 rows",len(kr))
    qs=sorted({r.get("분기") for r in kr}, key=str)
    print(qs)
    print(json.dumps(kr[0],ensure_ascii=False)[:600])
