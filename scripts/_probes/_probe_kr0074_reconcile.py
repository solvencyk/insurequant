# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src")
import numpy as np
from solvency.validation.kics_json_rules import MARKET_M, irr_derive_expected

# --- 19_market check: item19 = sqrt(V' M V), V=[36,37,38,39,40] ---
V = np.array([4093.59, 5564.55, 1048.26, 1469.82, 60.78])
expected19 = float(np.sqrt(V @ MARKET_M @ V))
actual19 = 8193.0  # from item19 값 currently stored (억원, from core 값 already loaded)
print(f"19_market: expected(from 36-40)={expected19:.4f}  actual(item19)={actual19}  diff={expected19-actual19:.4f}")

# --- 36_irr check ---
values = {41: 71250.84, 42: 71521.96, 43: 67040.49, 44: 75751.56, 45: 70100.37, 46: 72529.62}
expected36 = irr_derive_expected(values)
actual36_printed_raw = 409359 / 100  # 백만원 -> 억원, printed "Ⅳ. 금리 위험액" on p.25
print(f"36_irr: expected(from 41-46)={expected36:.4f}  printed(item36 raw p.25)={actual36_printed_raw}  diff={expected36-actual36_printed_raw:.4f}")

tol_36irr = 0.05  # IRR_DERIVED_TOL_REL
rel_diff = abs(expected36 - actual36_printed_raw) / abs(actual36_printed_raw)
print(f"36_irr relative diff = {rel_diff*100:.4f}%  (tol={tol_36irr*100}%)")

tol_19mkt = 0.01  # DIVERSIFIED_SQRT_TOL_REL
rel_diff19 = abs(expected19 - actual19) / abs(actual19)
print(f"19_market relative diff = {rel_diff19*100:.4f}%  (tol={tol_19mkt*100}%)")
