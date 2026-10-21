import sys
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml
T = read_tables(main_xml(sys.argv[1]))
for t in T:
    if "5.재무제표주석" not in t["title"].replace(" ", ""): continue
    hdr = " ".join(c for r in t["rows"][:4] for c in r["cells"]).replace(" ", "")
    if "보험계약마진" in hdr and "손실요소" in hdr:
        print(t["line"], len(t["rows"]), "|", " / ".join(t["rows"][0]["cells"])[:200], "|", [r["cells"][0][:20] for r in t["rows"][:14] if r["cells"]])
