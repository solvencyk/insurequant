"""Cross-check KR0104 2026.1Q item36-40(후) reproduces item19(후)=10865.69
via the MARKET_M formula, before writing them."""
import math

# diag 1.0; (37,39) FX-equity = -0.25; 40(자산집중) paired w/ anything = 0; else 0.25
names = [36, 37, 38, 39, 40]
M = [[0.0] * 5 for _ in range(5)]
for i in range(5):
    M[i][i] = 1.0
for i in range(5):
    for j in range(5):
        if i == j:
            continue
        a, b = names[i], names[j]
        if 40 in (a, b):
            M[i][j] = 0.0
        elif {a, b} == {37, 39}:
            M[i][j] = -0.25
        else:
            M[i][j] = 0.25

V = [5314.85, 5491.41, 3018.74, 3778.16, 0.0]
total = sum(M[i][j] * V[i] * V[j] for i in range(5) for j in range(5))
item19 = math.sqrt(total)
print(f"computed item19 from 36-40 = {item19:.2f}  (already-stored item19 = 10865.69)")
