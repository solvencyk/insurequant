# s01: cell-level diff vs git HEAD (KR0072 only) + other companies vs pre-load backup. Own code.
import json, collections
R='C:/Users/sangwook.cho/Desktop/insurequant/'
V=R+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
B=R+'data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb_load2/'
def load(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def key(r): return (r['원보험사코드'],r['공시분기'],r['항목번호'])
lines=[]
def P(*a):
    s=' '.join(str(x) for x in a); lines.append(s); print(s)
out={}
for name in ['PL_breakdown','CSM_waterfall']:
    old=load(V+'head/'+name+'.json'); new=load(R+name+'.json'); pre=load(B+name+'.json')
    om={key(r):r for r in old}; nm={key(r):r for r in new}; pm={key(r):r for r in pre}
    P('==',name,'rows head',len(old),'pre',len(pre),'new',len(new),'dupkeys',len(old)-len(om),len(new)-len(nm))
    P('added vs head',len(set(nm)-set(om)),'removed vs head',len(set(om)-set(nm)),'| added vs pre',len(set(nm)-set(pm)),'removed vs pre',len(set(pm)-set(nm)))
    P('key order identical vs head:', [key(r) for r in old]==[key(r) for r in new])
    # other companies vs pre-load backup
    oth=collections.Counter()
    for k in pm.keys()&nm.keys():
        if k[0]=='KR0072': continue
        a,b=pm[k],nm[k]
        for fld in set(a)|set(b):
            if a.get(fld)!=b.get(fld): oth[k[0]]+=1
    P('other-company field changes vs PRE-LOAD backup:',dict(oth))
    # KR0072 vs head
    rows=[]
    for k in om.keys()&nm.keys():
        if k[0]!='KR0072': continue
        a,b=om[k],nm[k]
        for fld in set(a)|set(b):
            if a.get(fld)!=b.get(fld): rows.append((k[1],k[2],a.get('항목명'),fld,a.get(fld),b.get(fld)))
    P('KR0072 changed cells vs HEAD:',len(rows))
    qs=sorted({r[0] for r in rows})
    P('quarters touched:',qs)
    cnt=collections.Counter((q,f) for q,i,n,f,x,y in rows)
    P('per quarter/field',dict(sorted(cnt.items())))
    cnt2=collections.Counter((i,f) for q,i,n,f,x,y in rows)
    P('per item/field',dict(sorted(cnt2.items())))
    # fields in KR0072 rows: any new keys?
    ks=collections.Counter()
    for k in nm:
        if k[0]=='KR0072':
            for f in nm[k]: ks[f]+=1
    P('KR0072 row field names',dict(ks))
    for r in sorted(rows,key=lambda r:(r[0],r[1],r[3])): P('  ',*r)
    out[name]=rows
with open(V+'s01_diff.txt','w',encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')
with open(V+'s01_changes.json','w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False)
