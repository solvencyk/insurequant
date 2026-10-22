import json,sys,glob,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
m={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
h={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(HERE+"head/PL_breakdown.json",encoding="utf-8"))}
print("KB 2023.4Q items 24-32  HEAD -> NEW")
for i in range(24,33): print("  ",i,h.get(("KR0010","2023.4Q",i)),"->",m.get(("KR0010","2023.4Q",i)))
f=R+"data/dart/FY2024_Q4/raw/KR0010_KB손해보험_20250314001697/20250314001697.xml"
d=xmlrd.get(f)
ti,t=d.table_at_line(46223)
print("table",t["start"],t["end"],"unit",d.unit_before(t))
for r in t["rows"]:
    cs=[c["t"] for c in r["cells"]]
    if r["line"]>=46100 or True:
        lab=cs[0] if cs else ""
        if re.search(r"포괄|OCI|금융|평가|재측정|지분|파생|환산|세후|당기순|총포괄",lab):
            print(r["line"],lab[:40],"|",cs[1:])
