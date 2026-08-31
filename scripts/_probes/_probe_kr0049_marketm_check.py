import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from src.solvency.validation.kics_json_rules import MARKET_M  # noqa

print("MARKET_M matrix:")
for row in MARKET_M:
    print(row)

# item36..40 candidate values (억원), derived from raw PDF pages 36-41 (당기/current column)
item36 = 34555 / 100  # 금리위험액
item37 = 11718 / 100  # 주식위험액
item38 = 13641 / 100  # 부동산위험액
item39 = 20581 / 100  # 외환위험액
item40 = 6357 / 100   # 자산집중위험액

V = [item36, item37, item38, item39, item40]
print("\nV =", V)

total = 0.0
for i in range(5):
    for j in range(5):
        total += V[i] * MARKET_M[i][j] * V[j]

import math
item19_derived = math.sqrt(total)
print(f"\nderived item19 = sqrt({total:.4f}) = {item19_derived:.4f}")
print("actual item19 (from disclosure) = 536 (integer-rounded), 53618 백만원/100 = 536.18 precise")
