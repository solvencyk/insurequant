import json,sys
sys.stdout.reconfigure(encoding="utf-8")
rows=json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json",encoding="utf-8"))
code=sys.argv[1]; qs=sys.argv[2].split(",")
names={}
for r in rows:
    if r["원보험사코드"]==code and r["공시분기"] in qs: names.setdefault(r["항목번호"],r["항목명"])
d={(r["공시분기"],r["항목번호"]):r for r in rows if r["원보험사코드"]==code}
for it in sorted(names):
    print(it,names[it],*["%s:%s/%s"%(q,d.get((q,it),{}).get("값"),d.get((q,it),{}).get("값_당분기")) for q in qs],sep="  ")
