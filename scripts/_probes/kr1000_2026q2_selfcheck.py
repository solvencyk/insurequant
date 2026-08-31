# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from solvency.validation.kics_json_rules import (
    R4, MARKET_M, irr_derive_expected, _diversified_sqrt, IRR_SCENARIO_ITEMS,
)

print("IRR_SCENARIO_ITEMS =", IRR_SCENARIO_ITEMS)

# --- raw extracted figures (백만원, from raw PDF pages 20-21 via fitz + MD tables) ---
mn = {
    36: 478_074,      # Ⅳ.금리위험액 row, leading value (page20)
    37: 716_903,      # 주식위험액 Ⅲ.합계, 2026년2분기 block (page21)
    38: 153_965,      # 부동산위험액 Ⅲ.합계, first block (MD line ~754)
    39: 337_815,      # 외환위험액 계/계, first block (MD line ~778)
    40: 1_279,        # 자산집중위험액 계/계, first block (MD line ~799)
    41: 5_571_520,    # 순자산가치 충격전
    42: 5_598_973,    # 순자산가치 평균회귀
    43: 5_068_868,    # 순자산가치 금리상승
    44: 6_150_170,    # 순자산가치 금리하락
    45: 5_517_678,    # 순자산가치 금리평탄
    46: 5_637_558,    # 순자산가치 금리경사
}
eok = {k: v / 100.0 for k, v in mn.items()}  # -> 억원
for k in sorted(eok):
    print(f"item{k} = {mn[k]:>12,} 백만원 = {eok[k]:>12.4f} 억원")

# --- 36_irr: item36 =? irr_derive_expected(41-46) ---
irr_vals = {i: eok[i] for i in IRR_SCENARIO_ITEMS}
expected_36 = irr_derive_expected(irr_vals)
print(f"\n[36_irr check] disclosed item36={eok[36]:.4f} vs derived={expected_36:.4f} "
      f"diff={eok[36]-expected_36:+.4f}")

# --- 19_market: item19 =? sqrt(V' MARKET_M V), V=[36,37,38,39,40] ---
V = np.array([eok[36], eok[37], eok[38], eok[39], eok[40]], dtype=float)
expected_19 = _diversified_sqrt(V, MARKET_M)
disclosed_19 = 10627.0  # existing 전 value in kics_disclosure.json
print(f"[19_market check] disclosed item19={disclosed_19:.4f} vs derived={expected_19:.4f} "
      f"diff={disclosed_19-expected_19:+.4f} rel={abs(disclosed_19-expected_19)/expected_19*100:.4f}%")

# --- rule4/15: item15 =? sqrt([17,18,19,20]' R4 [17,18,19,20]) + item21 ---
for label, i17, i18, i19, i20, i21, i15_disclosed in [
    ("전", 12903, 15578, 10627, 4247, 2555, 30386),
    ("후(mirror)", 12903, 15578, 10627, 4247, 2555, 30385),
]:
    Vr4 = np.array([i17, i18, i19, i20], dtype=float)
    expected_15 = _diversified_sqrt(Vr4, R4) + i21
    print(f"[rule4/15 check {label}] disclosed item15={i15_disclosed} vs derived={expected_15:.4f} "
          f"diff={i15_disclosed-expected_15:+.4f}")

# --- rule5/14: item14 =? item15-item22+item23 ---
for label, i15, i22, i23, i14_disclosed in [
    ("전", 30386, 7216, 184, 23353),
    ("후(mirror)", 30385, 7216, 184, 23353),
]:
    expected_14 = i15 - i22 + i23
    print(f"[rule5/14 check {label}] disclosed item14={i14_disclosed} vs derived={expected_14} "
          f"diff={i14_disclosed-expected_14:+d}")

# --- rule6/16: item16 =? sum(17..21) - item15 ---
for label, i17, i18, i19, i20, i21, i15, i16_disclosed in [
    ("전", 12903, 15578, 10627, 4247, 2555, 30386, 15525),
    ("후(mirror i15=30385)", 12903, 15578, 10627, 4247, 2555, 30385, None),
]:
    expected_16 = (i17+i18+i19+i20+i21) - i15
    print(f"[rule6/16 check {label}] disclosed item16={i16_disclosed} vs derived={expected_16} ")
