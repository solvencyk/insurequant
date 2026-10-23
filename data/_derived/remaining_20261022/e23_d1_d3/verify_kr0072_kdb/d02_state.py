import json
R='C:/Users/sangwook.cho/Desktop/insurequant/'
def load(p):
    with open(R+p,encoding='utf-8') as f: return json.load(f)
pl=load('PL_breakdown.json'); csm=load('CSM_waterfall.json')
for name,rows,items in [('PL',pl,[4,7,12,16,21,22,23,24]),('CSM',csm,[1,4,5,6])]:
    print(name)
    for r in rows:
        if r['원보험사코드']=='KR0072' and r['공시분기'].startswith('2023') and r['항목번호'] in items:
            print(r['공시분기'],r['항목번호'],r['항목명'],r['값'],r.get('값_당분기'))
