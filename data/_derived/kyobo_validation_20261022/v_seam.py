import json
cs = json.load(open("CSM_waterfall.json", encoding="utf-8"))
pl = json.load(open("PL_breakdown.json", encoding="utf-8"))
M = {(r["공시분기"], int(r["항목번호"])): (r["값"], r["값_당분기"]) for r in cs if r["원수사명"] == "교보생명보험"}
qs = ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"]
print("CSM 값 / 값_당분기 (억원)")
for q in qs:
    print(q, [M.get((q,i)) for i in range(1,7)])
    v = [M.get((q,i)) for i in range(1,7)]
    if all(x and x[1] is not None for x in v):
        q_id = v[0][1]+v[1][1]+v[2][1]+v[3][1]+v[4][1]-v[5][1]   # 기초(당분기값?) check below
print("single-quarter identity: 신계약+이자+가정+상각 = 기말-기초(분기)? using 값_당분기 of 2-5 vs close-open per quarter")
prevclose = None
for q in qs:
    v = {i: M[(q,i)] for i in range(1,7)}
    d = sum(v[i][1] for i in (2,3,4,5))
    print(q, "sum(2..5 당분기)=%.2f" % d, " 기말_cum - 기초_cum = %.2f" % (v[6][0]-v[1][0]), " 당분기 6 - 당분기 1 = %.2f / %.2f" % (v[6][1], v[1][1]))
P = {(r["공시분기"], int(r["항목번호"]) if str(r["항목번호"]).isdigit() else r["항목번호"]): (r["값"], r["값_당분기"]) for r in pl if r["원수사명"]=="교보생명보험"}
print("PL item4 (백만원) 값/당분기:")
for q in qs: print(q, P.get((q,4)), " CSM item5 억:", M.get((q,5)), " pair gap(백만)=", round(abs(P[(q,4)][0]) + M[(q,5)][0]*100, 3), " quarterly gap=", round(P[(q,4)][1] + M[(q,5)][1]*100, 3))
