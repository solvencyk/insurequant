"""Quick automated plausibility scan across management_indicators.json -- catches residual
extraction bugs (cohort-number leakage, wrong-column reads, sign errors) before backfill."""
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / "management_indicators.json", encoding="utf-8"))

by_co_q = defaultdict(dict)
for r in d:
    by_co_q[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]

COHORT_VALS = {13, 25, 37, 49, 61, 73, 85}
flags = []

for (code, q), items in sorted(by_co_q.items()):
    # 1) 계약유지율 items (15-21) should be plausible percentages, and NOT literally the
    #    cohort-number itself (13/25/37/.../85) -- that exact match is the smoking gun for the
    #    회차-label-leak bug recurring in some other rendering variant.
    for item_no in range(15, 22):
        v = items.get(item_no)
        if v is None:
            continue
        if v in COHORT_VALS:
            flags.append(f"{code} {q} item{item_no}: SUSPICIOUS value {v} (exactly a 회차 cohort number -- possible label-leak)")
        if not (-5 <= v <= 120):
            flags.append(f"{code} {q} item{item_no}: implausible 유지율 {v} (expected roughly 0-100%)")
    # 2) 지급여력비율 (item5/6) sanity: item6(후) should be >= item5(전) in the vast majority of
    #    cases (경과조치 boosts available capital) -- not a hard rule (a few real exceptions
    #    exist) but worth flagging for review.
    v5, v6 = items.get(5), items.get(6)
    if v5 is not None and v6 is not None and v6 < v5 - 0.5:
        flags.append(f"{code} {q}: item6(후)={v6} < item5(전)={v5} -- unusual (경과조치 후 통상 >= 전)")
    # 3) balance-sheet identity: 자산(1) ~= 부채(2)+자본(3)
    v1, v2, v3 = items.get(1), items.get(2), items.get(3)
    if v1 is not None and v2 is not None and v3 is not None:
        diff = v1 - (v2 + v3)
        if abs(diff) > max(2.0, 0.005 * abs(v1)):
            flags.append(f"{code} {q}: 자산(1)={v1} != 부채(2)+자본(3)={v2+v3} diff={diff:.2f}")
    # 4) ROA/ROE sign should generally match 당기순이익 sign (loss -> negative ROA/ROE), unless
    #    company hit 자본잠식 (equity went negative, flips ROE sign) -- flag for review not hard.
    v4, v9, v10 = items.get(4), items.get(9), items.get(10)
    if v4 is not None and v9 is not None:
        if (v4 < 0) != (v9 < 0) and abs(v4) > 1 and abs(v9) > 0.05:
            flags.append(f"{code} {q}: 당기순이익(4)={v4} sign != ROA(9)={v9} sign")

print(f"buckets scanned: {len(by_co_q)}")
print(f"flags: {len(flags)}")
for f in flags:
    print(" -", f)
