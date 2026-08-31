# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

rep = json.load(open("artifacts/kics_validation/report_20260831T072536Z.json", encoding="utf-8"))
findings = rep.get("findings", [])
kr76 = [f for f in findings if f.get("원보험사코드")=="KR0076" and f.get("공시분기")=="2026.2Q"]
print(f"total findings for KR0076 2026.2Q: {len(kr76)}")
for f in sorted(kr76, key=lambda f: str(f.get("rule"))):
    print(f"  rule={f.get('rule'):16s} status={f.get('status'):6s} expected={f.get('expected')!r} actual={f.get('actual')!r} diff={f.get('diff')!r}")
    if f.get("status") == "RED":
        print(f"    detail: {f.get('detail')}")
