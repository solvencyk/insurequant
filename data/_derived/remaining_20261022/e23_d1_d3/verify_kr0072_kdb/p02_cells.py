import json, collections
R='C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/'
with open(R+'e23_plan_kdb_final.json',encoding='utf-8') as f: p=json.load(f)
out=open(R.replace('kr0072_kdb','verify_kr0072_kdb')+'p02_cells.txt','w',encoding='utf-8')
kinds=collections.Counter()
for b in p['buckets']:
    for c in b['cells']:
        kinds[(c['kind'],c['formula'][:30])]+=1
        out.write(json.dumps({k:c[k] for k in ['quarter','item','item_name','old','new','kind','formula','operands','cls','gold_cell','source_unit']},ensure_ascii=False)+'\n')
        for pt in c['parts']: out.write('    '+json.dumps(pt,ensure_ascii=False)+'\n')
out.write(str(kinds)+'\n')
out.write(json.dumps(p['apply_contract'],ensure_ascii=False)[:4000]+'\n')
out.write(json.dumps(p['csm_buckets'][0],ensure_ascii=False)[:3000]+'\n')
out.write(json.dumps(p['seams'][0],ensure_ascii=False)+'\n')
