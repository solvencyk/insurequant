import sys,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
for f,a,b in (("data/dart/FY2025_Q2/raw/KR0003_롯데손해보험/xml/20250814003966.xml",57600,62000),("data/dart/FY2025_Q3/raw/KR0003_롯데손해보험/xml/20251114002985.xml",31900,34400)):
    d=xmlrd.get(R+f)
    print("=====",f)
    for ti,t in enumerate(d.tables):
        if a<=t["start"]<=b:
            r0=[" ".join(c["t"] for c in r["cells"])[:90] for r in t["rows"][:2]]
            labs=[r["cells"][0]["t"][:40] for r in t["rows"] if r["cells"]]
            seg=xmlrd.strip(d.text[max(0,t["pos"]-700):t["pos"]])[-40:]
            print(t["start"],t["end"],len(t["rows"]),"| prev:",seg,"| r0:",r0[0][:70],"| labs:",labs[5:9])
