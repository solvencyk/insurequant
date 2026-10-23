import json
d=json.load(open('PL_breakdown.json',encoding='utf-8'))
print(type(d), (list(d.keys())[:10] if isinstance(d,dict) else len(d)))
rows = d if isinstance(d,list) else d.get('rows') or d.get('data')
print(len(rows)); print(rows[0]); 
import collections
items=collections.OrderedDict()
for r in rows:
    items.setdefault((r.get('항목번호'),r.get('항목명')),0)
    items[(r.get('항목번호'),r.get('항목명'))]+=1
for k,v in items.items(): print(k,v)
print(set(k for r in rows for k in r))
