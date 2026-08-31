# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BEFORE = "artifacts/kics_validation/report_20260831T073827Z.json"
AFTER = "artifacts/kics_validation/report_20260831T075107Z.json"

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

b = load(BEFORE)
a = load(AFTER)

b_red = [f for f in b["findings"] if f["status"] == "RED"]
a_red = [f for f in a["findings"] if f["status"] == "RED"]
print(f"BEFORE total RED (whole dataset): {len(b_red)}")
print(f"AFTER  total RED (whole dataset): {len(a_red)}")

b_red_other = [f for f in b_red if not (f.get("원보험사코드")=="KR0010" and f.get("공시분기")=="2026.2Q")]
a_red_other = [f for f in a_red if not (f.get("원보험사코드")=="KR0010" and f.get("공시분기")=="2026.2Q")]
print(f"BEFORE RED excluding KR0010 2026.2Q: {len(b_red_other)}")
print(f"AFTER  RED excluding KR0010 2026.2Q: {len(a_red_other)}")
print("identical set (no other-company regressions)?", 
      sorted((f["rule"],f.get("원보험사코드"),f.get("공시분기")) for f in b_red_other) ==
      sorted((f["rule"],f.get("원보험사코드"),f.get("공시분기")) for f in a_red_other))

print(f"\nKR0010 2026.2Q RED before: {len([f for f in b_red if f.get('원보험사코드')=='KR0010' and f.get('공시분기')=='2026.2Q'])}")
print(f"KR0010 2026.2Q RED after:  {len([f for f in a_red if f.get('원보험사코드')=='KR0010' and f.get('공시분기')=='2026.2Q'])}")

# structural gates (coverage census / parent-child) for KR0010
for tag in ("coverage_census","parent_zero_child_nonzero","parent_present_child_incomplete"):
    bv = b.get(tag)
    av = a.get(tag)
    print(f"\n--- {tag} ---")
    if isinstance(bv, dict) and "missing_count" in bv:
        print("before missing_count:", bv["missing_count"], "after:", av["missing_count"])
    else:
        bmatches = [x for x in (bv or []) if "KR0010" in json.dumps(x, ensure_ascii=False)]
        amatches = [x for x in (av or []) if "KR0010" in json.dumps(x, ensure_ascii=False)]
        print("KR0010 mentions before:", bmatches)
        print("KR0010 mentions after:", amatches)
