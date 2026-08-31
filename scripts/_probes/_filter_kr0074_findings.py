# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    r = json.load(f)

findings = r.get("findings", [])
mine = [f for f in findings if f.get("원보험사코드") == "KR0074" and f.get("공시분기") == "2026.2Q"]
print(f"total findings for KR0074/2026.2Q: {len(mine)}")
by_status = {}
for f in mine:
    by_status.setdefault(f.get("status"), []).append(f)
for status, items in sorted(by_status.items()):
    print(f"  {status}: {len(items)}")

print()
print("=== RED / YELLOW detail ===")
for f in mine:
    if f.get("status") in ("RED", "YELLOW"):
        print(json.dumps(f, ensure_ascii=False))

print()
print("=== full listing (rule: status) ===")
for f in sorted(mine, key=lambda x: str(x.get("rule"))):
    print(f"  {f.get('rule')}: {f.get('status')}  expected={f.get('expected')} actual={f.get('actual')}")

# structural gates
print()
print("=== structural gates involving KR0074 2026.2Q ===")
pzc = r.get("parent_zero_child_nonzero", [])
mine_pzc = [x for x in pzc if x.get("code")=="KR0074" and x.get("quarter")=="2026.2Q"]
print("parent_zero_child_nonzero:", mine_pzc)

pc = r.get("parent_present_child_incomplete") or r.get("partial_child") or {}
print("parent_present_child_incomplete keys:", list(r.keys()))
