import hashlib
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

p = sys.argv[1] if len(sys.argv) > 1 else "PL_breakdown.json"
rows = json.load(open(p, encoding="utf-8"))
print("path:", p)
print("rows:", len(rows))
print("sha256:", hashlib.sha256(open(p, "rb").read()).hexdigest())
print("company-quarters:", len({(r["원보험사코드"], r["공시분기"]) for r in rows}))
print("max int item no:", max(r["항목번호"] for r in rows if isinstance(r["항목번호"], int)))
print("non_null 값:", sum(1 for r in rows if r["값"] is not None))
print("non_null 값_당분기:", sum(1 for r in rows if r.get("값_당분기") is not None))
