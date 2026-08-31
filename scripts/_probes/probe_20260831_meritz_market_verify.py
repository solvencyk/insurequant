# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\src")
import numpy as np
from solvency.validation.kics_json_rules import MARKET_M

v5 = np.array([3711.76, 16569.84, 3606.42, 5755.82, 7056.78])
est = float(np.sqrt(max(v5 @ MARKET_M @ v5, 0)))
print("est:", est, "vs item19=20615")
print("rel:", abs(est-20615)/20615*100, "%")
