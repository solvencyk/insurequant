import json,sys; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
m={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
H=json.load(open("v30_headline.json",encoding="utf-8"))
for c in ("KR0068","KR0001","KR0003"):
    print(c,[ (q,m.get((c,q,25),{}).get("값"),m.get((c,q,25),{}).get("값_당분기")) for q in ("2023.1Q","2023.2Q","2023.3Q","2023.4Q")])
    for q in ("2023.1Q","2023.2Q","2023.3Q"):
        rec=H.get(f"{c}|{q}"); v=(rec or {}).get("items",{}).get("25")
        print("   printed (next-year filing):",q,v and {k:(None if x is None else round(x,1)) for k,x in v.items() if k!="line"})
