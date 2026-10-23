import json
V='C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/'
P=json.load(open(V+'head/PL_breakdown.json',encoding='utf-8'))
o=open(V+'d06_items56.txt','w',encoding='utf-8')
for r in P:
    if r['원보험사코드']=='KR0072' and r['공시분기'][:4]=='2023' and r['항목번호'] in (3,4,5,6,7,8,9,10,11,12):
        o.write(f"{r['공시분기']} i{r['항목번호']} {r['값']} dangi={r.get('값_당분기')}\n")
