# -*- coding: utf-8 -*-
"""Verify KR0032 2026.2Q extracted market-risk / IRR / TFI values against the real rule engine."""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")

from solvency.validation.kics_json_rules import (
    MARKET_M, irr_derive_expected,
)
import numpy as np

# ---- extracted from raw PDF p.32-35 (백만원 -> 억원, /100) ----
item36 = 191442 / 100  # 금리위험액
item37 = 262442 / 100  # 주식위험액
item38 = 73079 / 100   # 부동산위험액
item39 = 44707 / 100   # 외환위험액
item40 = 0.0           # 자산집중위험액

V = np.array([item36, item37, item38, item39, item40])
computed19 = float(np.sqrt(V @ MARKET_M @ V))
print(f"item36-40: {item36}, {item37}, {item38}, {item39}, {item40}")
print(f"computed item19 (sqrt V'MV) = {computed19:.4f}")
print(f"disclosed item19 (headline, rounded) = 3932")
print(f"disclosed item19_후 (from page18 TIR table, 393215백만/100) = 3932.15")
print(f"diff vs headline 3932 = {computed19 - 3932:.4f} ({(computed19-3932)/3932*100:.4f}%)")

print()

# ---- items 41-46 (충격전/평균회귀/금리상승/금리하락/금리평탄/금리경사), 순자산가치, 백만원/100 ----
item41 = 3282006 / 100
item42 = 3315191 / 100
item43 = 3057865 / 100
item44 = 3467439 / 100
item45 = 3310674 / 100
item46 = 3281319 / 100
print(f"item41-46: {item41}, {item42}, {item43}, {item44}, {item45}, {item46}")

irr_vals = {41: item41, 42: item42, 43: item43, 44: item44, 45: item45, 46: item46}
expected36 = irr_derive_expected(irr_vals)
print(f"irr_derive_expected(41-46) = {expected36:.4f}")
print(f"disclosed item36 = {item36}")
diff = item36 - expected36
print(f"diff (actual-expected) = {diff:.4f} ({diff/expected36*100:.4f}%)  [known systemic band on this company: +1.08%~+4.69% per kics_json_rules.py L82-90]")

print()
print("=== TFI table (page 17, 백만원/100) ===")
item47_pre, item47_post = 790829/100, 698170/100
item48_pre, item48_post = 672170/100, 672170/100
item49_pre, item49_post = 881595/100, 881595/100
item50_pre, item50_post = 1113624/100, 1113624/100
item51_pre, item51_post = 1553765/100, 1646424/100
item52_pre, item52_post = 2667389/100, 2760048/100
item53_pre = 0.0
item54_pre = 92658/100

print(f"item47 전/후 = {item47_pre} / {item47_post}")
print(f"item48 전/후 = {item48_pre} / {item48_post}")
print(f"item49 전/후 = {item49_pre} / {item49_post}")
print(f"item50 전/후 = {item50_pre} / {item50_post}")
print(f"item51 전/후 = {item51_pre} / {item51_post}")
print(f"item52 전/후 = {item52_pre} / {item52_post}")
print(f"item53 전 = {item53_pre}, item54 전 = {item54_pre}")

print()
print("-- identity checks --")
print(f"item50+item51 (전) = {item50_pre+item51_pre}  vs item52(전) = {item52_pre}  match={abs(item50_pre+item51_pre-item52_pre)<0.01}")
print(f"item50+item51 (후) = {item50_post+item51_post}  vs item52(후) = {item52_post}  match={abs(item50_post+item51_post-item52_post)<0.01}")
print(f"CAPPED 전: min(47,48)+49 = {min(item47_pre,item48_pre)+item49_pre}  vs item51(전) = {item51_pre}  match={abs(min(item47_pre,item48_pre)+item49_pre-item51_pre)<0.01}")
capped_post = min(item47_post, item48_post) + item49_post
print(f"CAPPED 후 (no item54): min(47,48)+49 = {capped_post}  vs item51(후) = {item51_post}  residual={item51_post-capped_post:.4f}  (expect ~= item54_전 {item54_pre})")
print(f"CAPPED 후 (+item54_전): min(47,48)+49+item54(전) = {capped_post+item54_pre}  vs item51(후) = {item51_post}  match={abs(capped_post+item54_pre-item51_post)<0.02}")

print()
item14_pre_headline = 13443.0
item14_pre_precise = 1344340/100
print(f"item48 == item14_적용전(headline rounded {item14_pre_headline}) x 50% = {item14_pre_headline*0.5}  actual item48={item48_pre}  diff={item48_pre-item14_pre_headline*0.5:.4f}")
print(f"item48 == item14_적용전(TFI-table precise {item14_pre_precise}) x 50% = {item14_pre_precise*0.5}  actual item48={item48_pre}  diff={item48_pre-item14_pre_precise*0.5:.6f}")

print()
print("=== item19_적용후 cross-check via mirrored 36-40 (적용후=적용전, per company's own historical pattern) ===")
computed19_post = computed19  # mirrored V => same matrix result
print(f"computed item19_적용후 (mirrored subs) = {computed19_post:.4f}  vs page18-sourced item19_적용후 = 3932.15")
