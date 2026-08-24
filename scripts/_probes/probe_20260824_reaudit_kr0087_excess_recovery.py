# -*- coding: utf-8 -*-
"""Read-only: for KR0087 (and any company), test the 'tier2 excess recovery' reading.

excess_pre  = (debt_pre_precap) - limit
where debt_post_recognised = item51_post - item49_post  and
      debt_pre_precap      = debt_post_recognised + item53(신종) + item54(후순위)
Cross-check against the headline bridge requirement:
      required_excess = item2 - (item4 - item12 - item13)
"""
import json, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

CODES = sys.argv[1].split(",")

def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

by = {}
for r in recs:
    if r.get("원보험사코드") not in CODES:
        continue
    k = (r["원보험사코드"], r["공시분기"])
    by.setdefault(k, {})[str(r["항목번호"])] = (f(r.get("값")), f(r.get("값_적용후")))

hdr = ("q", "i2", "i4", "i12", "i13", "req_exc", "i47", "i48", "i51", "i49", "i53", "i54",
       "i51post", "i49post", "debt_post", "debt_pre", "exc_tfi")
print(" | ".join(f"{h:>10}" for h in hdr))
for k in sorted(by):
    d = by[k]
    g = lambda i, j=0: (d.get(i) or (None, None))[j]
    i2, i4, i12, i13 = g("2"), g("4"), g("12"), g("13")
    req = None
    if None not in (i2, i4, i12, i13):
        req = i2 - (i4 - i12 - i13)
    i47, i48, i51, i49 = g("47"), g("48"), g("51"), g("49")
    i53, i54 = g("53"), g("54")
    i51p, i49p = g("51", 1), g("49", 1)
    debt_post = (i51p - i49p) if None not in (i51p, i49p) else None
    grand = (i53 or 0) + (i54 or 0)
    debt_pre = (debt_post + grand) if debt_post is not None else None
    exc = (debt_pre - i48) if (debt_pre is not None and i48 is not None) else None
    row = [k[1], i2, i4, i12, i13, req, i47, i48, i51, i49, i53, i54, i51p, i49p,
           debt_post, debt_pre, exc]
    print(" | ".join(f"{('' if v is None else (v if isinstance(v,str) else round(v,2)))!s:>10}" for v in row))
