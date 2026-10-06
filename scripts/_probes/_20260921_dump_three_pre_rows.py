# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
rs = json.loads(open(ROOT + "kics_rate_sensitivity.json", encoding="utf-8").read())
for code in ("KR0050", "KR0069", "KR1098"):
    print(f"=== {code} 2026.2Q 적용전 rows (exact JSON) ===")
    for r in rs:
        if r.get("원보험사코드") == code and r.get("공시분기") == "2026.2Q":
            print(json.dumps(r, ensure_ascii=False))
