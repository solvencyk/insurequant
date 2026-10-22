import csv,sys,json; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
rows=list(csv.DictReader(open(R+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_csm_cells.csv",encoding="utf-8-sig")))
for r in rows:
    print(r["code"],r["quarter"],r["item"],r["old"],"->",r["new"],"|",r["later_filing"][-45:],"|",r["source_table"],"|",r["cite(label|line|text)"][:230],"|",r["how"][:80])
