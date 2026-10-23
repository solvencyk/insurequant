# Full CSM census: re-read all 6 items x 4 quarters from the prior-year CSM table of the later filing and compare with the simulated post-load master (and HEAD).
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
head=json.load(open(V+'head/CSM_waterfall.json',encoding='utf-8'))
H={(r['공시분기'],r['항목번호']):r['값'] for r in head if r['원보험사코드']=='KR0072'}
S=dict(H)
for cb in plan['csm_buckets']:
    for c in cb['cells']: S[(cb['quarter'],c['item'])]=c['new']
tabs={'2023.1Q':('data/dart/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml',36277),
      '2023.2Q':('data/dart/FY2024_Q2/raw/KR0072_케이디비생명보험/20240814000801.xml',40636),
      '2023.3Q':('data/dart/FY2024_Q3/raw/KR0072_케이디비생명보험/20241114000809.xml',18341),
      '2023.4Q':('data/dart/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302.xml',26189)}
LAB={1:lambda l:l.startswith('1. 기초'),2:lambda l:l.startswith('(3) 최초 인식한 계약'),3:lambda l:l.startswith('6. 보험금융손익'),
     4:lambda l:l.startswith('(1) 보험계약마진을 조정하는'),5:lambda l:l.startswith('(1) 서비스 이전'),6:lambda l:l.startswith('9.')}
out=open(V+'v07_csm_census.txt','w',encoding='utf-8')
nok=nbad=0
for q,(p,t0) in tabs.items():
    with open(ROOT+p,encoding='utf-8',errors='replace') as f: L=f.read().split('\n')
    a=t0-1;b=a
    while b<len(L) and '</TABLE>' not in L[b].upper(): b+=1
    txt='\n'.join(L[a:b+1])
    rows=[[strip(m.group(2)) for m in CELL.finditer(tr)] for tr in re.findall(r'<TR\b.*?</TR>',txt,re.S)]
    rows=[r for r in rows if r]
    for it,fn in LAB.items():
        m=[r for r in rows if fn(r[0])]
        if len(m)!=1:
            out.write(f'{q} i{it}: label matches={len(m)} {[r[0][:30] for r in m]}\n'); nbad+=1; continue
        v=num(m[0][3])/100.0   # 백만원 -> 억원
        s=S[(q,it)]; h=H[(q,it)]
        good=abs(s-v)<=0.0501
        nok+=good; nbad+=(not good)
        out.write(f'{q} i{it} {m[0][0][:34]!r:38} printed={v:.2f} sim={s} head={h} {"OK" if good else "MISMATCH"}{"  (changed vs head)" if abs(s-h)>1e-9 else ""}\n')
out.write(f'ok={nok} bad={nbad}\n'); print('ok',nok,'bad',nbad)
