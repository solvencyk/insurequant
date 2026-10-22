import sys,re,glob; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
f=glob.glob(R+"data/dart/FY2024_Q2/raw/KR0068_한화생명/*.xml")[0]
d=xmlrd.get(f); print(f.split("/")[-1])
ti,t,row,c=xmlrd.row_at_line(d,80447)
bt=[txt for pos,l,txt in reversed([x for x in d.titles if x[0]<t["pos"]]) if "재무제표" in txt][0]
print("table",t["start"],"section",bt,"unit",d.unit_before(t))
print("row:",[x["t"] for x in row["cells"]])
for r in t["rows"][:6]: print(r["line"],[x["t"][:16] for x in r["cells"]])
seg=xmlrd.strip(d.text[max(0,t["pos"]-500):t["pos"]]); print("pre:",seg[-120:])
