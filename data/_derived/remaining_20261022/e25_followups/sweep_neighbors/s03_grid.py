import json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT="C:/Users/sangwook.cho/Desktop/insurequant"
pl={ (r["원보험사코드"],str(r["항목번호"]),r["공시분기"]):r for r in json.load(open(f"{ROOT}/PL_breakdown.json",encoding="utf-8"))}
t=json.load(open("s01_touched.json",encoding="utf-8"))
moved=collections.defaultdict(set)
for k,v in t.items():
    fn,load=k.split("|")
    if not fn.startswith("PL"): continue
    for cq,items in v.items():
        c,q=cq.split("|")
        for i in items: moved[(c,q)].add(i)
cqs=sorted(moved, key=lambda x:(x[0],x[1]))
print("legend: M=moved by a load, .=present not moved, -=absent")
hdr=[str(i) for i in range(1,25)]
print("cq".ljust(16)+" ".join(h.rjust(2) for h in hdr))
for c,q in cqs:
    s=[]
    for i in range(1,25):
        r=pl.get((c,str(i),q))
        if r is None or r.get("값") is None: s.append(" -")
        elif str(i) in moved[(c,q)]: s.append(" M")
        else: s.append(" .")
    print(f"{c} {q}".ljust(16)+" ".join(s))
