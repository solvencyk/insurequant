import csv,json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
cells=json.load(open(HERE+"v01_PL_breakdown_cells.json",encoding="utf-8"))
chg={tuple(k) for k,f,a,b in cells if f=="값"}
master={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
rows=list(csv.DictReader(open(R+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
ex=[r for r in rows if r["sheet"]=="PL" and (r["code"],r["quarter"],int(r["item"])) not in chg]
print("excluded candidate cells:",len(ex))
out=[]
for r in ex:
    k=(r["code"],r["quarter"],int(r["item"])); m=master[k]
    new=float(r["new"]) if r["new"] not in ("",None) else None
    old=float(r["old"]) if r["old"] not in ("",None) else None
    d=None if (new is None or m is None) else new-m
    print(k,r["item_name"],"master",m,"csv-old",old,"csv-new",new,"delta(new-master)",None if d is None else round(d,3),"|",r["how"][:40],"|",r["cite(label|line|text)"][:70])
    out.append((k,m,new,d))
big=[x for x in out if x[3] is None or abs(x[3])>1.0001]
print("excluded with |delta|>1 mn or unknown:",len(big))
for x in big: print("   ",x)
