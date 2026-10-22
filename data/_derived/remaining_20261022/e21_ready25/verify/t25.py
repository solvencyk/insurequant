import sys,re,json,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2025_Q1/raw/KR0079_미래에셋생명/20250515001717.xml")
cnt=0
for ti,t in enumerate(d.tables):
    for r in t["rows"]:
        cs=[c["t"] for c in r["cells"]]
        if cs and re.search(r"상각|보험계약마진", cs[0]) and any(re.search(r"\(?50[,.]?7\d\d",x) for x in cs):
            print(t["start"],r["line"],cs[:12]); cnt+=1
print(cnt)
# print the CSM-related table heads
for ti,t in enumerate(d.tables):
    if t["start"]>46000 and t["start"]<62000:
        labs=[r["cells"][0]["t"][:20] for r in t["rows"] if r["cells"]]
        if any("보험계약마진" in l for l in labs):
            print("T",t["start"],t["end"],len(t["rows"]),labs[:6],d.unit_before(t))
