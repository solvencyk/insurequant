# -*- coding: utf-8 -*-
"""가드 민감도 — 각 가드를 하나씩 빼면 몇 버킷이 발동하고 축 A 가 몇 개 깨지는가.
'가드가 장식이 아니다' 를 수치로 보인다. 그리고 KR0087 나머지 분기 불변 확인."""
import json, sys, itertools
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from solvency.validation import kics_json_rules as K

recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
buckets = K._group_records(recs)
TOL = 2.0
scope_map = K._tier2_i47_scope_map(buckets, TOL)
eff = lambda c: K.IMAGE_OCR_TOLERANCE if c in K.IMAGE_OCR_COMPANIES else TOL

GUARDS = ["dup_row", "promo", "post_uncapped", "binds", "reproduces"]


def recover(b, tol, off=()):
    pre, post = b.values, b.values_post
    g = lambda d, k: d.get(k)
    i2, i2p = g(pre, 2), g(post, 2)
    i47, i48, i49, i51 = g(pre, 47), g(pre, 48), g(pre, 49), g(pre, 51)
    i48p, i49p, i51p = g(post, 48), g(post, 49), g(post, 51)
    if None in (i2, i2p, i47, i48, i49, i51, i48p, i49p, i51p):
        return None
    if "dup_row" not in off and abs(i47 - i48) > tol:
        return None
    promo = i2p - i2
    if "promo" not in off and promo <= tol:
        return None
    debt_post = i51p - i49p
    if "post_uncapped" not in off and debt_post + tol >= i48p:
        return None
    debt_true = debt_post + promo
    if "binds" not in off and debt_true <= i48 + tol:
        return None
    if "reproduces" not in off and abs((min(debt_true, i48) + i49) - i51) > tol:
        return None
    return debt_true - i48


def bridge_ok(b, exc, tol):
    s = b.values
    i2, i4, i12, i13 = s.get(2), s.get(4), s.get(12), s.get(13)
    if None in (i2, i4, i12, i13):
        return None
    return abs((i4 - (i12 - min(exc, max(0.0, i12))) - i13) - i2) <= tol


for off in [()] + [(g,) for g in GUARDS]:
    fired = solved = broken = 0
    names = []
    for b in buckets:
        tol = eff(b.code)
        scope = scope_map.get(b.code, K._TIER2_SCOPE_EXCL)
        branch, exc = K._tier2_branch(b, False, tol, scope=scope)
        cur = exc if branch in K._TIER2_EXCESS_BEARING_BRANCHES and exc is not None else 0.0
        new = recover(b, tol, off)
        if new is None or new < 0:
            continue
        fired += 1
        if branch not in K._TIER2_EXCESS_BEARING_BRANCHES:
            continue
        o, n = bridge_ok(b, cur, tol), bridge_ok(b, new, tol)
        if o is None or n is None or o == n:
            continue
        if n:
            solved += 1
        else:
            broken += 1
            names.append(f"{b.code} {b.quarter}")
    lbl = "전 가드 적용" if not off else f"가드 제거: {off[0]}"
    print(f"{lbl:32s} 발동={fired:3d}  해결={solved:2d}  파손={broken:2d}"
          + (f"  {names[:6]}" if names else ""))

print("\n=== KR0087 전 분기: 현행 룰 축 A(적용전) 상태 (제안 룰이 못 건드리는지 확인) ===")
for b in sorted((x for x in buckets if x.code == "KR0087"), key=lambda x: x.quarter):
    tol = eff(b.code)
    scope = scope_map.get(b.code, K._TIER2_SCOPE_EXCL)
    branch, exc = K._tier2_branch(b, False, tol, scope=scope)
    cur = exc if branch in K._TIER2_EXCESS_BEARING_BRANCHES and exc is not None else 0.0
    new = recover(b, tol)
    s = b.values
    i2, i4, i12, i13 = s.get(2), s.get(4), s.get(12), s.get(13)
    d = None if None in (i2, i4, i12, i13) else round(i2 - (i4 - (i12 - min(cur, max(0.0, i12))) - i13), 2)
    print(f"  {b.quarter}  i47={s.get(47)} i48={s.get(48)} branch={branch:10s} 현행exc={cur:8.2f} "
          f"다리잔차={d}  제안발동={'YES exc=%.2f' % new if new is not None else 'no'}")
