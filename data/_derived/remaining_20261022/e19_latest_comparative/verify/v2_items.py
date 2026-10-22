import json
ROOT="C:/Users/sangwook.cho/Desktop/insurequant"
cur=json.load(open(ROOT+"/PL_breakdown.json",encoding="utf-8"))
head=json.load(open("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/head_PL.json",encoding="utf-8"))
names={}
for r in cur: names[r["항목번호"]]=r["항목명"]
H={(r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in head}
C={(r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in cur}
out=[]
for i in sorted(names,key=str): out.append("%s %s"%(i,names[i]))
for code,q in [("KR0082","2023.3Q"),("KR0032","2024.1Q")]:
    out.append("== %s %s"%(code,q))
    for i in sorted(names,key=str):
        k=(code,i,q)
        if k in C:
            out.append("%2d %-20s head=%s cur=%s | dangi head=%s cur=%s"%(i,names[i],H[k]["값"],C[k]["값"],H[k].get("값_당분기"),C[k].get("값_당분기")))
open("v2_items.txt","w",encoding="utf-8").write("\n".join(out))
