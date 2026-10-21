import sys
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml
T = read_tables(main_xml(sys.argv[1]))
kw = sys.argv[2]; only = sys.argv[3] if len(sys.argv) > 3 else ""
for t in T:
    if only and only not in t["title"].replace(" ", ""): continue
    for r in t["rows"]:
        if r["cells"] and kw in r["cells"][0].replace(" ", ""):
            print(t["line"], t["title"][:30], "|", r["line"], " | ".join(r["cells"])[:240])
