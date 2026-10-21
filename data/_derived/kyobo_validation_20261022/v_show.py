import sys
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml
T = read_tables(main_xml(sys.argv[1]))
t = [x for x in T if x["line"] == int(sys.argv[2])][0]
for r in t["rows"]:
    print(r["line"], " | ".join(r["cells"]))
