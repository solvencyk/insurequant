# -*- coding: utf-8 -*-
import io, json, sys
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
rs = json.loads(open(ROOT + "kics_rate_sensitivity.json", encoding="utf-8").read())
q = "2026.2Q"
rows_q = [r for r in rs if r.get("공시분기") == q]
cnt = Counter(r["원보험사코드"] for r in rows_q)
print("companies with row count != 6:", [(c, n) for c, n in cnt.items() if n != 6])
print("total distinct companies:", len(cnt), "total rows:", sum(cnt.values()))
# also check for exact-duplicate keys (원보험사코드,경과조치여부,measure구분) within the quarter
key_cnt = Counter((r["원보험사코드"], r["경과조치여부"], r["measure구분"]) for r in rows_q)
dupes = [(k, n) for k, n in key_cnt.items() if n != 1]
print("duplicate (code,phase,measure) keys:", dupes)
