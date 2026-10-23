# Own full read of the 4 statements of comprehensive income (KDB, separate) -> compare label-matched rows with the simulated post-load master and the HEAD master.
import json, re
ROOT='C:/Users/sangwook.cho/Desktop/insurequant/'
V=ROOT+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/'
exec(open(V+'v01_reread.py',encoding='utf-8').read().split('res=[]')[0].split("with open(K+'e23_plan_kdb_final.json'")[0])
CELL=re.compile(r'<(TD|TE|TH|TU)\b[^>]*>(.*?)</\1>',re.S)
def strip(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',s)).replace('&amp;','&').strip()
def num(s):
    s=s.replace(',','').strip()
    if s in ('','-'): return 0.0
    neg=(s.startswith('(') and s.endswith(')'))
    s=re.sub(r'[()\s]','',s)
    return -float(s) if neg else float(s)
files={'2023.1Q':('data/dart/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml',24188,4,2),
       '2023.2Q':('data/dart/FY2024_Q2/raw/KR0072_케이디비생명보험/20240814000801.xml',27548,4,2),
       '2023.3Q':('data/dart/FY2024_Q3/raw/KR0072_케이디비생명보험/20241114000809.xml',3909,4,2),
       '2023.4Q':('data/dart/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302.xml',5362,2,1)}
sim=json.load(open(V+'d05_sim.json',encoding='utf-8'))['newcum']
head=json.load(open(V+'head/PL_breakdown.json',encoding='utf-8'))
H={f"{r['공시분기']}|{r['항목번호']}":r['값'] for r in head if r['원보험사코드']=='KR0072'}
LAB={'보험손익':1,'기타사업비용':16,'투자손익':17,'영업이익':20,'영업이익(손실)':20,'영업외손익':21,'법인세비용차감전순이익':22,'법인세비용차감전순이익(손실)':22,'법인세비용':23,'법인세비용(수익)':23,'당기순이익':24,'당기순이익(손실)':24,'기타포괄손익':25,'총포괄손익':31,'총포괄이익':31,'총포괄이익(손실)':31}
out=open(V+'v03_stmt.txt','w',encoding='utf-8')
mism=0;match=0
for q,(p,t0,pcol,ccol) in files.items():
    with open(ROOT+p,encoding='utf-8',errors='replace') as f: L=f.read().split('\n')
    a=t0-1; b=a
    while b<len(L) and '</TABLE>' not in L[b].upper(): b+=1
    txt='\n'.join(L[a:b+1])
    rows=[]
    for tr in re.findall(r'<TR\b.*?</TR>',txt,re.S):
        c=[strip(m.group(2)) for m in CELL.finditer(tr)]
        if c: rows.append(c)
    out.write(f'=== {q} rows={len(rows)} first4={rows[:2]}\n')
    # Q4 statement is in 원 but the kinds of rows differ. unit 원 -> mn
    for c in rows:
        lab=c[0].replace(' ','')
        if len(c)<=pcol: continue
        try: v=num(c[pcol])/1e6
        except Exception: continue
        it=LAB.get(lab)
        s=sim.get(f'{q}|{it}') if it else None
        h=H.get(f'{q}|{it}') if it else None
        if it:
            # tax row printed as expense: master item 23 = -(printed)?
            out.write(f'  {c[0]!r:40} item{it:>3} printed_prior={v:.6f} sim={s} head={h}\n')
            if s is not None:
                ok=abs(s-v)<0.011 or (it==23 and abs(s+v)<0.011)
                match+=ok; mism+=(not ok)
        else:
            out.write(f'  {c[0]!r:40} printed_prior={v:.6f}\n')
out.write(f'\nlabel-matched rows: match={match} mismatch={mism}\n')
print('match',match,'mismatch',mism)
