# Independent re-read of every cited line of the KDB plan against the raw filing XML (own code, std lib only).
import json, re, sys, os, collections
ROOT='C:/Users/sangwook.cho/Desktop/insurequant/'
K=ROOT+'data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2/'
OUT=ROOT+'data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2/xcheck_validation_reader_'
with open(K+'e23_plan_kdb_final.json',encoding='utf-8') as f: plan=json.load(f)
_cache={}
def lines(path):
    if path not in _cache:
        with open(ROOT+path,encoding='utf-8',errors='replace') as f: _cache[path]=f.read().split('\n')
    return _cache[path]
def strip(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',s)).replace('&amp;','&').strip()
CELL=re.compile(r'<(TD|TE|TH|TU)\b[^>]*>(.*?)</\1>',re.S)
def tr_of(L,ln):
    a=ln-1
    while a>=0 and not L[a].lstrip().startswith('<TR'): a-=1
    b=ln-1
    while b<len(L) and '</TR>' not in L[b]: b+=1
    txt='\n'.join(L[a:b+1])
    cells=[];hit=None
    for m in CELL.finditer(txt):
        l0=a+1+txt.count('\n',0,m.start()); l1=a+1+txt.count('\n',0,m.end())
        cells.append(strip(m.group(2)))
        if l0<=ln<=l1: hit=len(cells)-1
    return a,b,cells,hit
def table_of(L,ln):
    a=ln-1
    while a>=0 and not L[a].lstrip().upper().startswith('<TABLE'): a-=1
    return a
def header_rows(L,ta,n=4):
    rows=[];i=ta+1
    while i<len(L) and len(rows)<n:
        if L[i].lstrip().startswith('<TR'):
            a,b,c,h=tr_of(L,i+1); rows.append(c); i=b
        i+=1
    return rows
def unit_of(L,ta):
    for k in range(ta,max(ta-30,0),-1):
        m=re.search(r'단위\s*[:：]\s*([^)<\s]+)',L[k])
        if m: return m.group(1),k+1
    return None,None
def num(s):
    s=s.replace(',','').strip()
    neg=(s.startswith('(') and s.endswith(')')) or s.startswith('△') or s.startswith('-')
    s=re.sub(r'[()△\-\s]','',s)
    v=float(s); return -v if neg else v
UF={'원':1e-6,'백만원':1.0,'천원':1e-3,'억원':100.0}
res=[]
def check(tag,path,part):
    L=lines(path); ln=part['line']
    a,b,cells,hit=tr_of(L,ln)
    ta=table_of(L,ln)
    label=cells[0] if cells else ''
    printed=part['printed']
    col=[hit] if (hit is not None and cells[hit]==printed) else []
    unit,uline=unit_of(L,ta)
    lab_ok=None
    if 'label' in part:
        pl=strip(re.sub(r'\s*\[.*?\]','',part['label']))
        lab_ok=(pl==label) or (pl in label) or (label in pl)
    v=num(printed)
    u=part.get('unit')
    f=UF.get(unit or u)
    ok=None
    if f is not None and 'contribution_mn' in part:
        mn=v*f
        exp=part['sign']*(abs(mn) if part.get('abs') else mn)
        ok=abs(exp-part['contribution_mn'])<1e-6
    if f is not None and 'contribution_eok' in part:
        mn=v*f
        ok=abs(mn/100.0*part['sign']-part['contribution_eok'])<1e-6
    rec=dict(tag=tag,path=path[-40:],line=ln,label=label,plan_label=part.get('label'),printed=printed,
             col=col,ncols=len(cells),unit_xml=unit,unit_plan=u,val_ok=ok,table_line=ta+1,lab_ok=lab_ok,
             header=[' | '.join(r) for r in header_rows(L,ta)][:3],tr_cells=cells)
    res.append(rec); return rec
for bk in plan['buckets']:
    path=bk['meta']['file']
    for c in bk['cells']:
        for pt in c['parts']: check(f"PL {bk['quarter']} i{c['item']}",path,pt)
for s in plan['seams']:
    pm=s.get('printed_3m')
    if pm:
        for pt in pm['parts']: check(f"SEAM {s['quarter']} i{s['item']}",pm['file'],pt)
for cb in plan['csm_buckets']:
    path=cb['file'].split(' table@')[0]
    for c in cb['cells']:
        for pt in c['parts']:
            check(f"CSM {cb['quarter']} i{c['item']}",path,pt)
with open(OUT+'v01_reread.json','w',encoding='utf-8') as f: json.dump(res,f,ensure_ascii=False,indent=1)
bad=[r for r in res if r['lab_ok'] is False or r['val_ok'] is False or len(r['col'])==0]
print('parts checked',len(res),'flagged',len(bad))
open(OUT+'v01_flagged.txt','w',encoding='utf-8').write('\n'.join(json.dumps(r,ensure_ascii=False) for r in bad))
seen=collections.OrderedDict()
for r in res:
    k=(r['path'],r['table_line'],tuple(r['col'][-1:]),r['unit_xml'])
    seen.setdefault(k,[]).append(r)
with open(OUT+'v01_tables_cols.txt','w',encoding='utf-8') as f:
    for k,v in seen.items():
        f.write(f"{k} n={len(v)} first={v[0]['tag']}\n   header: {v[0]['header']}\n   row: {v[0]['tr_cells']}\n")
print('distinct table/col',len(seen))
