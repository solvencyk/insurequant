# -*- coding: utf-8 -*-
"""ABL생명(KR0070) 2025.3Q -- does item15후 = sqrt(V'R4V)+item21후 hold with the CURRENTLY
STORED items 17/18/19/20/21후? If yes, item16후 alone is the defect (should be the arithmetic
residual). If no, something in 15/17-21 is also off and needs raw-PDF re-derivation.
Read-only, imports R4/_diversified_sqrt from the rule engine (no retyping).
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.solvency.validation.kics_json_rules import R4, _diversified_sqrt  # noqa: E402
import numpy as np  # noqa: E402

# currently stored (from probe_20260901_abc_baseline.py dump)
stored = {15: 12459.99, 16: 5639.87, 17: 7471.13, 18: 0.0, 19: 4391.01, 20: 3499.0, 21: 1302.0}

V = np.array([stored[17], stored[18], stored[19], stored[20]], dtype=float)
mmult15 = _diversified_sqrt(V, R4) + stored[21]
print(f"mmult-derived item15후 = {mmult15:.4f}  (stored item15후 = {stored[15]})")
print(f"  diff = {mmult15 - stored[15]:.4f}")

r6_calc = sum(stored[i] for i in (17, 18, 19, 20, 21)) - stored[15]
print(f"\nR6 (sum17-21 - 15) = {r6_calc:.4f}  (stored item16후 = {stored[16]}, diff={stored[16]-r6_calc:.4f})")

# hypothesis: item16 was computed using item19-PRE (5828) instead of item19-POST (4391.01)
alt_v19 = 5828.0
r6_using_pre19 = (stored[17] + stored[18] + alt_v19 + stored[20] + stored[21]) - stored[15]
print(f"\nhypothesis: item16 computed with item19=pre({alt_v19}) instead of post: {r6_using_pre19:.4f}"
      f"  vs stored {stored[16]}  diff={stored[16]-r6_using_pre19:.4f}")

# also test mmult15 using item19-PRE instead
V2 = np.array([stored[17], stored[18], alt_v19, stored[20]], dtype=float)
mmult15_alt = _diversified_sqrt(V2, R4) + stored[21]
print(f"\nmmult15 using item19=pre: {mmult15_alt:.4f} vs stored item15후 {stored[15]}")
