"""Read-only: YTD monotonicity of the CSM waterfall flows (item 2 new business, 3 accretion, 5 amortisation): |YTD| must not shrink inside a fiscal year.
A shrink is a candidate for 3-month-as-cumulative in the CSM master."""
import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
rows = json.load(open(R + "CSM_waterfall.json", encoding="utf-8"))
s, nm = defaultdict(dict), {}
for r in rows:
    nm[r["원보험사코드"]] = r["원수사명"]
    if r["값"] is not None:
        s[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
n = 0
for (code, item), d in sorted(s.items()):
    if item not in (2, 3, 5):
        continue
    for y in (2023, 2024, 2025, 2026):
        qs = [f"{y}.{k}Q" for k in (1, 2, 3, 4)]
        for a, b in zip(qs, qs[1:]):
            if a in d and b in d and abs(d[a]) >= 5:
                if (d[a] > 0) == (d[b] > 0) and abs(d[b]) < abs(d[a]) * 0.97 - 0.5:
                    n += 1
                    print(code, nm[code], item, a, d[a], "->", b, d[b], f"ratio {d[b]/d[a]:.3f}")
print("flags", n)
