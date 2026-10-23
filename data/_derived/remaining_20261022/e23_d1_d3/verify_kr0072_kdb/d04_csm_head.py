import json
H='C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb/head/'
rows=json.load(open(H+'CSM_waterfall.json',encoding='utf-8'))
out=open(H.replace('head/','d04_csm_head.txt'),'w',encoding='utf-8')
for r in rows:
    if r['원보험사코드']=='KR0072' and r['공시분기'][:4] in ('2023','2024'):
        out.write(f"{r['공시분기']} {r['항목번호']} {r['항목명']} {r['값']} {r.get('값_당분기')}\n")
pl=json.load(open(H+'PL_breakdown.json',encoding='utf-8'))
out.write('---PL keys sample\n')
ks=set()
for r in pl:
    if r['원보험사코드']=='KR0072': ks.add((r['항목번호'],r['항목명']))
out.write(str(sorted(ks))+'\n')
