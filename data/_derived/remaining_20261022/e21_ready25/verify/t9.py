import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
f="data/dart/FY2023_Q1/raw/KR0001_메리츠화재해상보험/20230515002118.xml"
d=xmlrd.get(R+f)
for ti,t in enumerate(d.tables):
    labs=[r["cells"][0]["t"] for r in t["rows"] if r["cells"]]
    if any(l.startswith("재보험비용") for l in labs) and any("총 보험서비스결과" in l for l in labs):
        print("TABLE",t["start"],t["end"],len(t["rows"]))
        for rr in t["rows"]:
            print(rr["line"],[x["t"][:22] for x in rr["cells"]][:9])
