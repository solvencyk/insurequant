import json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
H=json.load(open(HERE+"v30_headline.json",encoding="utf-8"))
def load(p):
    d={}
    for r in json.load(open(p,encoding="utf-8")): d[(r["원보험사코드"],r["공시분기"],r["항목번호"])]=r
    return d
new=load(R+"PL_breakdown.json"); old=load(HERE+"head/PL_breakdown.json")
chg_q=collections.defaultdict(set)
for k,f,a,b in json.load(open(HERE+"v01_PL_breakdown_cells.json",encoding="utf-8")):
    if f=="값": chg_q[(k[0],k[1])].add(k[2])
NINE=["KR0104","KR0083","KR0070","KR0079","KR0010","KR0099","KR0003","KR0001","KR0068"]
OUTOFSCOPE={("KR0099",q) for q in ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"]}|{("KR0070",q) for q in ["2023.1Q","2023.2Q","2023.3Q","2023.4Q"]}|{("KR0003","2023.4Q")}
res=collections.Counter(); bad=[]
for code in NINE:
    for q in ["2023.2Q","2023.3Q","2024.2Q","2024.3Q"]:
        rec=H.get(f"{code}|{q}")
        if not rec or "err" in rec: continue
        for it,v in rec["items"].items():
            it=int(it)
            m=new.get((code,q,it)); 
            if m is None: continue
            stored=m.get("값_당분기"); p3=v.get("pri3m")
            if p3 is None: continue
            if stored is None: res["stored-blank"]+=1; continue
            ok=abs(stored-p3)<=max(1.001,1e-6*abs(p3))
            tag=("SCOPE-NEEDS_OWNER" if (code,q) in OUTOFSCOPE else "IN")
            res[(tag,"ok" if ok else "MISMATCH")]+=1
            if not ok: bad.append((code,q,it,stored,round(p3,3),tag,"cum changed" if it in chg_q.get((code,q),set()) else "cum same"))
print(dict(res))
for b in bad: print("  MISMATCH",b)
