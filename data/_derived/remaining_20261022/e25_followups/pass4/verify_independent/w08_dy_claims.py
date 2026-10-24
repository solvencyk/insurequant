import sys,re
sys.path.insert(0,"C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent")
from w02_lib import *
sys.stdout.reconfigure(encoding="utf-8")
for fq in sys.argv[1:]:
    p=raw_path(fq,"KR0087"); print("##",fq,p.split("raw")[-1])
    for t in read_tables(p):
        for r in t["rows"]:
            j="|".join(r["cells"])
            if re.search(r"예상.{0,12}(보험금|청구|발생)|실제.{0,12}(보험금|청구|발생)|예실차|예상과 실제",j) and re.search(r"[\d]",j):
                print("  t%d L%d %s"%(t["line"],r["line"],j[:200]))
