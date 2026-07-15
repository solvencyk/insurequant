"""KR0104 2023.1Q: does R4(17=raw②,18=0,19=raw③,20,21) reproduce the
already-trusted item15=28917 (identity-derived from headline item14=22802)?
If yes, the raw ②-table item17=8979.70 is consistent and the previously
reverted cells (33,34,35 = 해지/사업비/대재해) can be safely re-derived from
the SAME ②-table now that we trust the parent chain end-to-end."""
import math

R4 = [
    [1.0, 0.0, 0.25, 0.25],
    [0.0, 1.0, 0.25, 0.25],
    [0.25, 0.25, 1.0, 0.25],
    [0.25, 0.25, 0.25, 1.0],
]


def item15_from_v(V):
    total = sum(R4[i][j] * V[i] * V[j] for i in range(4) for j in range(4))
    return math.sqrt(total)


# raw (백만원)/100:
v17_raw2 = 897_970 / 100     # (2)표 생명장기 후
v18 = 0.0
v19_raw3 = 1_813_184 / 100   # (3)표 시장위험 후
v20 = 1_016_519 / 100
v21 = 186_219 / 100

core = item15_from_v([v17_raw2, v18, v19_raw3, v20])
item15_from_raw = core + v21
print(f"item17(raw (2)표)={v17_raw2:.2f}  item19(raw (3)표)={v19_raw3:.2f}")
print(f"item20={v20:.2f}  item21={v21:.2f}")
print(f"R4-computed item15 = {item15_from_raw:.2f}   (trusted/stored item15 = 28917)")
print(f"diff = {item15_from_raw - 28917:.2f}")

# reverse-solve: what item17 would make R4(...)  + item21 == 28917 exactly?
target_core = (28917 - v21) ** 2
# core = x^2 + v19^2 + v20^2 + 0.5*x*v19 + 0.5*x*v20 + 0.5*v19*v20  (v18=0)
# x^2 + x*(0.5*v19+0.5*v20) + (v19^2+v20^2+0.5*v19*v20 - target_core) = 0
b = 0.5 * v19_raw3 + 0.5 * v20
c = v19_raw3 ** 2 + v20 ** 2 + 0.5 * v19_raw3 * v20 - target_core
disc = b * b - 4 * c
if disc >= 0:
    x1 = (-b + math.sqrt(disc)) / 2
    x2 = (-b - math.sqrt(disc)) / 2
    print(f"reverse-solved item17 candidates: {x1:.2f}, {x2:.2f}  (old changelog value: 10899.56)")
else:
    print("no real solution")
