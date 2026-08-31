# -*- coding: utf-8 -*-
"""Full self-check of all confirmed KR0079 2026.2Q values against kics_json_rules identities."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from solvency.validation.kics_json_rules import R4, R7, MARKET_M

# ---- confirmed core items (page 16/19/20 direct read, 억원) ----
item1 = 37207
item2 = 23735
item3 = 13473
item4 = 34276
item5 = 10265
item7 = 17962
item8 = -218
item9 = -4828
item11 = 11096
item13 = 10542
item14 = 23962
item15 = 29924
item16 = 8714
item17 = 20349
item18 = 0
item19 = 12052
item20 = 3878
item21 = 2359
item22 = 5962
item23 = 0

print("=== rule 1: item1 == item2+item3 ===", item1, "vs", item2 + item3, "diff", item1 - (item2 + item3))
print("=== rule 5: item14 == item15-item22+item23 ===", item14, "vs", item15 - item22 + item23)
print("=== rule 6: item16 == sum(17..21)-item15 ===", item16, "vs", (item17 + item18 + item19 + item20 + item21) - item15)

V4 = np.array([item17, item18, item19, item20], dtype=float)
item15_expected = float(np.sqrt(V4 @ R4 @ V4)) + item21
print("=== rule 4: item15 == sqrt(V'R4V)+item21 ===", item15, "vs", item15_expected)

item27 = item1 / item14 * 100
item28 = item2 / item14 * 100
print("item27 (computed, full precision) =", item27)
print("item28 (computed, full precision) =", item28)

# ---- life sub-risks 29-35 (page 24/25 read, 백만원/100) ----
S = np.array([1842.32, 409.70, 8242.50, 0.0, 15899.62, 2479.25, 704.81])
item17_expected = float(np.sqrt(S @ R7 @ S))
print("=== 8_life: item17 == sqrt(S'R7S) ===", item17, "vs", item17_expected, "diversif ratio", S.sum() / item17_expected)

# ---- market sub-risks 36-40 (page 28/30/31 read, 백만원/100) ----
V = np.array([2341.56, 10081.54, 2919.10, 2260.87, 0.0])
item19_expected = float(np.sqrt(V @ MARKET_M @ V))
print("=== 19_market: item19 == sqrt(V'MV) ===", item19, "vs", item19_expected)

# ---- IRR 41-46 (page 28 read, 백만원/100) ----
item41, item42, item43, item44, item45, item46 = (
    -108292.87, -108136.38, -110728.81, -106116.93, -107664.13, -108846.48,
)
r_up = item41 - item43
r_down = item41 - item44
r_flat = item41 - item45
r_steep = item41 - item46
r_meanrev = item41 - item42
item36_expected = float(np.sqrt(max(r_up, r_down) ** 2 + max(r_flat, r_steep) ** 2)) + r_meanrev
print("=== 36_irr: item36 == sqrt(max(up,down)^2+max(flat,steep)^2)+meanrev ===")
print("   item36 (page28 direct) = 2341.56  vs derived =", item36_expected)

# ---- TFI table 47-54 (page 20 read, 백만원/100) ----
item47 = 13472.53
item48 = 11981.02
item49 = 10541.60
item50 = 23734.80
item51 = 13472.53
item52 = 37207.33
item54 = 2930.94
print("=== TFI: item50+item51 == item52 ===", item50 + item51, "vs", item52)
print("=== TFI: item48 == item14(전)*0.5 ===", item48, "vs", item14 * 0.5)
tier2_debt_incl = item47 - item49
print("=== TFI INCL scope: min(item47-item49,item48)+item49 == item51 ===",
      min(tier2_debt_incl, item48) + item49, "vs", item51)
print("=== TFI: item47-item49 == item54 (issued sub debt) ===", tier2_debt_incl, "vs", item54)
print("=== headline item3 ~= item47 (uncapped signature) ===", item3, "vs", item47)
