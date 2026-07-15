import math

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

# raw (백만원)/100, KR0104 2023.2Q ③표 후: 금리 1,298,257 / 주식 403,544 /
# 부동산 261,348(unchanged) / 외환 262,607(unchanged) / 자산집중 0
V = [1_298_257 / 100, 403_544 / 100, 261_348 / 100, 262_607 / 100, 0.0]
total = sum(M[i][j] * V[i] * V[j] for i in range(5) for j in range(5))
item19 = math.sqrt(total)
print(f"computed item19 from 36-40 = {item19:.2f}  (stored item19 = 16191.70)")
