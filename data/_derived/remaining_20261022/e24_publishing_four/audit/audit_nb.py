import json, sys, subprocess, collections
sys.stdout.reconfigure(encoding='utf-8')
R='C:/Users/sangwook.cho/Desktop/insurequant/'
FOUR={'KR0099','KR0003','KR0070','KR0009'}
now=json.load(open(R+'NB_CSM_multiple.json',encoding='utf-8'))
head=json.loads(subprocess.run(['git','-C',R[:-1],'show','HEAD:NB_CSM_multiple.json'],capture_output=True).stdout.decode('utf-8'))
wf=json.load(open(R+'CSM_waterfall.json',encoding='utf-8'))
K=lambda r:(r['원보험사코드'],r['공시분기'])
n={K(r):r for r in now}; h={K(r):r for r in head}
print('rows now/head',len(now),len(head),'dups',len(now)-len(n),'keys equal',set(n)==set(h),'order same',[K(r) for r in now]==[K(r) for r in head])
ch=[]
for k in n:
    for f in n[k]:
        if n[k][f]!=h[k].get(f): ch.append((k,f,h[k].get(f),n[k][f]))
    if set(n[k])!=set(h[k]): print('FIELDSET DIFF',k)
print('changed cells',len(ch),dict(collections.Counter(k[0] for k,_,_,_ in ch)))
print('outside FOUR:',[c for c in ch if c[0][0] not in FOUR])
print('by field',dict(collections.Counter(f for _,f,_,_ in ch)))
# only expected fields (CSM + multiples), not 월납
print('월납 changed:',[c for c in ch if '월납' in c[1]])
# rows changed
rc=sorted(set(k for k,_,_,_ in ch)); print('rows touched',len(rc),rc)
# independent recompute vs waterfall item 2
w={(r['원보험사코드'],r['공시분기']):r for r in wf if r['항목번호']==2}
miss=[k for k in w if k not in n]; extra=[k for k in n if k not in w]
print('census: wf item2 rows',len(w),'missing in NB',miss,'extra in NB',extra)
bad=[]
def ratio(c,d):
    if c is None or d in (None,0) or c<=0: return None
    r=round(c/d,4); return None if r>40 else r
for k,r in n.items():
    x=w.get(k)
    if not x: continue
    if r['신계약CSM_연누계']!=x['값']: bad.append((k,'ytd',r['신계약CSM_연누계'],x['값']))
    # 당분기 vs wf 값_당분기 (str or number)
    xd=x.get('값_당분기'); xd=float(xd) if xd not in (None,'') else None
    nd=r['신계약CSM_당분기']
    if (xd is None)!=(nd is None) or (xd is not None and abs(xd-nd)>1e-6): bad.append((k,'dangi',nd,xd))
    for ax in('연누계','당분기'):
        e=ratio(r[f'신계약CSM_{ax}'],r[f'월납월초보험료_{ax}'])
        a=r[f'신계약CSM배수_{ax}']
        if (e is None)!=(a is None) or (e is not None and abs(e-a)>1e-4): bad.append((k,'mult_'+ax,a,e))
print('stale/mismatch vs waterfall master & ratio identity:',len(bad)); 
for b in bad[:20]: print('  ',b)
# (c) gate tolerance
tol=[(k,r['신계약CSM_연누계'],w[k]['값']) for k,r in n.items() if k in w and r['신계약CSM_연누계'] is not None and w[k]['값'] is not None and abs(r['신계약CSM_연누계']-w[k]['값'])>max(1.0,0.01*abs(w[k]['값']))]
print('NB_VS_WATERFALL tolerance (abs>max(1,1%)) violations:',len(tol),tol[:5])
exact=[(k) for k,r in n.items() if k in w and r['신계약CSM_연누계'] is not None and w[k]['값'] is not None and r['신계약CSM_연누계']!=w[k]['값']]
print('exact-inequality rows (any amount):',len(exact))
# ytd diff identity (b)
def pq(q):
    y,m=int(q[:4]),int(q[5]); return None if m==1 else f'{y}.{m-1}Q'
fails=0
for k,r in n.items():
    c,y=r['신계약CSM_당분기'],r['신계약CSM_연누계']
    if c is None or y is None: continue
    p=pq(k[1]); e=y if p is None else (n[(k[0],p)]['신계약CSM_연누계']-y)*-1 if (k[0],p) in n and n[(k[0],p)]['신계약CSM_연누계'] is not None else None
    if e is None: continue
    if abs(e-c)>max(0.5,0.01*abs(e)): fails+=1; print('YTD fail',k,c,e)
print('YTD identity fails',fails)
# 4 company grid coverage
for c in sorted(FOUR):
    qs=[k[1] for k in n if k[0]==c]; print(c,len(qs),min(qs),max(qs))
