# -*- coding: utf-8 -*-
"""Self-check candidate KR0002 2026.2Q items 36-46 against the real validator formulas
(imported, not retyped) before writing the patch file."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(r"C:\Users\sangwook.cho\Desktop\insurequant")))

from src.solvency.validation.kics_json_rules import (
    MARKET_M, _diversified_sqrt, irr_derive_expected,
)

# candidate values, converted 백만원 -> 억원 (/100), from raw PDF pp.33/35/36
item36 = 216050 / 100
item37 = 1212656 / 100
item38 = 122487 / 100
item39 = 128065 / 100
item40 = 0.0

item41 = 6129157 / 100
item42 = 6173625 / 100
item43 = 5874869 / 100
item44 = 6356816 / 100
item45 = 6072524 / 100
item46 = 6199850 / 100

print("candidate 36-40:", item36, item37, item38, item39, item40)
print("candidate 41-46:", item41, item42, item43, item44, item45, item46)

# check 19_market: item19 = sqrt(V' MARKET_M V), V=[36,37,38,39,40]
v = [item36, item37, item38, item39, item40]
expected19 = _diversified_sqrt(v, MARKET_M)
print(f"\nderived item19 = {expected19:.4f}")
print("source item19 (전, 억원 rounded, from summary table) = 13081")
print("source item19 (후, 백만원-precise / from TFI table)  = ", 1308105 / 100)

# check 36_irr: item36 = derive(41-46)
irr_vals = {36: item36, 41: item41, 42: item42, 43: item43, 44: item44, 45: item45, 46: item46}
expected36 = irr_derive_expected(irr_vals)
print(f"\nderived item36 (from 41-46) = {expected36:.4f}")
print(f"source item36 (직접공시, page33 'Ⅳ.금리위험액') = {item36:.4f}")
print(f"residual = {expected36 - item36:.6f}")

# cross-check against 2025.4Q already-loaded data (page 34 columns, should match verbatim)
print("\n--- 2025.4Q cross-validation (page 34 vs already-loaded kics_disclosure.json) ---")
q4_2025 = {
    41: 5022854 / 100, 42: 5055472 / 100, 43: 5011600 / 100,
    44: 4976418 / 100, 45: 4873513 / 100, 46: 5179253 / 100,
    36: 123776 / 100,
}
print("page34-derived 2025.4Q item41-46, item36:", q4_2025)
print("already-loaded (from earlier probe): item41=50228.54 item42=50554.72 item43=50116 "
      "item44=49764.18 item45=48735.13 item46=51792.53 item36=1237.76")
