import json
R='C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/'
with open(R+'e23_plan_kdb_final.json',encoding='utf-8') as f: p=json.load(f)
print(list(p.keys()))
for k,v in p.items():
    if isinstance(v,list): print(k,'list',len(v), (list(v[0].keys()) if v and isinstance(v[0],dict) else v[:2]))
    elif isinstance(v,dict): print(k,'dict',list(v.keys())[:12])
b=p['buckets'][0]; print(list(b.keys()), b['meta'])
for b in p['buckets']: print(b['quarter'],b['kind'],len(b['cells']),b['meta']['file'][-30:])
