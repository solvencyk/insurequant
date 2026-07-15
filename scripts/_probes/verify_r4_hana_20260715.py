import math

R4 = [
    [1.0, 0.0, 0.25, 0.25],
    [0.0, 1.0, 0.25, 0.25],
    [0.25, 0.25, 1.0, 0.25],
    [0.25, 0.25, 0.25, 1.0],
]


def item15_from_v(V):
    total = 0.0
    for i in range(4):
        for j in range(4):
            total += R4[i][j] * V[i] * V[j]
    return math.sqrt(total)


V = [4055.79, 0.0, 1440.74, 1057.64]  # 17,18,19,20
item21 = 511.49
item15 = item15_from_v(V) + item21
print(f"computed item15 = {item15:.2f}")

for item22, item23, label in [(0.26, 0.0, "raw-precise 22=0.26"), (0.0, 0.0, "stored 22=0")]:
    item14 = item15 - item22 + item23
    print(f"  using {label}: item14 = {item14:.2f}  (headline says 5558)")

item27 = 8622.61 / (item15 - 0.26) * 100
print(f"cross-check item27 with item22=0.26: {item27:.2f} (headline says 155.13)")
