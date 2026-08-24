# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from solvency.validation import kics_json_rules as K
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
buckets = K._group_records(recs)
TOL = 2.0
sm = K._tier2_i47_scope_map(buckets, TOL)
eff = lambda c: K.IMAGE_OCR_TOLERANCE if c in K.IMAGE_OCR_COMPANIES else TOL
for b in buckets:
    tol = eff(b.code); pre, post = b.values, b.values_post
    i2, i2p = pre.get(2), post.get(2)
    i47, i48, i49, i51 = pre.get(47), pre.get(48), pre.get(49), pre.get(51)
    i48p, i49p, i51p = post.get(48), post.get(49), post.get(51)
    if None in (i2, i2p, i47, i48, i49, i51, i48p, i49p, i51p): continue
    promo = i2p - i2
    if promo <= tol: continue
    dp = i51p - i49p
    if dp + tol >= i48p: continue
    dt = dp + promo
    if dt <= i48 + tol: continue
    if abs((min(dt, i48) + i49) - i51) > tol: continue
    br, exc = K._tier2_branch(b, False, tol, scope=sm.get(b.code, K._TIER2_SCOPE_EXCL))
    cur = exc if br in K._TIER2_EXCESS_BEARING_BRANCHES and exc is not None else 0.0
    s = b.values; i4, i12, i13 = s.get(4), s.get(12), s.get(13)
    d0 = None if None in (i4,i12,i13) else round(i2-(i4-(i12-min(cur,max(0.0,i12)))-i13),2)
    d1 = None if None in (i4,i12,i13) else round(i2-(i4-(i12-min(dt-i48,max(0.0,i12)))-i13),2)
    print(f"{b.code} {b.quarter} dup={abs(i47-i48)<=tol} i47={i47} i48={i48} 현행exc={cur:.2f} "
          f"제안exc={dt-i48:.2f} 다리잔차 {d0} -> {d1}")
