import sys,re; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R="C:/Users/sangwook.cho/Desktop/insurequant/"
d=xmlrd.get(R+"data/dart/FY2024_Q1/raw/KR0068_한화생명/20240514000837.xml")
ti,t=d.table_at_line(77453)
print(t["start"], d.unit_before(t))
seg=d.text[max(0,t["pos"]-2500):t["pos"]]
print([xmlrd.strip(m.group(1))[:80] for m in re.finditer(r"<P[^>]*>(.*?)</P>",seg,re.S)][-6:])
print(re.findall(r"단위[^<]{0,20}",seg))
# any '단위' within the first 5 rows
print([c["t"] for r in t["rows"][:3] for c in r["cells"]][:10])
# the 'current' note table before it: its unit
tp=d.tables[ti-1]
print(tp["start"], d.unit_before(tp), [c["t"] for r in tp["rows"][:2] for c in r["cells"]][:8])
# find the (단위 : 백만원) occurrences before this table at distance
txt=xmlrd.strip(d.text[max(0,t["pos"]-20000):t["pos"]])
for m in re.finditer(r"\(단위[^)]*\)",txt): print(m.group(0), txt[max(0,m.start()-30):m.start()])
