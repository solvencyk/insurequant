# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src")
import numpy as np
from solvency.validation.kics_json_rules import R4

V = np.array([20210.0, 0.0, 8193.0, 2350.0])  # item17,18,19,20
item21 = 2475.0
expected15 = float(np.sqrt(V @ R4 @ V)) + item21
print(f"rule4 expected item15 = {expected15:.4f}")
print(f"disclosed item15 (값, from p. detail table) = 26914")
print(f"currently-stored 값_적용후 (STALE) = 26913")
print(f"diff expected vs disclosed 값: {expected15-26914:.4f}")
