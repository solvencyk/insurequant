import json,sys; sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
pl={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
plh={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open("head/PL_breakdown.json",encoding="utf-8"))}
cs={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"CSM_waterfall.json",encoding="utf-8"))}
csh={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open("head/CSM_waterfall.json",encoding="utf-8"))}
for c,qs in (("KR0068",["2023.1Q","2023.2Q","2023.3Q"]),("KR0079",["2024.1Q","2024.2Q","2024.3Q","2023.4Q"]),("KR0104",["2023.1Q"])):
    for q in qs:
        print(c,q,"PL4 new",pl.get((c,q,4)),"old",plh.get((c,q,4)),"| CSM5 new",cs.get((c,q,5)),"old",csh.get((c,q,5)), "| ratio", None if cs.get((c,q,5)) is None or pl.get((c,q,4)) is None else round(pl[(c,q,4)]/-cs[(c,q,5)]/100,5))
