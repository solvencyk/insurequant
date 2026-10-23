import json,sys
sys.stdout.reconfigure(encoding='utf-8')
R='C:/Users/sangwook.cho/Desktop/insurequant/'
d=json.load(open(R+'data/compare/panel_compare.json',encoding='utf-8'))
for m in d['metrics']:
    ks={k:(v if not isinstance(v,(list,dict)) else type(v).__name__+str(len(v))) for k,v in m.items()}
    print(json.dumps(ks,ensure_ascii=False)[:420])
m=d['metrics'][[x['id'] for x in d['metrics']].index('csm_end')] if any(x['id']=='csm_end' for x in d['metrics']) else d['metrics'][5]
for k,v in m.items():
    if isinstance(v,dict): print(k, list(v)[:5], json.dumps(list(v.values())[0],ensure_ascii=False)[:300])
