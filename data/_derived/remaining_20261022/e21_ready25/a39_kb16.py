"""a39: KB 2024.4Q item 16 history (READ-ONLY)"""
import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_plan_lib as P
import e21_read as R
sys.stdout.reconfigure(encoding="utf-8")
pl = P.head_json("PL_breakdown.json")
for r in pl:
    if r["원보험사코드"] == "KR0010" and r["항목번호"] == 16:
        print(r["공시분기"], r["값"], r.get("값_당분기"))
st = R.Stmt("KR0010", "FY2025_Q4")
v = R.read_vector(st, "prior", "cum")
print("FY2025_Q4 prior item16:", [(p.label, p.line, p.printed) for p in v[16]["parts"]], sum(p.sign * p.val_mn for p in v[16]["parts"]))
v = R.read_vector(st, "cur", "cum")
print("FY2025_Q4 cur item16:", [(p.label, p.line, p.printed) for p in v[16]["parts"]], sum(p.sign * p.val_mn for p in v[16]["parts"]))
