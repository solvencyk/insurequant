import json,sys; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
m={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
h={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r for r in json.load(open(HERE+"head/PL_breakdown.json",encoding="utf-8"))}
for it in (1,17,19,20,22,24,25,26,27,31):
    row=[]
    for q in ("2024.1Q","2024.2Q","2024.3Q","2024.4Q"):
        r=m.get(("KR0083",q,it)); row.append((q[:6],None if r is None else round(r["값"]/100,1),None if r is None or r.get("값_당분기") is None else round(r["값_당분기"]/100,1)))
    hr=h.get(("KR0083","2024.4Q",it))
    print(it,row,"| HEAD 2024.4Q cum/dangi:",None if hr is None else (round(hr["값"]/100,1),None if hr.get("값_당분기") is None else round(hr["값_당분기"]/100,1)))
