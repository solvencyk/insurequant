import sys; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd, time
t0=time.time()
d=xmlrd.get("C:/Users/sangwook.cho/Desktop/insurequant/data/dart/FY2024_Q1/raw/KR0104_농협생명보험/20240514001371.xml")
print(time.time()-t0, len(d.tables), len(d.titles))

r=xmlrd.row_at_line(d,5657)
ti,t,row,c=r
print(ti,t["start"],t["end"],[c["t"] for c in row["cells"]], d.title_before(t["pos"]), d.unit_before(t))
for rr in t["rows"][:8]: print(rr["line"],[c["t"] for c in rr["cells"]])
