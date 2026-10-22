import sys,re,json,csv,glob,os; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
rows=list(csv.DictReader(open(R+"data/_derived/remaining_20261022/e20_held_and_remaining/measure/ready_cells_ALL.csv",encoding="utf-8-sig")))
files={}
for r in rows:
    if r["sheet"]=="PL" and r["code"] in ("KR0010","KR0003","KR0001"):
        files[(r["code"],r["quarter"])]=r["later_filing"].split(" (")[0].strip()
MK=re.compile(r"전분기|전반기|전3분기|\(전\)|전기|당분기|당반기|당3분기|\(당\)|당기")
for k,f in sorted(files.items()):
    d=xmlrd.get(R+f)
    print("==",k,f)
    for ti,t in enumerate(d.tables):
        labs=[r["cells"][0]["t"] if r["cells"] else "" for r in t["rows"]]
        if any(l.replace(" ","").startswith("총보험서비스결과") for l in labs) or any("서비스의 이전으로 당기손익" in l and ("보험수익" in l) for l in labs[:12]):
            seg=xmlrd.strip(d.text[max(0,t["pos"]-3000):t["pos"]])
            ms=list(MK.finditer(seg)); mk=seg[max(0,ms[-1].start()-2):ms[-1].end()+3] if ms else None
            bt=None
            for pos,ln,txt in reversed([x for x in d.titles if x[0]<t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt=txt;break
            print("  table",t["start"],t["end"],"rows",len(t["rows"]),"| marker:",mk,"| section:",bt)
