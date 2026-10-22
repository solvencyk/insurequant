import sys,json,re,collections; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
recs=json.load(open(HERE+"v07_cites.json",encoding="utf-8"))
master={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
head={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(HERE+"head/PL_breakdown.json",encoding="utf-8"))}
buckets=collections.defaultdict(list)
for c in recs: buckets[(c["key"][0],c["key"][1])].append(c)
def norm(s):
    s=re.sub(r"\s+","",s); s=re.sub(r"^\(\d+\)","",s); s=re.sub(r"\(주\d+\)$","",s); return s
for (co,q),cs in sorted(buckets.items()):
    if co not in ("KR0010","KR0003","KR0001"): continue
    if (co,q,19) not in master: continue
    c=[x for x in cs if x["key"][2] in (17,20,24)]
    if not c: continue
    c=c[0]; doc=xmlrd.get(R+c["file"]); ti,t,row,cell=xmlrd.row_at_line(doc,c["line"])
    ci=row["cells"].index(cell); n=len(row["cells"]); unit=xmlrd.unit_div(c["unit"])
    got={}
    for r in t["rows"]:
        if len(r["cells"])!=n: continue
        k=norm(r["cells"][0]["t"])
        if k in ("보험금융수익","재보험금융수익","보험금융비용","재보험금융비용","출재보험금융수익","출재보험금융비용"):
            v=xmlrd.parse_num(r["cells"][ci]["t"]); 
            if v is None and r["cells"][ci]["t"].strip() in ("-","0"): v=0.0
            got.setdefault(k,v/unit if v is not None else None)
    ex=(got.get("보험금융수익",0) or 0)+(got.get("재보험금융수익",0) or 0)+(got.get("출재보험금융수익",0) or 0)-(got.get("보험금융비용",0) or 0)-(got.get("재보험금융비용",0) or 0)-(got.get("출재보험금융비용",0) or 0)
    m=master[(co,q,19)]; h=head.get((co,q,19))
    print(co,q,"lines",{k:round(v,3) for k,v in got.items()},"=> recomputed",round(ex,3),"master",m,"head",h,"" if abs(ex-m)<=1.001 else "  <== DIFF")
