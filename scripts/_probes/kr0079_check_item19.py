# -*- coding: utf-8 -*-
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import MARKET_M, R4
import numpy as np

V = np.array([2341.56, 10081.54, 2919.10, 2260.87, 0.0])
item19_expected = float(np.sqrt(V @ MARKET_M @ V))
print("V(36-40) =", V.tolist())
print("item19_expected =", item19_expected)
print("currently loaded (OCR) item19 = 72052  <- clearly wrong, digit garble")

# also check item15 = sqrt([17,18,19,20]' R4 [17,18,19,20]) + item21
item17 = 20349.23
item18 = 0.0
item19 = item19_expected
item20 = 3878.0  # OCR-read, matches 2026.1Q comparative col exactly (confirm below)
item21 = 2359.0  # OCR item21 as loaded
Vb = np.array([item17, item18, item19, item20])
item15_expected = float(np.sqrt(Vb @ R4 @ Vb)) + item21
print("item15_expected (from 17/18/19/20/21) =", item15_expected)
print("currently loaded item15 = 29924 (직접읽음, page19 예정 재검증)")
