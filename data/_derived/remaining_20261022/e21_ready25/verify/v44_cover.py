import json,csv,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
cells=json.load(open(HERE+"v01_PL_breakdown_cells.json",encoding="utf-8"))
chg={tuple(k) for k,f,a,b in cells if f=="값"}
cites=json.load(open(HERE+"v07_cites.json",encoding="utf-8"))
direct={tuple(c["key"]) for c in cites}
rows=list(csv.DictReader(open(R+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
how={(r["code"],r["quarter"],int(r["item"])):r["how"] for r in rows if r["sheet"]=="PL"}
NOTE_CO={"KR0010","KR0001","KR0003"}
NOTE_ITEMS={2,3,4,5,6,8,9,10,11,13,14}
LIFE_STMT={"KR0104","KR0068","KR0079","KR0083"}
cat=collections.defaultdict(list)
for k in sorted(chg):
    c,q,it=k
    if k in direct and how[k].startswith(("statement","note table")): cat["A direct cite read (value+col+basis+unit)"].append(k)
    elif c in NOTE_CO and it in NOTE_ITEMS: cat["B note-engine independent recompute (v10-v12)"].append(k)
    elif c in LIFE_STMT and it in (2,3,8,19) : cat["C life statement lines recompute (v13)"].append(k)
    elif c in ("KR0068","KR0079") and it==4: cat["D CSM-table (item4) re-read"].append(k)
    elif c=="KR0099": cat["E KB라이프 raw table L25521-25589"].append(k)
    elif k in direct: cat["A2 direct cite (compound legs)"].append(k)
    else: cat["F plug/derived: identity closure only"].append(k)
for k,v in cat.items(): print(len(v),k)
print("F items:",collections.Counter((x[0],x[2]) for x in cat["F plug/derived: identity closure only"]))
print("A2:",[ (x,how[x]) for x in cat.get("A2 direct cite (compound legs)",[])][:12])
