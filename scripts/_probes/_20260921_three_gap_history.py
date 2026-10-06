# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
rs = json.loads(open(ROOT + "kics_rate_sensitivity.json", encoding="utf-8").read())

for code in ("KR0050", "KR0069", "KR1098"):
    print(f"=== {code} — all quarters/phases in master ===")
    recs = [r for r in rs if r.get("원보험사코드") == code]
    by_q = {}
    for r in recs:
        by_q.setdefault(r["공시분기"], set()).add(r["경과조치여부"])
    for q in sorted(by_q):
        print(f"  {q}: phases={sorted(by_q[q])}")
    print()
