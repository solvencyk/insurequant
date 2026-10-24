import sys,re
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent")
from w02_lib import *
sys.stdout.reconfigure(encoding="utf-8")
fq=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3]); pat=sys.argv[4] if len(sys.argv)>4 else "."
p=raw_path(fq,"KR0087")
for t in read_tables(p):
    if t["line"]<=b and t["rows"] and t["rows"][-1]["line"]>=a:
        print("=== table",t["line"],len(t["rows"]))
        for r in t["rows"]:
            j="|".join(r["cells"])
            if re.search(pat,j) : print(" ",r["line"],j[:260])
