# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("artifacts/kics_validation/report_latest.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

findings = rep["findings"]
kr49_q2 = [f for f in findings if f.get("원보험사코드") == "KR0049" and f.get("공시분기") == "2026.2Q"]
print("KR0049 2026.2Q findings:", len(kr49_q2))
for f in sorted(kr49_q2, key=lambda x: x["rule"]):
    print(f"  [{f['status']:6s}] {f['rule']:28s} expected={f.get('expected')!r} actual={f.get('actual')!r} diff={f.get('diff')!r}")
    if f.get("detail"):
        print(f"           detail: {f['detail']}")
