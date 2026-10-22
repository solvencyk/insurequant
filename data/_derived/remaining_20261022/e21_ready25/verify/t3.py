import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
recs=json.load(open("v07_cites.json",encoding="utf-8"))
MK=re.compile(r"<?\s*(제\s*\d+\s*\(\s*[전당]\s*\)\s*기[^>]{0,12}|전분기|전반기|전기|당분기|당반기|당기|전3분기|당3분기)\s*>?")
seen=set()
for c in recs:
    if c["prior"]: continue
    key=(c["file"],c["table_start"])
    if key in seen: continue
    seen.add(key)
    d=xmlrd.get(R+c["file"])
    ti,t,row,cell=xmlrd.row_at_line(d,c["line"])
    # markers within P elements before table up to 12000 chars
    seg=d.text[max(0,t["pos"]-15000):t["pos"]]
    ps=[(m.start(),xmlrd.strip(m.group(1))) for m in re.finditer(r"<P[^>]*>(.*?)</P>",seg,re.S)]
    mk=[(p,x) for p,x in ps if re.search(r"전분기|전반기|당분기|당반기|\(전\)|\(당\)|전기|당기",x) and len(x)<80]
    print(c["key"],c["file"].split("/")[-1],t["start"],"| LAST MARKERS:",[x for p,x in mk[-3:]])
