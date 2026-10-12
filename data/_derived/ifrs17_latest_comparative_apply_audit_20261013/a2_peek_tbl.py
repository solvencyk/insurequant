import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_dart import *
here = os.path.dirname(os.path.abspath(__file__))
code, fyq, rc = sys.argv[1].split(":")
idxs = [int(x) for x in sys.argv[2].split(",")]
path = find_xml(code, fyq, rc)[0]
t = load_tables(path)
out = open(here + "/a2_peek_tbl.txt", "w", encoding="utf-8")
out.write(f"{path} {len(t)} tables\n")
for i in idxs:
    tb = t[i]
    out.write(f"#### table {tb['idx']} line {tb['line']} caption={tb['caption'][:200]}\n")
    for r in tb["rows"]:
        out.write(" | ".join(r) + "\n")
