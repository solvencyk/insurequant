import sys,re,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
for f,ln in (("data/dart/FY2025_Q3/raw/KR0003_롯데손해보험/xml/20251114002985.xml",32162),("data/dart/FY2025_Q2/raw/KR0003_롯데손해보험/xml/20250814003966.xml",58268)):
    d=xmlrd.get(R+f)
    ti,t,row,c=xmlrd.row_at_line(d,ln)
    print(f,t["start"],t["end"])
    for rr in t["rows"][:10]: print(rr["line"],[(x["t"][:40],x["span"]) for x in rr["cells"]])
    print("row:",[x["t"][:30] for x in row["cells"]])
    # texts in P before table
    seg=d.text[max(0,t["pos"]-4000):t["pos"]]
    print([xmlrd.strip(m.group(1))[:80] for m in re.finditer(r"<P[^>]*>(.*?)</P>",seg,re.S)][-8:])
