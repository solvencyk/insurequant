# -*- coding: utf-8 -*-
"""읽기 전용 전수 시뮬레이션 — `한도적용전 행이 한도값으로 인쇄된 버킷`의 한도초과 복원.

제안 룰(적용전 컬럼 한정):
  전제 D : item47 ~= item48 (한도적용전 행이 한도값을 인쇄 = TIER2_DUPLICATE_ROW)
  복원   : promo      = item2후 - item2전                (경과조치 기본자본 승격액)
           debt_post  = item51후 - item49후              (적용후 인정 채무성 보완자본)
           debt_true  = debt_post + promo
  가드   : promo > tol, debt_post + tol < item48후 (적용후 미구속), debt_true > item48전 + tol,
           그리고 min(debt_true, i48) + i49 == item51전 (인쇄 보완자본 재현)
  적용   : 한도초과 = debt_true - item48전   (기존 클램프 exc <= item12 는 그대로)

전 버킷에 대해 축 A(2_tier1_bridge, 적용전) 상태 전이를 센다: 해결 / 파손 / 무변동.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from solvency.validation import kics_json_rules as K

recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
buckets = K._group_records(recs)
TOL = K.DEFAULT_TOLERANCE if hasattr(K, "DEFAULT_TOLERANCE") else 2.0
scope_map = K._tier2_i47_scope_map(buckets, TOL)
print(f"buckets={len(buckets)}  tol={TOL}  INCL사={sorted(scope_map)}")


def eff_tol(code):
    return K.IMAGE_OCR_TOLERANCE if code in K.IMAGE_OCR_COMPANIES else TOL


def recover(b, tol):
    """제안 복원. 반환 (excess, why) 또는 (None, 사유)."""
    pre, post = b.values, b.values_post
    i2, i2p = pre.get(2), post.get(2)
    i47, i48, i49, i51 = pre.get(47), pre.get(48), pre.get(49), pre.get(51)
    i48p, i49p, i51p = post.get(48), post.get(49), post.get(51)
    if None in (i2, i2p, i47, i48, i49, i51, i48p, i49p, i51p):
        return None, "입력결측"
    if abs(i47 - i48) > tol:
        return None, "중복행 아님"
    promo = i2p - i2
    if promo <= tol:
        return None, "승격액 없음"
    debt_post = i51p - i49p
    if debt_post + tol >= i48p:
        return None, "적용후도 한도구속(복원불가)"
    debt_true = debt_post + promo
    if debt_true <= i48 + tol:
        return None, "복원해도 한도 미구속(초과 0)"
    if abs((min(debt_true, i48) + i49) - i51) > tol:
        return None, "복원값이 인쇄 보완자본을 재현 못함"
    return debt_true - i48, f"promo={promo:.2f} debt_post={debt_post:.2f} debt_true={debt_true:.2f}"


def bridge(b, exc, tol):
    src = b.values
    i2, i4, i12, i13 = src.get(2), src.get(4), src.get(12), src.get(13)
    if None in (i2, i4, i12, i13):
        return None
    e = min(exc, max(0.0, i12))
    expected = i4 - (i12 - e) - i13
    return abs(expected - i2) <= tol, round(i2 - expected, 4), round(e, 4)


solved, broken, same, fired = [], [], 0, []
for b in buckets:
    tol = eff_tol(b.code)
    scope = scope_map.get(b.code, K._TIER2_SCOPE_EXCL)
    branch, exc = K._tier2_branch(b, False, tol, scope=scope)
    cur_exc = exc if branch in K._TIER2_EXCESS_BEARING_BRANCHES and exc is not None else 0.0
    new_exc_val, why = recover(b, tol)
    if new_exc_val is None:
        continue
    fired.append((b.code, b.quarter, branch, round(cur_exc, 2), round(new_exc_val, 2), why))
    if branch not in K._TIER2_EXCESS_BEARING_BRANCHES:
        continue  # 축 A 는 excess-bearing 갈래에서만 초과를 더한다
    old = bridge(b, cur_exc, tol)
    new = bridge(b, new_exc_val, tol)
    if old is None or new is None:
        continue
    if old[0] == new[0]:
        same += 1
    elif new[0]:
        solved.append((b.code, b.quarter, old, new))
    else:
        broken.append((b.code, b.quarter, old, new))

print(f"\n=== 전제 D(중복행)+가드 전부 통과해 룰이 발동하는 버킷: {len(fired)} ===")
for r in fired:
    print("   ", r)
print(f"\n해결 {len(solved)} / 파손 {len(broken)} / 무변동 {same}")
for tag, lst in (("해결", solved), ("파손", broken)):
    for c, q, old, new in lst:
        print(f"  [{tag}] {c} {q}: 현행 pass={old[0]} diff={old[1]} exc={old[2]} "
              f"-> 제안 pass={new[0]} diff={new[1]} exc={new[2]}")

# 중복행 버킷 전수(가드 탈락 사유 포함) — 은닉 필터 확인용
print("\n=== item47 ~= item48 인 버킷 전수 (가드 탈락 사유) ===")
n = 0
for b in buckets:
    tol = eff_tol(b.code)
    i47, i48 = b.values.get(47), b.values.get(48)
    if i47 is None or i48 is None or abs(i47 - i48) > tol:
        continue
    n += 1
    v, why = recover(b, tol)
    print(f"  {b.code} {b.quarter} i47={i47} i48={i48} -> "
          + (f"발동 exc={v:.2f} ({why})" if v is not None else f"미발동: {why}"))
print(f"  총 {n}버킷")
