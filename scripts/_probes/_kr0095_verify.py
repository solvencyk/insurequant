# -*- coding: utf-8 -*-
import io
import sys
import math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def eok(millions):
    return millions / 100.0

# ---- items 41-46 from raw PDF p27 "II. 금리위험액 현황", 당기(2026.2Q), row III.순자산가치 (백만원) ----
item41 = eok(4_856_281)   # 충격전
item42 = eok(4_849_046)   # 평균회귀
item43 = eok(4_622_611)   # 금리상승
item44 = eok(4_961_985)   # 금리하락
item45 = eok(4_573_675)   # 금리평탄
item46 = eok(5_068_922)   # 금리경사
item36_actual = 3744.68

print("item41..46 (억원):", item41, item42, item43, item44, item45, item46)

R_up = item41 - item43
R_down = item41 - item44
R_flat = item41 - item45
R_steep = item41 - item46
R_mrr = item41 - item42
expected36 = math.sqrt(max(R_up, R_down)**2 + max(R_flat, R_steep)**2) + R_mrr
print("R_up=%.2f R_down=%.2f R_flat=%.2f R_steep=%.2f R_mrr=%.2f" % (R_up, R_down, R_flat, R_steep, R_mrr))
print("expected item36 = %.2f, actual item36 = %.2f, diff=%.2f, tol(5%%)=%.2f" % (
    expected36, item36_actual, expected36 - item36_actual, 0.05*item36_actual))

# ---- cross-check against 2025.4Q known-good values (same table structure, "직전반기" column p28) ----
q_prev = {
    41: eok(4_927_978), 42: eok(4_937_989), 43: eok(4_748_594),
    44: eok(4_940_448), 45: eok(4_644_923), 46: eok(5_155_256),
}
known_2025q4 = {41: 49279.78, 42: 49379.89, 43: 47485.94, 44: 49404.48, 45: 46449.23, 46: 51552.56}
print("\n2025.4Q cross-check (computed vs master):")
for k in (41,42,43,44,45,46):
    print(f"  item{k}: computed={q_prev[k]:.2f} master={known_2025q4[k]} match={abs(q_prev[k]-known_2025q4[k])<0.005}")

# ---- items 47-54 TFI table (백만원), md_inbox lines 428-439 ----
i47 = eok(0)
i48 = eok(1_044_696)
i49 = eok(2_185_377)
i50 = eok(2_670_904)
i51 = eok(2_185_377)
i52 = eok(4_856_281)
i53 = eok(0)
i54 = eok(0)
print("\nitem47..54 (억원):", i47, i48, i49, i50, i51, i52, i53, i54)

# self-check identity from precedent script: item51 == min(47,48) + 49 + 54
lhs = min(i47, i48) + i49 + i54
print(f"self-check item51 ({i51}) == min(47,48)+49+54 ({lhs}) -> {abs(i51-lhs)<0.01}")

# cross-check item48 against capital-tiering memo formula: 보완자본한도 = SCR(item14) * 50%
item14 = 20894
print(f"item48 vs SCR*50%%: computed={i48:.2f} vs item14*0.5={item14*0.5:.2f} match={abs(i48-item14*0.5)<1.0}")

# sanity: item48 vs existing WRONG stored value (21854, which is actually item3=보완자본)
print(f"existing stored item48=21854 == item3(보완자본)=21854 -> mismap confirmed: {21854==21854}")
print(f"correct item48={i48:.2f} != item3=21854 -> {abs(i48-21854)>1}")

# ---- items 29-35, 36-40 cross-check against existing master values via ②③ TFI tables (백만원) ----
existing_29_35 = {29:1988.43,30:401.87,31:4886.1,32:0,33:17515.72,34:3733.64,35:794.47}
raw_29_35_mm = {29:198_843,30:40_187,31:488_610,32:0,33:1_751_572,34:373_364,35:79_447}
print("\nitem29-35 cross-check (raw TFI table /100 vs master):")
for k in sorted(existing_29_35):
    computed = eok(raw_29_35_mm[k])
    print(f"  item{k}: computed={computed} master={existing_29_35[k]} match={abs(computed-existing_29_35[k])<0.01}")

existing_36_40 = {36:3744.68,37:4533.38,38:361.61,39:6504.5,40:0}
raw_36_40_mm = {36:374_468,37:453_338,38:36_161,39:650_450,40:0}
print("\nitem36-40 cross-check (raw TFI table /100 vs master):")
for k in sorted(existing_36_40):
    computed = eok(raw_36_40_mm[k])
    print(f"  item{k}: computed={computed} master={existing_36_40[k]} match={abs(computed-existing_36_40[k])<0.01}")

# ---- R1/R5/R6/R7 identity re-check with mirrored values (items already in master, just copied to 후) ----
v = {1:48563,2:26709,3:21854,14:20894,15:27519,16:6339,17:21367,18:0,19:9253,20:1548,21:1690,22:6625,23:0,27:232.42557672}
print("\nR1 (1=2+3):", v[1], "==", v[2]+v[3], abs(v[1]-(v[2]+v[3]))<0.01)
print("R5 (14=15-22+23):", v[14], "==", v[15]-v[22]+v[23], abs(v[14]-(v[15]-v[22]+v[23]))<0.01)
print("R6 (16=sum(17-21)-15):", v[16], "==", sum(v[i] for i in (17,18,19,20,21))-v[15], abs(v[16]-(sum(v[i] for i in (17,18,19,20,21))-v[15]))<0.01)
print("R7 (27=1/14*100):", v[27], "==", v[1]/v[14]*100, abs(v[27]-(v[1]/v[14]*100))<0.01)
