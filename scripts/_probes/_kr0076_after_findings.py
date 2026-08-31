# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

rep = json.load(open("artifacts/kics_validation/report_20260831T073539Z.json", encoding="utf-8"))
findings = rep.get("findings", [])
kr76 = [f for f in findings if f.get("원보험사코드")=="KR0076" and f.get("공시분기")=="2026.2Q"]
print(f"total rule-engine findings for KR0076 2026.2Q: {len(kr76)}")
red = [f for f in kr76 if f.get("status")=="RED"]
print(f"RED count: {len(red)}")
for f in red:
    print(f"  RED rule={f.get('rule')} detail={f.get('detail')}")
yellow = [f for f in kr76 if f.get("status")=="YELLOW"]
print(f"YELLOW count: {len(yellow)}")
for f in yellow:
    print(f"  YELLOW rule={f.get('rule')} expected={f.get('expected')!r} actual={f.get('actual')!r} diff={f.get('diff')!r}")

print()
print("=== structural gates (parent-child / continuity / absence-pin) mentioning KR0076 ===")
def scan(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            scan(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            s = json.dumps(v, ensure_ascii=False) if not isinstance(v, (dict, list)) else None
            if s and "KR0076" in s:
                print(f"{path}[{i}]: {s}")
            elif isinstance(v, (dict, list)):
                s2 = json.dumps(v, ensure_ascii=False)
                if "KR0076" in s2:
                    print(f"{path}[{i}]: {s2}")

for key in ("coverage_census", "parent_zero_child_nonzero", "parent_present_child_incomplete"):
    scan(rep.get(key), key)
