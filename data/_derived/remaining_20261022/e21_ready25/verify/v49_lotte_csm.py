import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
f=glob.glob(R+"data/dart/FY2024_Q1/raw/KR0003_롯데손해보험/20240516001888.xml")[0]
d=xmlrd.get(f)
ti,t=d.table_at_line(15846)
print("table",t["start"],t["end"],"unit",d.unit_before(t))
for r in t["rows"]:
    cs=[c["t"] for c in r["cells"]]
    print(r["line"],[x[:26] for x in cs])
seg=xmlrd.strip(d.text[max(0,t["pos"]-500):t["pos"]]); print("pre:",seg[-90:])
# original FY2023_Q1: any table mentioning CSM measurement?
g=[x for x in glob.glob(R+"data/dart/FY2023_Q1/raw/KR0003*/*.xml")+glob.glob(R+"data/dart/FY2023_Q1/raw/KR0003*/xml/*.xml") if not x.endswith("_00760.xml")]
print(g)
o=xmlrd.get(g[0]); n=0
for tt in o.tables:
    txt=" ".join(c["t"] for r in tt["rows"] for c in r["cells"])
    if re.search(r"보험계약마진",txt) and re.search(r"기초|기말",txt): n+=1; print("   orig table w/ CSM+기초/기말:",tt["start"], txt[:100])
print("orig tables mentioning 보험계약마진 with 기초/기말:",n)
