import json, re, glob
ROOT='C:/Users/sangwook.cho/Desktop/insurequant/'
OUT=ROOT+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/'
res=json.load(open(OUT+'v01_reread.json',encoding='utf-8'))
plan=json.load(open(ROOT+'data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/e23_plan_kdb_final.json',encoding='utf-8'))
files=set()
for b in plan['buckets']: files.add(b['meta']['file'])
for cb in plan['csm_buckets']: files.add(cb['file'].split(' table@')[0])
def full(p):
    c=[f for f in files if f.endswith(p)]
    return c[0]
seen={}
for r in res: seen.setdefault((r['path'],r['table_line']),r)
def strip(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',s)).strip()
out=open(OUT+'v02_titles.txt','w',encoding='utf-8')
for (p,t),r in seen.items():
    fp=full(p)
    L=open(ROOT+fp,encoding='utf-8',errors='replace').read().split('\n')
    out.write(f'=== {fp[-50:]} table@{t}\n')
    k=t-1; got=[]
    while k>0 and len(got)<6:
        s=strip(L[k])
        if s: got.append(f'L{k+1}: {s[:120]}')
        k-=1
    out.write('\n'.join(reversed(got))+'\n')
