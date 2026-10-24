import sys; sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent")
from w02_lib import *
sys.stdout.reconfigure(encoding="utf-8")
fq=sys.argv[1]; code=sys.argv[2]; pat=sys.argv[3]
p=raw_path(fq,code); print(p)
for t in read_tables(p):
    flat=" ".join(" ".join(r["cells"]) for r in t["rows"])
    if re.search(pat,flat):
        print("=== table line",t["line"],"rows",len(t["rows"]))
        for r in t["rows"][:int(sys.argv[4]) if len(sys.argv)>4 else 80]:
            print(r["line"],"|".join(r["cells"]))
