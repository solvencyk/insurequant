import math

R4 = [
    [1.0, 0.0, 0.25, 0.25],
    [0.0, 1.0, 0.25, 0.25],
    [0.25, 0.25, 1.0, 0.25],
    [0.25, 0.25, 0.25, 1.0],
]


def item15_calc(v17, v18, v19, v20, v21):
    V = [v17, v18, v19, v20]
    core = sum(R4[i][j] * V[i] * V[j] for i in range(4) for j in range(4))
    return math.sqrt(core) + v21


cases = {
    "KR0104 2023.1Q": dict(v17=897_970 / 100, v18=0.0, v19=1_813_184 / 100,
                            v20=1_016_519 / 100, v21=186_219 / 100,
                            headline_item15=28917.0),
    "KR0104 2023.2Q": dict(v17=899_705 / 100, v18=0.0, v19=1_619_170 / 100,
                            v20=946_394 / 100, v21=179_684 / 100,
                            headline_item14=21226.0, item22=556_520 / 100, item23=0.0),
}

for name, c in cases.items():
    print(f"=== {name} ===")
    item15 = item15_calc(c["v17"], c["v18"], c["v19"], c["v20"], c["v21"])
    print(f"  R4-computed item15 = {item15:.2f}")
    if "headline_item15" in c:
        print(f"  vs stored/trusted item15 = {c['headline_item15']}  diff={item15 - c['headline_item15']:.2f}")
    if "headline_item14" in c:
        item14_check = item15 - c["item22"] + c["item23"]
        print(f"  -> item14 = item15-22+23 = {item14_check:.2f}  vs stored item14={c['headline_item14']}  diff={item14_check - c['headline_item14']:.2f}")
    print()
