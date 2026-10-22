import csv, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT="C:/Users/sangwook.cho/Desktop/insurequant/"
rows=list(csv.DictReader(open(ROOT+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
seen=collections.Counter()
for r in rows:
    if r["sheet"]!="PL": continue
    h=r["how"][:40]
    seen[h]+=1
    if seen[h]<=2:
        print(r["code"],r["quarter"],r["item"],r["item_name"],"old",r["old"],"new",r["new"],"|",r["later_filing"],"|",r["source_table"],"|",r["cite(label|line|text)"],"|",r["how"])
