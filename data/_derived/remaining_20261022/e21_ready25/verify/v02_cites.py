import csv, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT="C:/Users/sangwook.cho/Desktop/insurequant/"
cells=json.load(open("v01_PL_breakdown_cells.json",encoding="utf-8"))
chg={}
for k,f,a,b in cells:
    if f=="값": chg[tuple(k)]=(a,b)
print(len(chg))
rows=list(csv.DictReader(open(ROOT+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
idx=collections.defaultdict(list)
for r in rows:
    if r["sheet"]!="PL": continue
    idx[(r["code"],r["quarter"],int(r["item"]))].append(r)
miss=[];multi=0
for k,(a,b) in sorted(chg.items()):
    rs=idx.get(k,[])
    if not rs: miss.append(k)
    if len(rs)>1: multi+=1
print("changed PL cells with no csv row:",len(miss),miss[:20])
print("multi-row:",multi)
extra=[k for k in idx if k not in chg]
print("csv rows (PL) for cells not changed in master:",len(extra))
print(collections.Counter(r["how"][:60] for rs in idx.values() for r in rs).most_common(30))
