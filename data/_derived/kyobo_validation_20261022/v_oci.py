import json, subprocess
def show(rev, f): return json.loads(subprocess.run(["git","show",f"{rev}:{f}"],capture_output=True,check=True).stdout.decode("utf-8"))
old, new = show("3e53aef8~1","PL_breakdown.json"), show("3e53aef8","PL_breakdown.json")
bs = json.load(open("IFRS17_BS.json", encoding="utf-8"))
def get(rows, it): return {r["공시분기"]: (r["값"], r["값_당분기"]) for r in rows if r["원보험사코드"]=="KR0073" and str(r["항목번호"])==str(it)}
o, n = get(old,25), get(new,25)
b = {r["공시분기"]: r["값"] for r in bs if r["원보험사코드"]=="KR0073" and r["항목번호"]==4}
qs = ["2022.4Q","2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q"]
for q in qs: print(q, "PL25 old", o.get(q), "new", n.get(q), " BS4", b.get(q))
chg = [(r["항목번호"], r["공시분기"]) for r in new if r["원보험사코드"]=="KR0073" and str(r["항목번호"]) in ("25","26","27","28","29","30","31","32") ]
d = [(r["항목번호"], r["공시분기"], r["값"], r["값_당분기"]) for r in new if r["원보험사코드"]=="KR0073" and str(r["항목번호"]) in ("25",) ]
oo = {(r["항목번호"], r["공시분기"]): (r["값"], r["값_당분기"]) for r in old if r["원보험사코드"]=="KR0073"}
nn = {(r["항목번호"], r["공시분기"]): (r["값"], r["값_당분기"]) for r in new if r["원보험사코드"]=="KR0073"}
print("OCI-block changes:", sorted(k for k in nn if str(k[0]) in [str(i) for i in range(25,33)] and nn[k]!=oo[k]))
