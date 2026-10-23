# Compare the simulated post-load single-quarter values with the 3-month column printed in the same later filing (prior year) for every label-matched row.
import json, re
ROOT='C:/Users/sangwook.cho/Desktop/insurequant/'
V=ROOT+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/'
CELL=re.compile(r'<(TD|TE|TH|TU)\b[^>]*>(.*?)</\1>',re.S)
def strip(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',s)).replace('&amp;','&').strip()
def num(s):
    s=s.replace(',','').strip()
    if s in ('','-'): return 0.0
    neg=(s.startswith('(') and s.endswith(')'))
    s=re.sub(r'[()\s]','',s)
    return -float(s) if neg else float(s)
plan=json.load(open(ROOT+'data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/e23_plan_kdb_final.json',encoding='utf-8'))
sim=json.load(open(V+'d05_sim.json',encoding='utf-8'))['newcum']
setd={}
for e in plan['apply_contract']['set_dangi_add']:
    setd[(e[1],e[2])]=e[3]
Q=['2023.1Q','2023.2Q','2023.3Q','2023.4Q']
def cum(q,i): return sim.get(f'{q}|{i}')
def single(q,i):
    if (q,i) in setd: return setd[(q,i)]
    c=cum(q,i)
    if c is None: return None
    if q=='2023.1Q': return c
    p=cum(Q[Q.index(q)-1],i)
    return None if p is None else c-p
files={'2023.1Q':('data/dart/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml',24188),
       '2023.2Q':('data/dart/FY2024_Q2/raw/KR0072_케이디비생명보험/20240814000801.xml',27548),
       '2023.3Q':('data/dart/FY2024_Q3/raw/KR0072_케이디비생명보험/20241114000809.xml',3909)}
LAB={'보험손익':1,'기타사업비용':16,'투자손익':17,'영업이익':20,'영업외손익':21,'법인세차감전순이익':22,'법인세차감전순이익(손실)':22,'법인세비용(수익)':23,'당기순이익':24,'당기순이익(손실)':24,'당기기타포괄손익':25,'당기총포괄손익':31}
out=open(V+'v06_single.txt','w',encoding='utf-8')
ok=bad=0
for q,(p,t0) in files.items():
    with open(ROOT+p,encoding='utf-8',errors='replace') as f: L=f.read().split('\n')
    a=t0-1; b=a
    while b<len(L) and '</TABLE>' not in L[b].upper(): b+=1
    txt='\n'.join(L[a:b+1])
    for tr in re.findall(r'<TR\b.*?</TR>',txt,re.S):
        c=[strip(m.group(2)) for m in CELL.finditer(tr)]
        if len(c)<5: continue
        it=LAB.get(c[0].replace(' ',''))
        if not it: continue
        p3=num(c[3])/1e6
        s=single(q,it)
        if s is None:
            out.write(f'{q} i{it} printed3m={p3:.6f} sim_single=None  (not in master after load)\n'); continue
        good=abs(s-p3)<0.011 or (it==23 and abs(s+p3)<0.011)
        ok+=good; bad+=(not good)
        out.write(f'{q} i{it} printed3m={p3:.6f} sim_single={s:.6f} diff={s-p3:+.6f} {"OK" if good else "MISMATCH"}\n')
out.write(f'ok={ok} bad={bad}\n')
print('ok',ok,'bad',bad)
