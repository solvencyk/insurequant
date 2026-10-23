import json
R='C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/'
p=json.load(open(R+'kr0072_kdb_load2/e23_plan_kdb_final.json',encoding='utf-8'))
out=open(R+'verify_kr0072_kdb_loaded/s02_plan_peek.txt','w',encoding='utf-8')
print(list(p.keys()),file=out)
for b in p['buckets']:
    print('BUCKET',b['quarter'],b['kind'],b['meta'],file=out)
    for c in b['cells']:
        print(json.dumps(c,ensure_ascii=False)[:700],file=out)
for cb in p['csm_buckets']:
    print('CSMBUCKET',cb['quarter'],{k:v for k,v in cb.items() if k!='cells'},file=out)
    for c in cb['cells']:
        print(json.dumps(c,ensure_ascii=False)[:700],file=out)
print(json.dumps(p['apply_contract'],ensure_ascii=False)[:6000],file=out)
