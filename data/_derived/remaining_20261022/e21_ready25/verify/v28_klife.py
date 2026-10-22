import sys,json,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
m={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
f=R+"data/dart/FY2024_Q1/raw/KR0099_케이비라이프생명보험/xml/20240516001445.xml"
d=xmlrd.get(f)
ti,t=d.table_at_line(25521)
print("table",t["start"],t["end"],"unit",d.unit_before(t))
print("hdr:",[ [c["t"][:14] for c in r["cells"]] for r in t["rows"][:3]])
for r in t["rows"]:
    cs=[c["t"] for c in r["cells"]]
    if cs and re.search(r"^(보험영업수익|재보험영업수익|보험영업비용|재보험영업비용|총|기타사업비용|보험영업손익)",cs[0].replace(" ","")): print(r["line"],cs[0][:24],"|",cs[1:7])
print({i:m.get(("KR0099","2024.1Q",i)) for i in (1,2,3,8,12,13,14)})
bt=[txt for pos,l,txt in reversed([x for x in d.titles if x[0]<t["pos"]]) if "재무제표" in txt][0]; print("section",bt)
# other KB라이프 buckets: is there any with negative re-revenue? list item8 and 12 over quarters
for q in ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q","2025.1Q","2025.2Q","2025.3Q","2025.4Q"]:
    print(q,{i:m.get(("KR0099",q,i)) for i in (1,2,3,8,12)})
