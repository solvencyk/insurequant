import json
pl=json.load(open('PL_breakdown.json',encoding='utf-8'))
print(len(pl), pl[0].keys())
qs=["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"]
rows=[r for r in pl if r['원수사명']=='교보생명보험' and r['공시분기'] in qs]
items={}
for r in rows:
    items.setdefault((r.get('항목번호',r.get('항목')),r['항목명']),{})[r['공시분기']]=(r['값'],r.get('값_당분기'))
for k in sorted(items, key=lambda x: str(x[0])):
    if str(k[0]) in ('1','4','17','19','20','22','23','24','25','31'):
        print(k,{q:items[k].get(q) for q in qs})
c=json.load(open('CSM_waterfall.json',encoding='utf-8'))
print(len(c), c[0])
