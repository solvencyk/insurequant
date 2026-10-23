# Simulate the planned KDB load on a HEAD copy (in memory only) and check: old values, single-quarter recompute, identities, CSM chain.
import json, collections, copy
ROOT='C:/Users/sangwook.cho/Desktop/insurequant/'
V=ROOT+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/'
H=V+'head/'
def load(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
plan=load(ROOT+'data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/e23_plan_kdb_final.json')
pl=load(H+'PL_breakdown.json'); csm=load(H+'CSM_waterfall.json')
goldpl=load(H+'user_pl_cells.json')
Q=['2023.1Q','2023.2Q','2023.3Q','2023.4Q','2024.1Q']
def sel(rows,co='KR0072'):
    d={}
    for r in rows:
        if r['원보험사코드']==co: d[(r['공시분기'],r['항목번호'])]=r
    return d
P=sel(pl); C=sel(csm)
out=open(V+'d05_sim.txt','w',encoding='utf-8')
def W(*a):
    s=' '.join(str(x) for x in a); out.write(s+'\n')
# gold null/set dangi at HEAD for KR0072
nd=[c for c in goldpl['null_dangi']['cells'] if c[0]=='KR0072']
sd=[c for c in goldpl['set_dangi']['cells'] if c[0]=='KR0072']
W('HEAD null_dangi KR0072',nd); W('HEAD set_dangi KR0072',sd)
# (1) rule check at HEAD: dangi == cum - prev cum
def dangi_rule(cum, q, item, nullset, setmap, over=None):
    qi=Q.index(q)
    if (q,item) in setmap: return setmap[(q,item)]
    if (q,item) in nullset: return None
    cur=cum.get((q,item))
    if cur is None: return None
    if q.endswith('1Q'): return cur
    prev=cum.get((Q[qi-1],item))
    if prev is None: return None
    return cur-prev
nullset={(c[1],c[2]) for c in nd}; setmap={(c[1],c[2]):c[3] for c in sd}
cum0={k:r['값'] for k,r in P.items()}
bad=[]
for (q,i),r in sorted(P.items()):
    if q not in Q[:4]: continue
    e=dangi_rule(cum0,q,i,nullset,setmap)
    a=r.get('값_당분기')
    if (e is None)!=(a is None) or (e is not None and abs(e-a)>0.0051): bad.append((q,i,a,e))
W('HEAD recompute-rule mismatches (rule check):',len(bad),bad[:40])
# (2) old values still match HEAD
oldbad=[]
n_pl=0
newcum=dict(cum0)
chg=[]
for b in plan['buckets']:
    for c in b['cells']:
        k=(c['quarter'],c['item']); n_pl+=1
        h=P.get(k,{}).get('값')
        if (h is None and c['old'] is not None) or (h is not None and (c['old'] is None or abs(h-c['old'])>1e-9)): oldbad.append((k,h,c['old']))
        newcum[k]=c['new']
        chg.append((k,h,c['new']))
W('PL planned cells',n_pl,'old!=HEAD',oldbad)
cnt=collections.Counter(k[0] for k,h,n in chg); W('per quarter',dict(cnt))
W('PL cells where new==HEAD (no-op):',[(k) for k,h,n in chg if h is not None and abs(h-n)<1e-9])
W('PL cells where |new-HEAD|<=0.01 (rounding-size):',[(k,h,n) for k,h,n in chg if h is not None and 0<abs(h-n)<=0.01])
# seam overrides from plan
ap=plan['apply_contract']
W('apply_contract keys',{k:(len(v) if hasattr(v,'__len__') else v) for k,v in ap.items()})
nd2=set(nullset); sd2=dict(setmap)
for e in ap.get('null_dangi_add',[]):
    nd2.add((e[1],e[2]) if isinstance(e,list) else (e['quarter'],e['item']))
for e in ap.get('null_dangi_remove',[]):
    nd2.discard((e[1],e[2]) if isinstance(e,list) else (e['quarter'],e['item']))
for e in ap.get('set_dangi_add',[]):
    if isinstance(e,list): sd2[(e[1],e[2])]=e[3]
    else: sd2[(e['quarter'],e['item'])]=e['value']
for e in ap.get('set_dangi_remove',[]):
    sd2.pop((e[1],e[2]) if isinstance(e,list) else (e['quarter'],e['item']),None)
W('after null_dangi',sorted(nd2),'after set_dangi',sorted(sd2.items()))
# single-quarter before/after
chg_d=[];
for (q,i),r in sorted(P.items()):
    if q not in Q[:4]: continue
    a=r.get('값_당분기'); e=dangi_rule(newcum,q,i,nd2,sd2)
    if (a is None)!=(e is None) or (a is not None and abs(a-e)>1e-9): chg_d.append((q,i,a,e))
W('single-quarter cells that change (sim):',len(chg_d))
W('  per quarter',dict(collections.Counter(x[0] for x in chg_d)))
for x in chg_d: W('  ',x)
json.dump({'newcum':{f'{k[0]}|{k[1]}':v for k,v in newcum.items() if k[0] in Q},'dangi_changes':chg_d},open(V+'d05_sim.json','w',encoding='utf-8'),ensure_ascii=False)
# (3) identities cum and single, HEAD vs sim
def val(d,q,i):
    return d.get((q,i))
IDS={
 'I_2=3+8':lambda g:(g(2),[g(3),g(8)]),
 'I_1=2+13+14+15-16':lambda g:(g(1),[g(2),g(13),g(14),g(15),None if g(16) is None else -g(16)]),
 'I_17=18+19':lambda g:(g(17),[g(18),g(19)]),
 'I_20=1+17':lambda g:(g(20),[g(1),g(17)]),
 'I_22=20+21':lambda g:(g(22),[g(20),g(21)]),
 'I_23=22-24':lambda g:(g(23),[g(22),None if g(24) is None else -g(24)]),
 'I_31=24+25':lambda g:(g(31),[g(24),g(25)]),
 'I_25=26+27+28+29+30+32':lambda g:(g(25),[g(26),g(27),g(28),g(29),g(30),g(32)]),
}
def idcheck(cum,label,single=False):
    rows=[]
    for q in Q[:4]:
        if single:
            g=lambda i: dangi_rule(cum,q,i,nd2 if label=='SIM' else nullset,sd2 if label=='SIM' else setmap)
        else:
            g=lambda i: cum.get((q,i))
        for n,f in IDS.items():
            lhs,rhs=f(g)
            if lhs is None: rows.append((q,n,'LHS-none')); continue
            if any(x is None for x in rhs):
                # treat missing as zero but note
                s=sum(x for x in rhs if x is not None); miss=sum(1 for x in rhs if x is None)
                rows.append((q,n,round(lhs-s,4),f'missing_rhs={miss}'))
            else:
                rows.append((q,n,round(lhs-sum(rhs),4),''))
    return rows
for label,cum in (('HEAD',cum0),('SIM',newcum)):
    for single in (False,True):
        r=idcheck(cum,label,single)
        W(f'--- identities {label} {"single-quarter" if single else "cumulative"} (residual lhs-rhs; |res|>0.5 flagged)')
        for x in r:
            flag='  <<' if (isinstance(x[2],float) and abs(x[2])>0.5) or x[2]=='LHS-none' else ''
            W('  ',x,flag)
# (4) CSM planned vs HEAD
W('=== CSM')
ccount=0; cbad=[]
newc={k:r['值'] if False else r['값'] for k,r in C.items()}
for cb in plan['csm_buckets']:
    for c in cb['cells']:
        k=(cb['quarter'],c['item']); ccount+=1
        h=C[k]['값']
        if abs(h-c['old'])>1e-9: cbad.append((k,h,c['old']))
        newc[k]=c['new']
W('CSM planned cells',ccount,'old!=HEAD',cbad)
def csm_dangi(cum,q,i):
    qi=Q.index(q)
    if q.endswith('1Q'): return cum[(q,i)]
    if i==1: return cum[(Q[qi-1],6)]   # opening of the quarter = prior quarter closing
    if i==6: return cum[(q,6)]
    return cum[(q,i)]-cum[(Q[qi-1],i)]
for lab,cc in (('HEAD',{k:r['값'] for k,r in C.items()}),('SIM',newc)):
    W(f'--- CSM closure + opening chain {lab}')
    for q in Q:
        o,n,ii,a,am,cl=[cc[(q,i)] for i in range(1,7)]
        W('  ',q,'open',o,'close',cl,'closure resid (o+n+i+a+am-cl)',round(o+n+ii+a+am-cl,3))
    for q in Q[1:]:
        qi=Q.index(q)
        W('   boundary',Q[qi-1],'close',cc[(Q[qi-1],6)],'-> ',q,'cum opening',cc[(q,1)],'drift(open_q - FY opening)' if q!='2024.1Q' else 'FY boundary (open 2024.1Q - close 2023.4Q)',round(cc[(q,1)]-(cc[('2023.1Q',1)] if q!='2024.1Q' else cc[('2023.4Q',6)]),3))
    # single-quarter closure
    for q in Q[:4]:
        ds=[csm_dangi(cc,q,i) for i in range(1,7)]
        W('   single',q,'resid',round(ds[0]+ds[1]+ds[2]+ds[3]+ds[4]-ds[5],3),'dangi',[round(x,3) for x in ds])
    # HEAD single-quarter stored vs derived
HD={k:r.get('값_당분기') for k,r in C.items()}
W('HEAD stored dangi vs derived mismatch (opening=prior closing)',[(k,HD[k],round(csm_dangi({kk:r['값'] for kk,r in C.items()},k[0],k[1]),3)) for k in sorted(C) if k[0] in Q[:4] and abs(HD[k]-csm_dangi({kk:r['값'] for kk,r in C.items()},k[0],k[1]))>0.051])
