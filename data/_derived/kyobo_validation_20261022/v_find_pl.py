import sys
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml
f = main_xml(sys.argv[1])
T = read_tables(f)
print(f, len(T))
for k, t in enumerate(T):
    txt = " ".join(c for r in t["rows"] for c in r["cells"]).replace(" ", "")
    if "보험서비스결과" in txt and "법인세" in txt and "당기순이익" in txt:
        print(k, t["line"], t["title"][:60], len(t["rows"]), t["rows"][0]["cells"][:6])
