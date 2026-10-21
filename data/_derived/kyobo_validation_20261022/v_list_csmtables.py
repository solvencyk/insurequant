import sys
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml
for fy in sys.argv[1:]:
    T = read_tables(main_xml(fy))
    print("==", fy)
    for t in T:
        if "5.재무제표주석" not in t["title"].replace(" ", ""): continue
        hdr = " ".join(c for r in t["rows"][:4] for c in r["cells"]).replace(" ", "")
        if "보험계약마진" in hdr and "미래현금흐름" in hdr:
            labs = [r["cells"][0] for r in t["rows"] if r["cells"]]
            op = next((r for r in t["rows"] if r["cells"] and r["cells"][0].replace(" ","").startswith("1.기초")), None)
            cl = next((r for r in t["rows"] if r["cells"] and r["cells"][0].replace(" ","").startswith("8.기말")), None)
            print(t["line"], len(t["rows"]), "labels0:", labs[3][:30] if len(labs)>3 else "", "| open:", op["cells"][1:] if op else None, "| close:", cl["cells"][1:] if cl else None)
