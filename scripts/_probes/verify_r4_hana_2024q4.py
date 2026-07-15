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


# audit-report style (단위: 천원) -> /100000 to 억원
def to_eok(thousand_won):
    return thousand_won / 100_000


# 전 (pre)
v_pre = [to_eok(289_550_527), to_eok(0), to_eok(246_346_234), to_eok(154_877_709)]
item21_pre = to_eok(36_485_031)
item15_pre_calc = item15_calc(v_pre, item21_pre)
print(f"PRE: computed item15 = {item15_pre_calc:.2f}  (raw states Ⅰ.기본요구자본 전 = {to_eok(532_143_333):.2f})")

# 후 (post)
v_post = [to_eok(200_189_811), to_eok(0), to_eok(200_345_315), to_eok(154_877_709)]
item21_post = to_eok(36_485_031)
item15_post_calc = item15_calc(v_post, item21_post)
print(f"POST: computed item15 = {item15_post_calc:.2f}  (raw states Ⅰ.기본요구자본 후 = {to_eok(430_530_508):.2f})")
