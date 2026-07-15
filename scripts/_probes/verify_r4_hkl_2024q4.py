import math

R4 = [
    [1.0, 0.0, 0.25, 0.25],
    [0.0, 1.0, 0.25, 0.25],
    [0.25, 0.25, 1.0, 0.25],
    [0.25, 0.25, 0.25, 1.0],
]


def item15_calc(V, item21):
    core = sum(R4[i][j] * V[i] * V[j] for i in range(4) for j in range(4))
    return math.sqrt(core) + item21


v17 = 922_222 / 100    # (2)-table, disjoint
v18 = 0.0
v19 = 591_521 / 100    # (3)-table, disjoint
v20 = 405_758 / 100    # both tables agree unchanged
item21 = 80_133 / 100  # both tables agree unchanged

item15 = item15_calc([v17, v18, v19, v20], item21)
print(f"computed item15 (R4, disjoint 17/19) = {item15:.2f}")

headline_item14 = 16987.0
net_22_minus_23 = item15 - headline_item14
print(f"trusted headline item14 = {headline_item14}")
print(f"=> item22 - item23 (net) = item15 - item14 = {net_22_minus_23:.2f}")

# compare against the two raw tables' own (22-23) implied nets, for context
for label, i22, i23 in [("(2)표", 348_792 / 100, 599_206 / 100), ("(3)표", 429_635 / 100, 703_625 / 100)]:
    print(f"  {label}: item22={i22:.2f} item23={i23:.2f} net(22-23)={i22-i23:.2f}")
