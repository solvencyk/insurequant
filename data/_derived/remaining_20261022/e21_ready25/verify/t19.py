import sys,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2024_Q1/raw/KR0104_농협생명보험/20240514001371.xml")
ti,t=d.table_at_line(5657)
m={(r["항목번호"]):r["값"] for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8")) if r["원보험사코드"]=="KR0104" and r["공시분기"]=="2023.1Q"}
print({k:m[k] for k in sorted(m)})
for rr in t["rows"]:
    cs=[c["t"] for c in rr["cells"]]
    if len(cs)>=5 and cs[0]:
        print(rr["line"],cs[0][:40],"|",cs[-1])
