import csv, collections, sys, json
sys.stdout.reconfigure(encoding="utf-8")
ROOT="C:/Users/sangwook.cho/Desktop/insurequant/"
cells=json.load(open("v01_PL_breakdown_cells.json",encoding="utf-8"))
chg={tuple(k) for k,f,a,b in cells if f=="값"}
rows=list(csv.DictReader(open(ROOT+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
cnt=collections.Counter()
for r in rows:
    if r["sheet"]!="PL": continue
    k=(r["code"],r["quarter"],int(r["item"]))
    if k not in chg: continue
    c=r["cite(label|line|text)"]
    kind=r["how"][:30]
    cnt[(r["code"],kind,"cite" if c else "nocite")]+=1
for k,v in sorted(cnt.items()): print(k,v)
