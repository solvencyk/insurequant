import json, sys, collections, os
R='C:/Users/sangwook.cho/Desktop/insurequant/'
H=R+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/head/'
OUT=R+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/'
def load(p):
    with open(p,encoding='utf-8') as f: return json.load(f)
def key(r): return (r['원보험사코드'],r['공시분기'],r['항목번호'])
lines=[]
def P(*a):
    s=' '.join(str(x) for x in a); lines.append(s); print(s)
for name in ['PL_breakdown','CSM_waterfall']:
    old=load(H+name+'.json'); new=load(R+name+'.json')
    om={key(r):r for r in old}; nm={key(r):r for r in new}
    P('==',name,'rows old',len(old),'new',len(new),'dupkeys',len(old)-len(om),len(new)-len(nm))
    added=set(nm)-set(om); removed=set(om)-set(nm)
    P('added',len(added),sorted(added)[:20],'removed',len(removed),sorted(removed)[:20])
    cc=collections.Counter(); byco=collections.Counter()
    rows=[]
    for k in om.keys()&nm.keys():
        a,b=om[k],nm[k]
        for fld in set(a)|set(b):
            if a.get(fld)!=b.get(fld):
                byco[(k[0])]+=1
                if k[0]=='KR0072':
                    cc[(k[1],k[2],fld)]+=1
                    rows.append((k[1],k[2],a.get('항목명'),fld,a.get(fld),b.get(fld)))
    P('changed field-count by company',dict(byco))
    # key order check / extra fields
    P('KR0072 changed cells:',len(rows))
    cnt=collections.Counter((q,f) for q,i,n,f,x,y in rows)
    P('per quarter/field',dict(sorted(cnt.items())))
    for q,i,n,f,x,y in sorted(rows):
        P('  ',q,i,n,f,x,'->',y)
with open(OUT+'d01_diff.txt','w',encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')
