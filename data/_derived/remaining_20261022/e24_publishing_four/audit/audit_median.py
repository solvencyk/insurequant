import json,sys,statistics
sys.stdout.reconfigure(encoding='utf-8')
R='C:/Users/sangwook.cho/Desktop/insurequant/'
b=json.load(open(R+'data/compare/panel_compare.json',encoding='utf-8'))
print(b['meta']['median_rule'])
m=[x for x in b['metrics'] if x['id']=='nb_multiple'][0]
print({k:(v if not isinstance(v,(list,dict)) else '..') for k,v in m.items() if k not in('note','defn')})
print('med keys',list(m['med']),'na',m.get('na'))
co={c['code']:c for c in b['companies']}
print({k:v for k,v in list(co.items())[:2]})
qs=b['meta']['quarters']
for key,arr in m['med'].items(): print(key,arr)
for typ in ('생보','손보'):
    pop=[c for c,x in co.items() if x['type']==typ and not x.get('sector') ]
    out=[]
    for i,q in enumerate(qs):
        vs=[m['v'][c][i] for c in pop if c in m['v'] and m['v'][c][i] is not None]
        out.append(round(statistics.median(vs),1) if vs else None)
    print(typ,len(pop),out)
