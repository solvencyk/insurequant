import sys,re,json,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
f=glob.glob(R+"data/dart/FY2025_Q1/raw/KR0010_KB손해보험/*.xml")[0]
print(f)
d=xmlrd.get(f)
ti,t=d.table_at_line(36148)
print(t["start"],t["end"],len(t["rows"]))
for rr in t["rows"]:
    print(rr["line"],[x["t"][:18] for x in rr["cells"]])
# preceding caption
seg=d.text[max(0,t["pos"]-3000):t["pos"]]
print([xmlrd.strip(m.group(1))[:100] for m in re.finditer(r"<P[^>]*>(.*?)</P>",seg,re.S)][-4:])
