# -*- coding: utf-8 -*-
"""Compute the properly-combined (multi-axis simultaneous) 흥국화재(KR0005) 2026.2Q 적용후
chain, using the gate's own R4/MARKET_M matrices (imported, not retyped) and raw-verified leaf
values. Same methodology as scripts/fix_20260821_kr0005_2024q4_market_combined.py /
scripts/_probes/compute_kr0005_20260821.py (that precedent's own probe) for the same company.

Raw source (fitz-read, data/disclosure/FY2026_Q2/pdf/KR0005_흥국화재.pdf):
  p18 (idx17) ② 장수·사업비·해지·대재해 경과조치 (IR axis)  생명장기위험액후=1,683,505백만=16835.05억
                                                          일반손해위험액후=82,474백만=824.74억
                                                          법인세조정액후=577,892백만=5778.92억 (IR-axis-only marginal)
  p19 (idx18) ③ 주식위험 경과조치 (EQ axis)   주식위험후=191,277백만=1912.77억 (다른 leaf 불변)
  p19 (idx18) ④ 금리위험 경과조치 (INT axis)  금리위험후 = "-" (blank, genuinely not printed —
              confirmed via fitz raw text, not a docling drop). Only 시장위험액후=397,646백만=3976.46억
              is printed, with 주식/부동산/외환/자산집중 legs explicitly unchanged (336,516/148,451/38,404/-).
              -> must invert MARKET_M to recover the 금리위험 leaf.
  p20 (idx19) 4-2-3 최근 3개 사업연도: 경과조치 후 지급여력기준금액(당기) = 17,718억 (headline anchor,
              also matches the [지급여력비율의 경과조치 적용에 관한 사항] intro block earlier in the MD).

Root cause (same shape as 2024.4Q): item19후(시장위험액 combined) was stored as table③'s OWN
isolated market-risk subtotal (3358.88, holds INT axis at 전 value 1252, only moves EQ). KR0005
elected all of IR+EQ+INT (_TRANSITION_KIND["KR0005"]={"IR","EQ","INT"}, confirmed against raw
table row 361-369 AND data/_derived/kics_transition_applicability.json 2026.1Q record), so the
true combined item19후 must move BOTH the EQ leaf (37) and the INT leaf (36) simultaneously via
MARKET_M. item36후 itself was also wrong (mirrored 값=1252 instead of the INT-axis-derived value).
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
from solvency.validation.kics_json_rules import R4, MARKET_M, _diversified_sqrt  # noqa: E402

# --- leaves (억원) already raw-verified correct in master / from table② (IR axis) ---
item17_post = 16835.05   # p18 ② table (already correct in master)
item18_post = 824.74     # p18 ② table (already correct in master)
item20_post = 2369.0     # unchanged (신용위험, no axis touches it)
item21_post = 4720.0     # unchanged (운영위험, no axis touches it)

item37_post = 1912.77    # p19 ③ table (EQ axis) — 주식위험 336,516 -> 191,277
item38_post = 1484.51    # unchanged (부동산)
item39_post = 384.04     # unchanged (외환)
item40_post = 0.0        # unchanged (자산집중)

# --- guard 1: reproduce 적용전 item15 from R4(17,18,19,20)+21 (sanity on matrix/order) ---
v_pre_eok = np.array([22688.0, 831.0, 4545.0, 2369.0])  # 값(전), 억원 직접
item15_pre_expected = _diversified_sqrt(v_pre_eok, R4) + 4720.0
print(f"[guard1] 적용전 item15 reproduced = {item15_pre_expected:.4f}  (master 값=29788)")

# --- step 0: invert MARKET_M to recover item36(금리)_post from ④ table's printed total ---
# ④ table: 시장위험액후 = 397,646백만 = 3976.46억; legs 주식/부동산/외환/자산집중 unchanged at PRE.
target19_INTonly = 3976.46
v_pre_market = {"주식": 3365.16, "부동산": 1484.51, "외환": 384.04, "자산집중": 0.0}
b, c, d, e = v_pre_market["주식"], v_pre_market["부동산"], v_pre_market["외환"], v_pre_market["자산집중"]

# quadratic(a) = a^2 + b^2+c^2+d^2+e^2 + 2a*(.25b+.25c+.25d+.25e) + 2*(.25bc -.25bd +0*be +.25cd +0*ce +0*de)
# with e=0: a^2 + a*(0.5b+0.5c+0.5d) + (b^2+c^2+d^2 + 0.5bc - 0.5bd + 0.5cd) - target^2 = 0
lin_coeff = 0.5 * b + 0.5 * c + 0.5 * d
const_no_a = b * b + c * c + d * d + 0.5 * b * c - 0.5 * b * d + 0.5 * c * d
const_term = const_no_a - target19_INTonly ** 2
roots = np.roots([1.0, lin_coeff, const_term])
real_roots = [r.real for r in roots if abs(r.imag) < 1e-6]
print(f"[step0] quadratic roots for item36(금리)_post: {roots} -> real: {real_roots}")
# baseline check: value of the quadratic sqrt at a=0 (금리=0)
a0_val = _diversified_sqrt(np.array([0.0, b, c, d, e]), MARKET_M)
print(f"[step0] sqrt(quadratic) at a=0 (금리=0) = {a0_val:.4f}  (target {target19_INTonly}, "
      f"diff={a0_val - target19_INTonly:+.4f})")
positive_roots = [r for r in real_roots if r > 1e-2]
if positive_roots:
    item36_post = min(positive_roots)
    print(f"[step0] using positive root: item36_post = {item36_post:.4f}")
else:
    # both roots <= ~0 (quadratic is monotonically increasing in a>=0 since all cross-terms
    # with 'a' carry +0.25; target already reached/exceeded at a=0) -> risk charge clamps to 0,
    # residual is sub-백만 rounding noise from the 2-decimal-억원 inputs being squared.
    item36_post = 0.0
    print(f"[step0] no root > 0 (closest real root {max(real_roots):+.5f} eok-won, "
          f"a=0 already {'meets/exceeds' if a0_val >= target19_INTonly else 'undershoots'} target) "
          f"-> clamp item36_post = 0.0")
print(f"[step0] item36_post (INT-axis derived, inverted from ④'s 시장위험액후=3976.46) = {item36_post:.4f}  "
      f"(전=1252.00, sanity: should be < 전 since TIRR phase-in reduces charge)")

# cross-check: does this item36_post reproduce 3976.46 when combined with PRE 주식/부동산/외환/자산집중?
check_v = np.array([item36_post, b, c, d, e])
check19 = _diversified_sqrt(check_v, MARKET_M)
print(f"[step0 check] sqrt(MARKET_M . [item36_post,주식전,부동산전,외환전,집중전]) = {check19:.4f}  "
      f"(target 3976.46, diff={check19 - target19_INTonly:+.4f})")

# --- combined item19_post via MARKET_M (5 leaves, BOTH INT and EQ axes moved simultaneously) ---
v19 = np.array([item36_post, item37_post, item38_post, item39_post, item40_post])
item19_post_combined = _diversified_sqrt(v19, MARKET_M)
print(f"\nitem19_post (combined, corrected) = {item19_post_combined:.4f}   "
      f"(was stored: 3358.88 = table③-only marginal, ignores INT axis)")

# --- combined item15_post via R4 (4 leaves: 17,18,19,20) + item21 ---
v15 = np.array([item17_post, item18_post, item19_post_combined, item20_post])
item15_post_combined = _diversified_sqrt(v15, R4) + item21_post
print(f"item15_post (combined) = {item15_post_combined:.4f}   (was stored: 23496.92, gate-flagged mismatch 79.07)")

# --- item16_post (분산효과) = childrensum(17,18,19,20,21) - item15 ---
childsum = item17_post + item18_post + item19_post_combined + item20_post + item21_post
item16_post_combined = childsum - item15_post_combined
print(f"item16_post (combined, 분산효과) = {item16_post_combined:.4f}   "
      f"(children sum={childsum:.4f}; was stored: 4610.98)")

# --- item14 anchor: disclosed headline (4-2-3 trend table + [지급여력비율의 경과조치...] intro),
#     both = 17,718억 ---
item14_disclosed = 17718.0
item23_post = 0.0
item22_post_residual = item15_post_combined - item14_disclosed + item23_post
print(f"item14_post (disclosed anchor, UNCHANGED) = {item14_disclosed}")
print(f"item22_post (법인세조정액, residual) = {item22_post_residual:.4f}   "
      f"(was stored: 5778.92 = table②-only marginal, ignores EQ/INT axes)")

# --- guard: monotonicity — combined item15 must be <= 전(29788) and <= each single-axis isolated value ---
item15_isolated_IR = 24131.28   # p18 ② table: 2,413,128백만 (IR axis alone)
item15_isolated_EQ = 29289.39   # p19 ③ table: 2,928,939백만 (EQ axis alone)
item15_isolated_INT = 29542.95  # p19 ④ table: 2,954,295백만 (INT axis alone)
print(f"\n[guard3] combined item15={item15_post_combined:.2f} <= 전 item15=29788.0? "
      f"{item15_post_combined <= 29788.0}")
print(f"[guard3] combined item15={item15_post_combined:.2f} <= isolated-IR-only {item15_isolated_IR}? "
      f"{item15_post_combined <= item15_isolated_IR}")
print(f"[guard3] combined item15={item15_post_combined:.2f} <= isolated-EQ-only {item15_isolated_EQ}? "
      f"{item15_post_combined <= item15_isolated_EQ}")
print(f"[guard3] combined item15={item15_post_combined:.2f} <= isolated-INT-only {item15_isolated_INT}? "
      f"{item15_post_combined <= item15_isolated_INT}")

# --- ratio cross-check: item27_post = item1_post/item14_post*100 should reproduce disclosed 201.45 ---
item1_post = 35693.0
item27_check = item1_post / item14_disclosed * 100
print(f"\n[crosscheck] item27_post = item1/item14*100 = {item27_check:.4f}  (disclosed 201.45, master item27후=201.45)")

# --- item28 cross-check (uses item2후=8433.02, unaffected by this fix, sanity only) ---
item2_post = 8433.02
item28_check = item2_post / item14_disclosed * 100
print(f"[crosscheck] item28_post = item2/item14*100 = {item28_check:.4f}  (master item28후=47.5957783)")

print("\n=== FINAL VALUES (round to 2 decimals for JSON) ===")
print(f"item15후 = {round(item15_post_combined, 2)}")
print(f"item16후 = {round(item16_post_combined, 2)}")
print(f"item19후 = {round(item19_post_combined, 2)}")
print(f"item22후 = {round(item22_post_residual, 2)}")
print(f"item36후 = {round(item36_post, 2)}")
print(f"item23후 = {round(item23_post, 2)}")
