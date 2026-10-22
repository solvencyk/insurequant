p="v12_lotte_split.py"
s=open(p,encoding="utf-8").read()
s=s.replace('''    csm = val(T[0], "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    ra = val(T[0], "비금융위험에 대한 위험조정의 변동분")
    rev_exp = val(T[0], "보고기간에 발생한 보험서비스비용")
    cost_act = val(T[3], "발생한 보험금 및 그 밖의")
    re_rev_act = val(T[4], "발생보험금 및 기타재보험수익")
    re_csm = val(T[5], "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    re_ra = val(T[5], "비금융위험에 대한 위험조정의 변동분")
    re_exp = val(T[5], "보고기간에 발생한 보험서비스비용")''','''    if q == "2024.2Q":
        L = dict(csm="서비스의 이전으로 당기손익에 인식한 보험계약마진", ra="비금융위험에 대한 위험조정의 변동분", rev_exp="보고기간에 발생한 보험서비스비용",
                 cost_act="발생한 보험금 및 그 밖의", re_rev="발생보험금 및 기타재보험수익", re_exp="보고기간에 발생한 보험서비스비용")
    else:
        L = dict(csm="보험계약마진 상각", ra="위험조정 변동", rev_exp="예상보험금 및 예상기타보험서비스비용",
                 cost_act="발생보험금 및 기타서비스비용", re_rev="발생보험금 및 기타재보험수익", re_exp="회수예상 보험금 및 기타보험서비스비용")
    csm = val(T[0], L["csm"]); ra = val(T[0], L["ra"]); rev_exp = val(T[0], L["rev_exp"])
    cost_act = val(T[3], L["cost_act"]); re_rev_act = val(T[4], L["re_rev"])
    re_csm = val(T[5], L["csm"]); re_ra = val(T[5], L["ra"]); re_exp = val(T[5], L["re_exp"])''')
open(p,"w",encoding="utf-8").write(s)
