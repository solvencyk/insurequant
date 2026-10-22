import io
p="data/_derived/remaining_20261022/v_oci/recompute.py"
s=io.open(p,encoding="utf-8").read()
for a,b in (('c == "CFY2025dFQA"','c in ("CFY2025dFQA","CFY2025eFQA")'),('c == "PFY2025dFQA"','c in ("PFY2025dFQA","PFY2025eFQA")'),('c == "PFY2025dFQQ"','c in ("PFY2025dFQQ","PFY2025eFQQ")'),('c == "CFY2025dHYA"','c in ("CFY2025dHYA","CFY2025eHYA")'),('c.startswith("CFY2024")','c.startswith("CFY2024")')):
    assert a in s; s=s.replace(a,b)
io.open(p,"w",encoding="utf-8").write(s)
