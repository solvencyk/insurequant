import sys
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml
T = read_tables(main_xml(sys.argv[1]))
kw = sys.argv[2]
for k, t in enumerate(T):
    txt = " ".join(c for r in t["rows"] for c in r["cells"]).replace(" ", "")
    if kw in txt:
        print(k, t["line"], t["title"][:50], len(t["rows"]), "|", " / ".join(t["rows"][0]["cells"][:5])[:100], "|", " / ".join(t["rows"][min(1,len(t['rows'])-1)]["cells"][:5])[:100])
