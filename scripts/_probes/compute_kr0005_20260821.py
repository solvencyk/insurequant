# -*- coding: utf-8 -*-
"""Compute the properly-combined (multi-axis simultaneous) 흥국화재 2024.4Q 적용후 chain,
using the gate's own R4/MARKET_M matrices (imported, not retyped) and the raw-verified leaf
values (items 17,18,20,21,36-40 already correct in master; item19 is the one under repair).
Methodology (matches validation's established combined-transition approach,
scripts/rebuild_combined_transition_after.py): each selective-transition table in the raw
moves ONLY its own leaf; the combined post-transition parent = correlation-formula applied to
all leaves simultaneously (not any single isolated table's own subtotal)."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
from solvency.validation.kics_json_rules import R4, MARKET_M, _diversified_sqrt  # noqa: E402

# --- leaves (억원), all raw-verified from data/disclosure/FY2024_Q4/raw/KR0005_흥국화재.pdf ---
item17_post = 15021.33   # p42 ② table (IR-only axis; already correct in master)
item18_post = 732.35     # p42 ② table (already correct in master)
item20_post = 2757.0     # unchanged (신용위험, no axis touches it)
item21_post = 1122.0     # unchanged (운영위험, no axis touches it)

item36_post = 399.35     # p44 ④ table (INT axis)
item37_post = 2180.10    # p42-43 ③ table (EQ axis)
item38_post = 1035.06    # unchanged
item39_post = 545.47     # unchanged
item40_post = 0.0        # unchanged

# --- guard 1: reproduce 적용전 item15 from R4(17,18,19,20)+21 (sanity on the matrix/order) ---
v_pre = np.array([19348.0, 738.0, 5375.0, 2757.0])  # 백만원 -> will scale below; use 억원 same ratio
v_pre_eok = np.array([19348 / 10, 738 / 10, 5375 / 10, 2757 / 10])  # not needed; use direct 억원 read
# master already stores 값(전) directly in 억원 (item17=19348 is 억원 per earlier query: '19348')
v_pre_eok = np.array([19348.0, 738.0, 5375.0, 2757.0])
item15_pre_expected = _diversified_sqrt(v_pre_eok, R4) + 1122.0
print(f"[guard1] 적용전 item15 reproduced = {item15_pre_expected:.2f}  (master=23493)")

# --- combined item19_post via MARKET_M (5 leaves) ---
v19 = np.array([item36_post, item37_post, item38_post, item39_post, item40_post])
item19_post_combined = _diversified_sqrt(v19, MARKET_M)
print(f"item19_post (combined, corrected) = {item19_post_combined:.4f}   (was stored: 3860.81, gate-computed: 2801.44)")

# --- combined item15_post via R4 (4 leaves: 17,18,19,20) + item21 ---
v15 = np.array([item17_post, item18_post, item19_post_combined, item20_post])
item15_post_combined = _diversified_sqrt(v15, R4) + item21_post
print(f"item15_post (combined) = {item15_post_combined:.4f}")

# --- item16_post (분산효과) = childrensum(17,18,19,20,21) - item15 ---
childsum = item17_post + item18_post + item19_post_combined + item20_post + item21_post
item16_post_combined = childsum - item15_post_combined
print(f"item16_post (combined, 분산효과) = {item16_post_combined:.4f}   (children sum={childsum:.4f})")

# --- item14 anchor: disclosed headline (raw p37 총괄 + p44 5-2-3 trend table, both = 13,978억) ---
item14_disclosed = 13978.0
item23_post = 0.0
item22_post_residual = item15_post_combined - item14_disclosed + item23_post
print(f"item14_post (disclosed anchor) = {item14_disclosed}")
print(f"item22_post (법인세조정액, residual) = {item22_post_residual:.4f}   (was stored: 4443.96)")

# --- guard: monotonicity — combined item15 must be <= either single-axis-isolated item15 ---
item15_isolated_INT = 23075.55  # p44 ④ table: 2,307,555백만
item15_isolated_EQ = None       # not directly captured; skip if unavailable
print(f"[guard3] combined item15={item15_post_combined:.2f} <= isolated-INT-only {item15_isolated_INT}? "
      f"{item15_post_combined <= item15_isolated_INT}")
print(f"[guard3] combined item15={item15_post_combined:.2f} <= 전 item15=23493? "
      f"{item15_post_combined <= 23493}")

# --- ratio cross-check: item27_post = item1_post/item14_post*100 should reproduce disclosed 199.56 ---
item1_post = 27894.0
item27_check = item1_post / item14_disclosed * 100
print(f"[crosscheck] item27_post = item1/item14*100 = {item27_check:.2f}  (disclosed 199.56)")
