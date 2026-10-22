# -*- coding: utf-8 -*-
"""v36: for every headline cumulative cell that moved, classify the reason: compare HEAD/NEW with the ORIGINAL filing's own prints (separate and consolidated)."""
import sys,re,glob,os,json,collections; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
import importlib.util
spec=importlib.util.spec_from_file_location("hl","v30_headline.py")
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
LAB={1:r"^(Ⅰ\.|I\.)?(보험손익|보험서비스손익|보험영업손익)$",17:r"^(Ⅱ\.|II\.)?(투자손익|투자서비스손익)$",20:r"^(Ⅲ\.|III\.)?영업이익(\(손실\))?$",
 24:r"^(Ⅶ\.|VII\.|Ⅷ\.|VIII\.|Ⅸ\.|IX\.)?(당기|분기|반기)순(이익|손익)(\(손실\))?$",25:r"^(Ⅷ\.|VIII\.|Ⅸ\.|IX\.)?기타포괄(손익|이익)(\(손실\))?$",31:r"^(Ⅸ\.|IX\.|Ⅹ\.)?((당기|분기|반기)\s*)?총포괄(손익|이익)(\(손실\))?$"}
def nlab(s): return re.sub(r"\s+","",s)
def main_file(code,fy,q):
    d=glob.glob(R+f"data/dart/FY{fy}_Q{q}/raw/{code}*"); fs=[]
    for dd in d: fs+=glob.glob(dd+"/*.xml")+glob.glob(dd+"/xml/*.xml")
    fs=[f for f in fs if not f.endswith("_00760.xml")]
    return max(fs,key=os.path.getsize) if fs else None
def tables(doc):
    out=[]
    for t in doc.tables:
        labs=[nlab(r["cells"][0]["t"]) for r in t["rows"] if r["cells"]]
        if sum(1 for l in labs if re.search(r"보험손익|투자손익|영업이익|순이익|순손익|보험서비스손익|보험영업손익",l))>=3 and len(t["rows"])>15:
            bt=None
            for pos,ln,txt in reversed([x for x in doc.titles if x[0]<t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt=txt;break
            if bt and "주석" not in bt: out.append((("연결" if "연결" in bt else "별도"),t))
    return out
def read(doc,t):
    hdr=" ".join(c["t"] for r in t["rows"][:5] for c in r["cells"])
    per=len(set(re.findall(r"제\s*\d+\s*\(?[당전]?\)?\s*기",hdr))); has_cum="누적" in hdr.replace(" ","")
    unit=xmlrd.unit_div(doc.unit_before(t)); res={}
    for it,rx in LAB.items():
        for r in t["rows"]:
            cs=[c["t"] for c in r["cells"]]
            if cs and re.search(rx,nlab(cs[0])):
                nums=[xmlrd.parse_num(x) for x in cs[1:]]
                nums=[v for v,x in zip(nums,cs[1:]) if v is not None and not re.fullmatch(r"\d{1,2}",x.strip())]
                if has_cum and len(nums)>=4: res[it]=nums[-4:][1]/unit      # current cumulative
                elif per>=2 and len(nums)>=per: res[it]=nums[-per:][0]/unit  # current
                elif len(nums)>=1: res[it]=nums[-1]/unit if per<=1 else None
                break
    return res
def load(p):
    d={}
    for r in json.load(open(p,encoding="utf-8")): d[(r["원보험사코드"],r["공시분기"],r["항목번호"])]=r["값"]
    return d
new=load(R+"PL_breakdown.json"); old=load(HERE+"head/PL_breakdown.json")
cells=json.load(open(HERE+"v01_PL_breakdown_cells.json",encoding="utf-8"))
cq=sorted({(k[0],k[1]) for k,f,a,b in cells if f=="값"})
out=[]
for code,q in cq:
    y,qq=int(q[:4]),int(q[5])
    f=main_file(code,y,qq)
    if not f: print(code,q,"no original filing"); continue
    doc=xmlrd.get(f); tabs=tables(doc)
    prints={}
    for basis,t in tabs:
        if basis not in prints: prints[basis]=read(doc,t)
    for it in LAB:
        o,n=old.get((code,q,it)),new.get((code,q,it))
        if o==n: continue
        ps=prints.get("별도",{}).get(it); pc=prints.get("연결",{}).get(it)
        def eq(a,b): return a is not None and b is not None and abs(a-b)<=max(1.001,1e-6*abs(b))
        cls=("HEAD==orig별도" if eq(o,ps) else "HEAD==orig연결" if eq(o,pc) else "HEAD blank" if o is None else "HEAD!=orig prints")
        cls2=("NEW==orig별도 (no restatement)" if eq(n,ps) else "NEW!=orig별도 (restated)" if ps is not None else "orig별도 unreadable")
        out.append((code,q,it,o,n,ps,pc,cls,cls2))
cnt=collections.Counter((r[7],r[8]) for r in out)
for k,v in sorted(cnt.items()): print(v,k)
json.dump(out,open(HERE+"v36_why.json","w",encoding="utf-8"),ensure_ascii=False)
print()
for r in out:
    if r[7]!="HEAD==orig별도" or r[8]!="NEW!=orig별도 (restated)":
        print(r)
