import json,sys
sys.stdout.reconfigure(encoding="utf-8")
m=json.load(open("CSM_waterfall.json",encoding="utf-8"))
rows=[r for r in m if r["원보험사코드"]=="KR0068"]
print(len(rows), set(k for r in rows for k in r))
q=["2024.4Q","2025.1Q","2025.2Q","2025.3Q","2025.4Q","2026.1Q","2026.2Q"]
for no in range(1,12):
    out=[]
    for qq in q:
        c=[r for r in rows if r["항목번호"]==no and r["공시분기"]==qq]
        out.append(str([(x.get("값"),x.get("값_당분기")) for x in c]))
    nm=[r["항목명"] for r in rows if r["항목번호"]==no][:1]
    print(no,nm,out)
v=json.load(open("data/dart/viz/csm_waterfall.json",encoding="utf-8"))
print(type(v), list(v)[:10] if isinstance(v,dict) else len(v))
