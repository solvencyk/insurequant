import io
import sys
sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
from solvency.validation.kics_json_rules import (
    MARKET_M, R4, _diversified_sqrt, irr_derive_expected,
)

# ---- extracted raw values (억원), from MD lines 616-757 (2026년 2/4분기 blocks) ----
item19 = 157702.0

item36 = 1_383_302 / 100   # 금리위험액 (line 645, 6th scenario col, docling merge artifact)
item37 = 14_722_584 / 100  # 주식위험액 (line 687 first "Ⅲ.합계2)" block)
item38 = 990_758 / 100     # 부동산위험액 (line 709 first "Ⅲ.합계" block)
item39 = 1_062_126 / 100   # 외환위험액 (line 732 first "계" row)
item40 = 4_039_558 / 100   # 자산집중위험액 (line 752 first "계" row, 2026년 2/4분기 group)

V = np.array([item36, item37, item38, item39, item40])
est19 = _diversified_sqrt(V, MARKET_M)
print(f"36-40 = {V.tolist()}")
print(f"item19 disclosed = {item19}")
print(f"item19 derived sqrt(V'MV) = {est19:.4f}  diff={est19-item19:.4f}  rel={abs(est19-item19)/item19*100:.4f}%")

# ---- rule6 cross-check: item16 = sum(17-21) - item15 ----
item15, item16, item17, item18, item20, item21 = 212079.0, 71628.0, 73281.0, 21737.0, 22942.0, 8044.0
s = item17 + item18 + item19 + item20 + item21
print(f"\nrule6: sum(17..21)={s}  -item15={s-item15}  vs item16={item16}  diff={s-item15-item16}")

# ---- rule4 cross-check: item15 = sqrt([17,18,19,20]' R4 [..]) + item21 ----
v4 = np.array([item17, item18, item19, item20])
est15 = _diversified_sqrt(v4, R4) + item21
print(f"rule4: derived item15={est15:.4f}  vs disclosed={item15}  diff={est15-item15:.4f}")

# ---- 36_irr cross-check ----
item41 = 17_227_623 / 100
item42 = 17_414_960 / 100
item43 = 15_677_339 / 100
item44 = 18_691_873 / 100
item45 = 16_975_586 / 100
item46 = 17_472_287 / 100
irr_vals = {41: item41, 42: item42, 43: item43, 44: item44, 45: item45, 46: item46}
est36 = irr_derive_expected(irr_vals)
print(f"\n41-46 = {irr_vals}")
print(f"36_irr: derived item36={est36:.4f}  vs disclosed(table)={item36:.4f}  diff={est36-item36:.4f}  rel={abs(est36-item36)/item36*100:.4f}%")

# ---- item48 = item14(적용전) x 50% ----
item14 = 155555.0
item48_expected = item14 * 0.5
item48_raw = 7_777_770 / 100
print(f"\nitem48 formula expected = {item48_expected}")
print(f"item48 from raw TFI table = {item48_raw}  diff={item48_raw-item48_expected}")
print(f"item48 CURRENTLY STORED (wrong, = item3) = 97415.0")

item47_raw = 308_980 / 100
item49_raw = 9_432_538 / 100
item3 = 97415.0
comp3 = min(item47_raw, item48_raw) + item49_raw
print(f"\nitem47(raw)={item47_raw}  item49(raw)={item49_raw}")
print(f"rule 3_tier2_composition: min(47,48)+49 = {comp3:.4f}  vs item3={item3}  diff={comp3-item3:.4f}")

item50_raw = 34_246_418 / 100
item51_raw = 9_741_518 / 100
item52_raw = 43_987_936 / 100
item53_raw = 0.0
item54_raw = 0.0
comp51 = min(item47_raw, item48_raw) + item49_raw + item54_raw
print(f"\nitem50(raw)={item50_raw}  item51(raw)={item51_raw}  item52(raw)={item52_raw}")
print(f"rule 51_tfi_tier2_composition: min(47,48)+49+54 = {comp51:.4f}  vs item51(raw)={item51_raw}  diff={comp51-item51_raw:.4f}")
print(f"rule 50_tfi_tier_split: item50+item51 = {item50_raw+item51_raw:.4f}  vs item52(raw)={item52_raw}  diff={item50_raw+item51_raw-item52_raw:.4f}")
print(f"item50(raw) vs headline item2=342464.0  diff={item50_raw-342464.0:.4f}")
print(f"item51(raw) vs headline item3=97415.0  diff={item51_raw-97415.0:.4f}")
print(f"item52(raw) vs headline item1=439879.0  diff={item52_raw-439879.0:.4f}")
