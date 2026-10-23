import json
V='C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/'
H=V+'verify_kr0072_kdb/head/'
out=open(V+'verify_kr0072_kdb/g01_gold.txt','w',encoding='utf-8')
plan=json.load(open(V+'kr0072_kdb/e23_plan_kdb_final.json',encoding='utf-8'))
out.write('csm_gold_class: '+json.dumps(plan['csm_gold_class'],ensure_ascii=False,indent=1)+'\n')
ap=plan['apply_contract']
for k in ['gold_replace','csm_gold_replace','csm_gold_remove']:
    out.write(k+': '+json.dumps([ (e['item'],e['quarter'],e.get('value'),e.get('was')) if isinstance(e,dict) else e for e in ap[k]],ensure_ascii=False)+'\n')
for n in ['user_pl_cells','user_csm_cells']:
    g=json.load(open(H+n+'.json',encoding='utf-8'))
    for e in g['set']:
        if e.get('원보험사코드')=='KR0072':
            out.write(n+' '+json.dumps({k:(v if k!='note' else v[:500]) for k,v in e.items()},ensure_ascii=False)+'\n')
