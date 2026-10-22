import json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
def load(p):
    d=collections.defaultdict(dict)
    for r in json.load(open(p,encoding="utf-8")): d[(r["원보험사코드"],r["공시분기"])][r["항목번호"]]=r["값"]
    return d
new=load(R+"PL_breakdown.json"); old=load(HERE+"head/PL_breakdown.json")
gold=json.load(open(R+"data/_gold/user_pl_cells.json",encoding="utf-8"))
gk={(e["원보험사코드"],e["공시분기"],e["항목번호"]):e for e in gold["set"]}
for q in ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q","2025.1Q","2025.2Q","2025.3Q","2025.4Q"]:
    m=new.get(("KR0010",q),{}); h=old.get(("KR0010",q),{})
    lob=[m.get(2),m.get(13),m.get(14)]
    br=None if None in lob or m.get(1) is None else sum(lob)-m[1]
    print(q,"item16 new",m.get(16),"head",h.get(16),"| gold",("yes" if ("KR0010",q,16) in gk else "no"),"| item1",m.get(1),"2+13+14-1 =",None if br is None else round(br,1),"| 15:",m.get(15))
