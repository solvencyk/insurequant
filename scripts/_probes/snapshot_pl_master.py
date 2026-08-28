import hashlib
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

p = "data/dart/viz/pl_breakdown_master.json"
rows = json.load(open(p, encoding="utf-8"))
print("rows:", len(rows))
print("sha256:", hashlib.sha256(open(p, "rb").read()).hexdigest())
print("company-quarters:", len({(r["원보험사코드"], r["공시분기"]) for r in rows}))
print("max int item no:", max(r["항목번호"] for r in rows if isinstance(r["항목번호"], int)))
print("non-int item no rows (e.g. 코리안리 2-1 등):", sum(1 for r in rows if not isinstance(r["항목번호"], int)))
print("non_null_values:", sum(1 for r in rows if r["값"] is not None))
