import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
recs=json.load(open("v07_cites.json",encoding="utf-8"))
MK=re.compile(r"전분기|전반기|전3분기|\(전\)|전기|당분기|당반기|당3분기|\(당\)|당기")
seen=set()
for c in recs:
    if c["prior"]: continue
    key=(c["file"],c["table_start"])
    if key in seen: continue
    seen.add(key)
    d=xmlrd.get(R+c["file"])
    ti,t,row,cell=xmlrd.row_at_line(d,c["line"])
    for win in (3000,20000,80000):
        seg=xmlrd.strip(d.text[max(0,t["pos"]-win):t["pos"]])
        ms=[m for m in MK.finditer(seg)]
        if ms: break
    print(c["key"],c["file"].split("/")[-1],t["start"],"win",win,"|",[seg[max(0,m.start()-25):m.end()+10] for m in ms[-2:]])
