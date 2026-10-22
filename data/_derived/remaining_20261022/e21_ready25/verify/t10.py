import csv,json,sys,collections
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
cells=json.load(open("v01_PL_breakdown_cells.json",encoding="utf-8"))
chg={tuple(k):(a,b) for k,f,a,b in cells if f=="값"}
rows=list(csv.DictReader(open(R+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
for r in rows:
    if r["sheet"]!="PL": continue
    k=(r["code"],r["quarter"],int(r["item"]))
    if k in chg and r["how"] in ("derived from note legs","derived") :
        print(k,r["item_name"],r["old"],r["new"],r["how"],"|",r["source_table"],"|",r["later_filing"][-40:])
