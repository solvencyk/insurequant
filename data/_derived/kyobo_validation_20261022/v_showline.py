import sys
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml
T = read_tables(main_xml(sys.argv[1]))
lo, hi = int(sys.argv[2]), int(sys.argv[3])
for t in T:
    if lo <= t["line"] <= hi:
        print("TABLE", t["line"], t["title"])
        for r in t["rows"]:
            print(r["line"], " | ".join(r["cells"])[:300])
