import re, io, sys, json
D="data/dart/"
FILES={
 "ORIG_2024Q4":D+"FY2024_Q4/raw/KR0073_교보생명보험_20250331004015/xml/20250331004015.xml",
 "LATE_FY2025ann":D+"FY2025_Q4/raw/KR0073_교보생명보험_20260331004015/20260331004015.xml",
 "ORIG_2025Q1":D+"FY2025_Q1/raw/KR0073_교보생명보험/xml/20250515002967.xml",
 "LATE_FY2026Q1":D+"FY2026_Q1/raw/KR0073_교보생명보험/20260813001077.xml",
 "ORIG_2025Q2":D+"FY2025_Q2/raw/KR0073_교보생명보험/xml/20250814004112.xml",
 "LATE_FY2026Q2":D+"FY2026_Q2/raw/KR0073_교보생명보험/20260814004024.xml",
 "ORIG_2025Q3":D+"FY2025_Q3/raw/KR0073_교보생명보험/20251114002942.xml",
}
def num(s):
    s=re.sub(r'<[^>]+>','',s).strip().replace(',','')
    s=s.replace('△','-')
    neg=s.startswith('(') and s.endswith(')')
    s2=s.strip('()')
    if not re.fullmatch(r'-?\d+(\.\d+)?',s2): return None
    v=float(s2); return -v if neg else v
def tr_rows(txt):
    out=[]
    for m in re.finditer(r'<TR\b.*?</TR>',txt,re.S|re.I):
        blk=m.group(0)
        cells=[]
        for t in re.finditer(r'<(TD|TE|TH)\b([^>]*)>(.*?)</\1>',blk,re.S|re.I):
            body=re.sub(r'<[^>]+>','',t.group(3)).strip()
            ctx=re.search(r'ACONTEXT="([^"]*)"',t.group(2))
            cells.append((body,ctx.group(1) if ctx else None))
        out.append((txt.count("\n",0,m.start())+1,m.start(),cells))
    return out
if __name__=="__main__":
  pass
o=io.open("data/_derived/remaining_20261022/v_oci/dump_stmt.txt","w",encoding="utf-8")
for name,p in FILES.items():
    txt=io.open(p,encoding="utf-8",errors="replace").read()
    rs=tr_rows(txt)
    o.write("=== %s %s lines=%d\n"%(name,p,txt.count("\n")))
    # candidate OCI rows with >=2 numeric cells; preceding heading
    for i,(ln,pos,cells) in enumerate(rs):
        lab=cells[0][0].strip() if cells else ""
        if lab=="기타포괄손익" and sum(1 for c in cells[1:] if num(c[0]) is not None)>=2:
            head=re.findall(r'[^<>]{0,40}포괄손익계산서[^<>]{0,20}',txt[max(0,pos-4000):pos])
            o.write("-- candidate OCI row line %d; nearest heading: %s\n"%(ln,(head[-1] if head else None)))
            # print block: back up to 당기순이익 row (<=12 rows) to 총포괄손익
            j=i
            while j>0 and not (rs[j][2] and rs[j][2][0][0].strip().replace(" ","")=="당기순이익"): j-=1
            if i-j>14: j=i
            k=i
            while k<len(rs) and not (rs[k][2] and rs[k][2][0][0].strip().replace(" ","").startswith("총포괄손익")): k+=1
            for ln2,_,cs in rs[j:k+1]:
                vals=[(num(c[0]) if num(c[0]) is None else num(c[0]), c[1]) for c in cs[1:] if num(c[0]) is not None]
                o.write("  L%d %s | %s\n"%(ln2,cs[0][0] if cs else "",[ (v if x is None else (x.split('_')[0],v)) for v,x in vals]))
o.close()
