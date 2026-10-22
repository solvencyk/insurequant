import json,csv,sys,collections
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
recs=json.load(open("v07_cites.json",encoding="utf-8"))
rows=list(csv.DictReader(open(R+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
how={(r["code"],r["quarter"],int(r["item"])):r["how"] for r in rows if r["sheet"]=="PL"}
mp=collections.defaultdict(collections.Counter)
for c in recs:
    k=tuple(c["key"])
    if how[k].startswith("statement") or how[k].startswith("note"):
        mp[k[2]][(k[0],c["row_label"])]+=1
for it in sorted(mp):
    print(it, dict(mp[it]))
