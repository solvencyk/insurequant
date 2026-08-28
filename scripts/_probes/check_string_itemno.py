import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
rows = json.load(open("data/dart/viz/pl_breakdown_master.json", encoding="utf-8"))
non_int = [r for r in rows if not isinstance(r["항목번호"], int)]
print("non-int item numbers:", len(non_int))
seen = set()
for r in non_int[:10]:
    print(r["원보험사코드"], repr(r["항목번호"]), r["항목명"])
