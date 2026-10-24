# -*- coding: utf-8 -*-
import sys,re,json
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent")
from w02_lib import *
sys.stdout.reconfigure(encoding="utf-8")
PL={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
M=lambda q,i,f="값":PL.get(("KR0087",q,i),{}).get(f)
out=[]; bad=0
def W(s): print(s); out.append(s)
def sep_line(p):
    with open(p,encoding="utf-8",errors="replace") as f:
        for i,l in enumerate(f,1):
            if re.search(r"<TITLE[^>]*>\s*5\.\s*재무제표 주석",l): return i
    raise SystemExit("no sep marker")
def reins_tables(fq):
    p=raw_path(fq,"KR0087"); s=sep_line(p); res=[]
    for t in read_tables(p):
        if t["line"]<s: continue
        labs=[("|".join(r["cells"])) for r in t["rows"]]
        if any(l.startswith("기초") and "출재보험계약자산" in l or l.startswith("기초 재보험계약자산") for l in labs):
            res.append(t)
    return p,s,res
def last_num(r):
    for c in reversed(r['cells']):
        v=to_num(c)
        if v is not None: return v
def find_row(t,pat):
    for r in t["rows"]:
        j="|".join(r["cells"])
        if re.search(pat,j) and last_num(r) is not None: return r
def last_num(r):
    for c in reversed(r["cells"]):
        v=to_num(c)
        if v is not None: return v
def open_total(t):
    for r in t["rows"]:
        j="|".join(r["cells"])
        if j.startswith("기초") : 
            return last_num(r)
def check(name,rawabs,m):
    global bad
    ok = m is not None and abs(abs(rawabs)-abs(m))<1e-6 and m<=0
    if not ok: bad+=1
    W("%s %-40s |raw|=%s master=%s"%("OK " if ok else "BAD",name,abs(rawabs),m))
# (fq, master quarter)
for fq,q in (("FY2025_Q1","2024.1Q"),("FY2025_Q2","2024.2Q"),("FY2025_Q3","2024.3Q")):
    p,s,ts=reins_tables(fq)
    W("## %s sep@%d reinsurance rollforward tables(after sep marker): %s"%(fq,s,[t["line"] for t in ts]))
    for t in ts: W("   table %d opening-total=%s"%(t["line"],open_total(t)))
    # prior table = second one whose opening(기초 재보험계약자산 first num) == known 2024.1.1 opening (12,333/12,334)
    pri=[t for t in ts if open_total(t) in (12333.0,12334.0) and find_row(t,r"보험계약마진 금액")]
    W("   prior-year (opening 12,333/12,334) tables: %s"%[t["line"] for t in pri])
    for t in pri:
        csm=find_row(t,r"보험계약마진 금액"); ra=find_row(t,r"비금융위험에 대한 위험조정")
        W("   t%d CSM row L%d printed total=%s | RA row L%d printed total=%s"%(t["line"],csm["line"],last_num(csm),ra["line"],last_num(ra)))
        check("%s item9 (CSM)"%q,last_num(csm),M(q,9)); check("%s item10 (RA)"%q,last_num(ra),M(q,10))
W("## singles / structure")
for q,prev in (("2024.2Q","2024.1Q"),("2024.3Q","2024.2Q")):
    for it in (9,10):
        s=M(q,it,"값_당분기"); d=M(q,it)-M(prev,it)
        ok=abs(s-d)<1e-6
        if not ok: bad+=1
        W("%s %s item%d single=%s cum-diff=%s"%("OK " if ok else "BAD",q,it,s,d))
for q in ("2024.1Q","2024.3Q"):
    W("%s item11 val/dangi=%s/%s item12 val/dangi=%s/%s"%(q,M(q,11),M(q,11,"값_당분기"),M(q,12),M(q,12,"값_당분기")))
    g=lambda i:M(q,i)
    W("   3=4+5+6+7: %s vs %s ; 2=3+8: %s vs %s ; 8=9+10+11+12: %s vs sum(9,10)=%s (11,12 blank)"%(g(3),sum(g(i) for i in (4,5,6,7)),g(2),g(3)+g(8),g(8),g(9)+g(10)))
W("4Q 9/10 cum %s %s; 4Q item11=%s item8=%s diff=%s"%(M("2024.4Q",9),M("2024.4Q",10),M("2024.4Q",11),M("2024.4Q",8),M("2024.4Q",11)-M("2024.4Q",8)))
W("BAD total %d"%bad)
open(R+"data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/w11_dy_verify.txt","w",encoding="utf-8").write("\n".join(out)+"\n")
