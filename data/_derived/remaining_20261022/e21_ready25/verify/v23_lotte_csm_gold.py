import json,sys; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
o=json.load(open(HERE+"head/user_csm_cells.json",encoding="utf-8")); n=json.load(open(R+"data/_gold/user_csm_cells.json",encoding="utf-8"))
for tag,g in (("HEAD",o),("NEW",n)):
    for e in g["set"]:
        if e["원보험사코드"]=="KR0003" and e["공시분기"] in ("2023.1Q","2023.2Q","2023.3Q","2023.4Q"):
            print(tag,e["공시분기"],e["항목번호"],e["값"],"was",e.get("was"),"\n      WHY:",e.get("why","")[:1500])
