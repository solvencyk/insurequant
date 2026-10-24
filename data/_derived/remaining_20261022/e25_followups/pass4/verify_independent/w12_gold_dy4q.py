import json,sys
sys.stdout.reconfigure(encoding="utf-8")
g=json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_gold/user_pl_cells.json",encoding="utf-8"))
for e in g["set"]:
    if e["원보험사코드"]=="KR0087" and e["항목번호"] in (8,9,10,11,12) and e["공시분기"] in ("2024.4Q","2025.1Q","2024.2Q"):
        print(e["공시분기"],e["항목번호"],e["값"],"was",e.get("was"),"|",(e.get("note") or "")[:260].replace("\n"," "))
