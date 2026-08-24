# -*- coding: utf-8 -*-
"""Read-only: verify the claim in my inbox answer -- that item51_post (TFI table's own
보완자본, POST column) reconciles with the master's existing item3 (headline 보완자본) for
all 7 Korean Re quarters, and that item2(bridge)'s residual at 2024.4Q matches item14*5%
(the pattern validation flagged in iter-2 sec 3-D). 2026-08-22."""
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
recs = data if isinstance(data, list) else data["records"]

by_bucket = {}
for r in recs:
    if r["원보험사코드"] != "KR1000":
        continue
    by_bucket.setdefault(r["공시분기"], {})[int(r["항목번호"])] = (r.get("값"), r.get("값_적용후"))

for q in sorted(by_bucket):
    b = by_bucket[q]
    if 50 not in b or 51 not in b:
        continue
    i3 = float(b.get(3, (None, None))[0]) if b.get(3, (None,))[0] else None
    i51_post = float(b[51][1]) if b[51][1] else None
    i2 = float(b.get(2, (None,))[0]) if b.get(2, (None,))[0] else None
    i4 = float(b.get(4, (None,))[0]) if b.get(4, (None,))[0] else None
    i12 = float(b.get(12, (None,))[0]) if b.get(12, (None,))[0] else None
    i13 = float(b.get(13, (None,))[0]) if b.get(13, (None,))[0] else None
    i47 = float(b.get(47, (None,))[0]) if b.get(47, (None,))[0] else None
    i48 = float(b.get(48, (None,))[0]) if b.get(48, (None,))[0] else None
    i49 = float(b.get(49, (None,))[0]) if b.get(49, (None,))[0] else None
    diff3 = None if (i3 is None or i51_post is None) else i3 - i51_post
    capped = None if None in (i47, i48, i49) else min(i47, i48) + i49
    diff_capped = None if (capped is None or i51_post is None) else i51_post - capped
    print(f"{q}: item3={i3} item51_post={i51_post} diff(item3-item51_post)={diff3}  "
          f"min(47,48)+49={capped} vs item51_post diff={diff_capped}")
    if i2 is not None and i4 is not None and i12 is not None and i13 is not None and i47 is not None and i48 is not None:
        exc = max(0.0, i47 - i48)
        exc_clamped = min(exc, i12) if i12 else exc
        bridge_expected = i4 - (i12 - exc_clamped) - i13
        print(f"    bridge: item2={i2} expected(with tier2 exc, clamped)={bridge_expected:.2f} diff={i2-bridge_expected:.2f}")
