import json, sys, subprocess, collections
sys.stdout.reconfigure(encoding='utf-8')
R='C:/Users/sangwook.cho/Desktop/insurequant/'
FOUR={'KR0099','KR0003','KR0070','KR0009'}
def gitj(f): return json.loads(subprocess.run(['git','-C',R[:-1],'show','HEAD:'+f],capture_output=True).stdout.decode('utf-8'))
def J(f): return json.load(open(R+f,encoding='utf-8'))
csm=J('CSM_waterfall.json'); pl=J('PL_breakdown.json'); nb=J('NB_CSM_multiple.json')
C={(r['원보험사코드'],r['공시분기'],r['항목번호']):r.get('값') for r in csm}
P={(r['원보험사코드'],r['공시분기'],r['항목번호']):r.get('값') for r in pl if isinstance(r['항목번호'],int)}
N={(r['원보험사코드'],r['공시분기']):r for r in nb}
# ---- compare
a=gitj('data/compare/panel_compare.json'); b=J('data/compare/panel_compare.json')
print('top-level equal parts:',{k:(a[k]==b[k]) for k in a})
qs=b['meta']['quarters']
am={m['id']:m for m in a['metrics']}; bm={m['id']:m for m in b['metrics']}
print('metric ids same/order',[m['id'] for m in a['metrics']]==[m['id'] for m in b['metrics']])
chg=[]; other=[]
for mid in bm:
    x,y=am[mid],bm[mid]
    for f in set(x)|set(y):
        if x.get(f)==y.get(f): continue
        if f in('v','v_pre'):
            for c in set(x[f])|set(y[f]):
                va=x[f].get(c); vb=y[f].get(c)
                if va!=vb:
                    for i in range(len(qs)):
                        if va is None or vb is None or va[i]!=vb[i]:
                            chg.append((mid,f,c,qs[i],None if va is None else va[i],None if vb is None else vb[i]))
        else:
            other.append((mid,f))
print('changed leaf values (v/v_pre):',len(chg),'; changed other fields:',sorted(set(other)))
print('by metric',dict(collections.Counter((c[0],c[1]) for c in chg)))
print('by company',dict(collections.Counter(c[2] for c in chg)))
print('NOT in FOUR:',[c for c in chg if c[2] not in FOUR])
print('blank->value:',sum(1 for c in chg if c[4] is None),' value->blank:',sum(1 for c in chg if c[5] is None))
# expected from masters
def exp(mid,c,q):
    if mid=='csm_closing': v=C.get((c,q,6)); return v
    if mid=='nb_multiple': r=N.get((c,q)); return None if r is None else r['신계약CSM배수_연누계']
    if mid=='nb_csm': r=N.get((c,q)); return None if r is None else r['신계약CSM_연누계']
    if mid=='ins_profit': v=P.get((c,q,1)); return None if v is None else v/100
    if mid=='net_income': v=P.get((c,q,24)); return None if v is None else v/100
    if mid=='inv_profit': v=P.get((c,q,17)); return None if v is None else v/100
    return 'n/a'
bad=0; ok=0; lines=[]
for mid,f,c,q,va,vb in chg:
    e=exp(mid,c,q)
    if e=='n/a': lines.append(('NO-MASTER-MAP',mid,c,q,va,vb)); continue
    tol=0.51 if bm[mid]['kind']=='eok' else 0.06
    good=(e is None and vb is None) or (e is not None and vb is not None and abs(e-vb)<=tol)
    ok+=good; bad+=(not good)
    if not good: print('MISMATCH',mid,c,q,'old',va,'new',vb,'expected',e)
    lines.append((mid,c,q,va,vb,e))
print('changed values checked against masters: ok',ok,'bad',bad)
# whole-grid recompute for the six metrics (all companies)
tot=0;badall=0
for mid in ('csm_closing','nb_multiple','nb_csm','ins_profit','net_income','inv_profit'):
    for c,v in bm[mid]['v'].items():
        for i,q in enumerate(qs):
            e=exp(mid,c,q); tol=0.51 if bm[mid]['kind']=='eok' else 0.06
            tot+=1
            if (e is None)!=(v[i] is None) or (e is not None and abs(e-v[i])>tol):
                badall+=1
                if badall<=10: print('GRID MISMATCH',mid,c,q,'panel',v[i],'master',e)
print('full-grid six metrics: cells',tot,'mismatch',badall)
# movers
mv=[(abs((vb or 0)-(va or 0)),mid,c,q,va,vb) for mid,f,c,q,va,vb in chg if f=='v' and bm[mid]['unit']=='억원']
mv.sort(reverse=True)
print('\nTop movers (억원):')
for d,mid,c,q,va,vb in mv[:14]: print(f'  {mid:12s} {c} {q} {va} -> {vb}  (Δ {None if va is None or vb is None else vb-va})')
# medians / na
mchg=[]
for mid in bm:
    for f in ('med','med_pre','na'):
        if am[mid].get(f)!=bm[mid].get(f): mchg.append((mid,f))
print('\nmedian/na fields changed:',mchg)
# companies list/loss_curve unchanged flagged above
# ---- combo
ca=gitj('data/csm_combo/panel_csm_combo.json'); cb=J('data/csm_combo/panel_csm_combo.json')
print('\ncombo meta equal',ca['meta']==cb['meta'],'companies keys equal',set(ca['companies'])==set(cb['companies']))
cols=cb['meta']['columns']; print('columns',cols)
cc=[]
for c in cb['companies']:
    x=ca['companies'][c]; y=cb['companies'][c]
    for k in ('n','type'):
        if x[k]!=y[k]: print('combo diff',c,k)
    assert set(x['q'])==set(y['q']),c
    for q in y['q']:
        for i,(p,r) in enumerate(zip(x['q'][q],y['q'][q])):
            if p!=r: cc.append((c,q,cols[i],p,r))
print('combo changed cells',len(cc),'companies',dict(collections.Counter(z[0] for z in cc)),'cols',dict(collections.Counter(z[2] for z in cc)))
for z in cc:
    e=N.get((z[0],z[1]),{}).get('신계약CSM_연누계') if False else None
    print('  ',z)
# combo nb_csm vs NB 당분기 whole grid
mm=0;tt=0
for c,v in cb['companies'].items():
    for q,arr in v['q'].items():
        e=N.get((c,q),{}).get('신계약CSM_당분기'); x=arr[cols.index('nb_csm')]
        tt+=1
        if (e is None)!=(x is None) or (e is not None and abs(e-x)>0.051): mm+=1; print('combo grid mismatch',c,q,x,e) if mm<=8 else None
print('combo nb_csm vs NB 당분기: cells',tt,'mismatch',mm)
for z in cc:
    e=N[(z[0],z[1])]['신계약CSM_당분기']; print('  combo spot',z[0],z[1],'new',z[4],'NB master 당분기',e)
