import sys,re,glob,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"; HERE=R+"data/_derived/remaining_20261022/e21_ready25/verify/"
m={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r["값"] for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
H=json.load(open("v30_headline.json",encoding="utf-8"))
for q in ("2024.1Q","2024.2Q","2024.3Q"):
    rec=H[f"KR0104|{q}"]; print(q,rec["file"],"table",rec["table"],"unit",rec["unit"])
    for it in ("1","17","20","22","24"):
        v=rec["items"].get(it)
        print("   item",it,"printed prior cum",None if not v else round(v["pricum"],6),"master",m.get(("KR0104",q,int(it))))
    print("   master item21",m.get(("KR0104",q,21)),"item18",m.get(("KR0104",q,18)),"item19",m.get(("KR0104",q,19)))
# find the 영업외손익 & lines in the FY2025_Q1 file
fs=[x for x in glob.glob(R+"data/dart/FY2025_Q1/raw/KR0104*/*.xml")+glob.glob(R+"data/dart/FY2025_Q1/raw/KR0104*/xml/*.xml") if not x.endswith("_00760.xml")]
d=xmlrd.get(fs[0]); rec=H["KR0104|2024.1Q"]
t=[t for t in d.tables if t["start"]==rec["table"]][0]
for r in t["rows"]:
    cs=[c["t"] for c in r["cells"]]
    if cs and re.search(r"^(영업외|투자손익|영업이익|법인세차감전|기타포괄)",re.sub(r"\s+","",cs[0])): print("  ",r["line"],cs[0],cs[1:])
