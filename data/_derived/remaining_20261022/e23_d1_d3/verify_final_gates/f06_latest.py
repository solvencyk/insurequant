import json,sys,collections
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
for f in ("CSM_waterfall.json","PL_breakdown.json"):
    d=json.load(open(R+f,encoding="utf-8"))
    qs=collections.defaultdict(set)
    for r in d: qs[r["원보험사코드"]].add(r["공시분기"])
    for c in ("KR0099","KR0003","KR0070","KR0009","KR0072"):
        s=sorted(qs[c]); print(f,c,"quarters",len(s),"first",s[0],"latest",s[-1])
