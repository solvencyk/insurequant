import re, io
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
    neg=s.startswith('(') and s.endswith(')')
    s2=s.strip('()')
    if not re.fullmatch(r'-?\d+(\.\d+)?',s2): return None
    v=float(s2); return -v if neg else v
def tr_rows(txt):
    out=[]
    for m in re.finditer(r'<TR\b.*?</TR>',txt,re.S|re.I):
        cells=[]
        for t in re.finditer(r'<(TD|TE|TH)\b([^>]*)>(.*?)</\1>',m.group(0),re.S|re.I):
            body=re.sub(r'<[^>]+>','',t.group(3)).strip()
            ctx=re.search(r'ACONTEXT="([^"]*)"',t.group(2))
            cells.append((body,ctx.group(1) if ctx else None))
        out.append((txt.count("\n",0,m.start())+1,m.start(),cells))
    return out
def isni(cells):
    if not cells: return False
    l=cells[0][0].replace(" ","")
    return bool(re.match(r"^(\(.\))?(\d\.)?(당기|반기|분기|당반기|당분기|당\(분\)기|당\(반\)기)?순이익|^(당기|반기|분기)순손익|^당기순이익",l)) and "법인세" not in l and "기타" not in l
def blocks(path):
    """OCI statement blocks: from 당기순이익 row to 총포괄손익 row, with basis tag."""
    txt=io.open(path,encoding="utf-8",errors="replace").read()
    rs=tr_rows(txt)
    res=[]
    for i,(ln,pos,cells) in enumerate(rs):
        if not cells or cells[0][0].strip()!="기타포괄손익": continue
        if sum(1 for c in cells[1:] if num(c[0]) is not None)<2: continue
        j=i
        while j>0 and not isni(rs[j][2]) and i-j<14: j-=1
        if not isni(rs[j][2]): continue
        k=i
        while k<len(rs) and k-i<30 and not (rs[k][2] and "총포괄손익" in rs[k][2][0][0].replace(" ","")): k+=1
        if not(rs[k][2] and "총포괄손익" in rs[k][2][0][0].replace(" ","")): continue
        ctxs=set(c[1] for r in rs[j:k+1] for c in r[2] if c[1])
        sep=any("SeparateMember" in (x or "") for x in ctxs)
        cons=any(x and "SeparateMember" not in x and "ConsolidatedMember" in x for x in ctxs)
        # heading: last '포괄손익계산서' title before block start with 별도/연결 within 30 chars before
        pre=re.sub(r'<[^>]+>',' ',txt[max(0,rs[j][1]-30000):rs[j][1]])
        hs=[m for m in re.finditer(r'(별\s*도|연\s*결)?\s*포\s*괄\s*손\s*익\s*계\s*산\s*서',pre)]
        head=None
        if hs:
            m=hs[-1]; head=pre[max(0,m.start()-12):m.end()].strip()
        res.append(dict(start=rs[j][0],end=rs[k][0],rows=[(r[0],r[2]) for r in rs[j:k+1]],sep_ctx=sep,cons_ctx=cons,head=head,nrows=k-j+1))
    return res
if __name__=="__main__":
    o=io.open("data/_derived/remaining_20261022/v_oci/locate.txt","w",encoding="utf-8")
    for n,p in FILES.items():
        for b in blocks(p):
            o.write("%s block L%d-L%d rows=%d sep_ctx=%s cons_ctx=%s head=%r OCI=%s\n"%(n,b["start"],b["end"],b["nrows"],b["sep_ctx"],b["cons_ctx"],b["head"],[ (num(c[0])) for c in b["rows"][[r[1][0][0] for r in b["rows"]].index("기타포괄손익")][1][1:] if num(c[0]) is not None]))
    o.close()
