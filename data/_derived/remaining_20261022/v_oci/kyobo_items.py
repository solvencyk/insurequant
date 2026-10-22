import json,subprocess,io
c=json.load(open("PL_breakdown.json",encoding="utf-8"))
h=json.loads(subprocess.run(["git","show","HEAD:PL_breakdown.json"],capture_output=True,check=True).stdout.decode("utf-8"))
o=io.open("data/_derived/remaining_20261022/v_oci/kyobo_items.txt","w",encoding="utf-8")
names={}
for r in c:
    if r["원보험사코드"]=="KR0073": names[r["항목번호"]]=r["항목명"]
for k in sorted(names,key=str): o.write("%s %s\n"%(k,names[k]))
def g(rows,item,q):
    for r in rows:
        if r["원보험사코드"]=="KR0073" and r["항목번호"]==item and r["공시분기"]==q: return r["값"],r["값_당분기"]
o.write("\nitem quarter head_val head_dangi | cur_val cur_dangi\n")
for it in (1,6,7,17,24,25,26,27,28,29,30,31,32):
    for q in ("2024.3Q","2024.4Q","2025.1Q","2025.2Q","2025.3Q","2025.4Q"):
        o.write("%s %s %s | %s\n"%(it,q,g(h,it,q),g(c,it,q)))
o.close()
