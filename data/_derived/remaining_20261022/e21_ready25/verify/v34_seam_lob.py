# -*- coding: utf-8 -*-
"""v34: LOB-note seam: next-year Q3 filing (prior 3개월 and 누적 cols) for Meritz/Lotte/KB 2023.3Q vs master (cum 2023.3Q unchanged, 2023.2Q changed)."""
import sys,re,json,glob,os; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd, v10_note_engine as E
R=E.ROOT
master,head=E.master,E.head
def lobs_tables(doc):
    out=[]
    for t in doc.tables:
        labs=[r["cells"][0]["t"].replace(" ","") for r in t["rows"] if r["cells"]]
        if any(l.startswith("총보험서비스결과") for l in labs) or ("보험계약마진상각" in "".join(labs) and "총재보험비용" in "".join(labs)):
            seg=xmlrd.strip(doc.text[max(0,t["pos"]-3000):t["pos"]])
            mk=re.findall(r"전분기|전반기|당분기|당반기",seg)
            bt=None
            for pos,ln,txt in reversed([x for x in doc.titles if x[0]<t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt=txt;break
            out.append((t,mk[-1] if mk else None,bt))
    return out
def main_file(code,fy,q):
    d=glob.glob(R+f"data/dart/FY{fy}_Q{q}/raw/{code}*")
    fs=[]
    for dd in d: fs+=glob.glob(dd+"/*.xml")+glob.glob(dd+"/xml/*.xml")
    fs=[f for f in fs if not f.endswith("_00760.xml")]
    return max(fs,key=os.path.getsize) if fs else None
def lob_vals(doc,t,sty):
    secs,cum_idx,ncols=E.read_table(doc,t)
    # derive 3m idx = cum idx - 1
    m3=[i-1 for i in cum_idx]
    return secs,cum_idx,m3
CASES=[("KR0001","MERITZ",[("2023.3Q",2024,3)]),("KR0003","LOTTE",[("2023.3Q",2024,3)]),("KR0010","KB",[("2023.3Q",2024,3)])]
ITEMS=[(4,"csm"),(5,"ra")]
for code,sty,qs in CASES:
    for q,fy,qq in qs:
        f=main_file(code,fy,qq); doc=xmlrd.get(f)
        cands=[c for c in lobs_tables(doc) if c[1] in ("전분기","전반기") and c[2] and "연결" not in c[2] and "주석" in c[2]]
        print("==",code,q,os.path.basename(f),"candidate prior separate tables:",[(c[0]["start"],c[1],c[2]) for c in cands])
        for t,mk,bt in cands[:1]:
            secs,cum_idx,m3=lob_vals(doc,t,sty)
            # CSM row (rev section) and RA row, first LOB (장기)
            def row(sec,needles):
                for lab,vals in secs.get(sec,[]):
                    l=lab.replace(" ","")
                    if any(n in l for n in needles) and not l.startswith("총"): return lab,vals
                return None,None
            for it,nm,sec,needles in ((4,"CSM상각","rev",["보험계약마진상각","당기손익으로인식한보험계약마진금액","제공된서비스의보험계약마진"]),(5,"RA","rev",["위험조정변동","위험해제에따른위험조정변동","위험해제로인한위험조정의변동"])):
                lab,vals=row(sec,needles)
                if vals is None: print("   no row",nm); continue
                c3=abs(vals[cum_idx[0]]); t3=abs(vals[m3[0]]) if m3[0]>=0 else None
                cur_cum3=master.get((code,q,it)); cur_cum2=master.get((code,"2023.2Q",it)); st=None
                print(f"   item{it} {nm}: printed prior cum(9M)={c3} prior 3M(Q3)={t3} | master cum 2023.3Q={cur_cum3} (HEAD {head.get((code,q,it))}) cum 2023.2Q={cur_cum2} (HEAD {head.get((code,'2023.2Q',it))})")
