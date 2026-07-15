"""Cross-check: does the disjoint-table-derived (17,18,19,20) reproduce item15
via the R4 formula, matching the headline-ratio-anchored item14/15?
If yes, the disjoint extraction (item17 from (2)-table alone, item19 from
(3)-table alone) is internally consistent and not just a guess."""
import math

R4 = [
    [1.0, 0.0, 0.25, 0.25],
    [0.0, 1.0, 0.25, 0.25],
    [0.25, 0.25, 1.0, 0.25],
    [0.25, 0.25, 0.25, 1.0],
]


def item15_from_v(v17, v18, v19, v20):
    V = [v17, v18, v19, v20]
    total = 0.0
    for i in range(4):
        for j in range(4):
            total += R4[i][j] * V[i] * V[j]
    return math.sqrt(total)


cases = {
    "NH농협생명 2026.1Q": dict(
        v17=11926.15, v18=0.0, v19=10865.69, v20=7697.0,
        item21=2696.0, item22=5923.0, item23=0.0,
        headline_item14=18500.0,  # already-stored, headline-ratio-anchored
    ),
    "교보생명 2026.1Q": dict(
        v17=32226.72, v18=0.0, v19=49562.71, v20=25686.0,
        item21=5136.0, item22=14697.0, item23=1888.0,
        headline_item14=69811.0,  # already-stored, headline-ratio-anchored
    ),
}

for name, c in cases.items():
    core = item15_from_v(c["v17"], c["v18"], c["v19"], c["v20"])
    item15 = core + c["item21"]
    item14_check = item15 - c["item22"] + c["item23"]
    print(f"=== {name} ===")
    print(f"  V=(17={c['v17']}, 18={c['v18']}, 19={c['v19']}, 20={c['v20']})")
    print(f"  computed item15 (R4 formula) = {item15:.2f}")
    print(f"  -> derived item14 = item15-22+23 = {item14_check:.2f}")
    print(f"  headline-anchored item14 (already in JSON) = {c['headline_item14']:.2f}")
    print(f"  diff = {item14_check - c['headline_item14']:.2f}  ({'MATCH' if abs(item14_check - c['headline_item14']) < 5 else 'MISMATCH'})")
    print()
