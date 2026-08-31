# -*- coding: utf-8 -*-
import io, sys, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src")
import numpy as np
from solvency.validation.kics_json_rules import R4, MARKET_M, irr_derive_expected

# ---- confirmed core items (26.2Q), 억원 (from clean 220dpi page render, pdf p20/print p18) ----
item1, item2, item3 = 135316, 54815, 80500
item4 = 127185
item5,item6,item7,item8,item9,item10,item11 = 665,0,74102,0,-11787,65,64140
item12, item13 = 552, 71817
item14 = 72187
item15 = 99164
item16 = 37196
item17,item18,item19,item20,item21 = 69561,10829,34792,15076,6103
item22, item23 = 27111, 133
item25 = 133

print("R1 item1=item2+item3:", item2+item3, "vs", item1, "diff", item1-(item2+item3))
print("R2 item4=sum(5-11):", sum([item5,item6,item7,item8,item9,item10,item11]), "vs", item4)

V4 = np.array([item17,item18,item19,item20], dtype=float)
r4val = math.sqrt(V4 @ R4 @ V4) + item21
print("R4 item15 = sqrt(V'R4V)+item21:", r4val, "vs disclosed", item15, "diff", item15-r4val)

print("R5 item14=item15-item22+item23:", item15-item22+item23, "vs", item14)
print("R6 item16=sum(17-21)-item15:", sum([item17,item18,item19,item20,item21])-item15, "vs", item16)

item27 = item1/item14*100
item28 = item2/item14*100
print("item27 (computed, full precision):", item27)
print("item28 (computed, full precision):", item28)

# ---- market subs 36-40 (from clean page render, 백만원 -> 억원 /100) ----
item36 = 1032124/100
item37 = 3043506/100
item38 = 136121/100
item39 = 829305/100
item40 = 0.0
V19 = np.array([item36,item37,item38,item39,item40], dtype=float)
m19 = math.sqrt(V19 @ MARKET_M @ V19)
print(f"\n19_market: item36..40 = {V19.tolist()}")
print("sqrt(V'MARKET_M V) =", m19, "vs disclosed item19", item19, "diff", item19-m19)

# ---- IRR 41-46 (백만원 -> 억원) ----
item41 = 14286970/100
item42 = 14396739/100
item43 = 13199801/100
item44 = 15329887/100
item45 = 13937712/100
item46 = 14495557/100
vals = {41:item41,42:item42,43:item43,44:item44,45:item45,46:item46}
expected36 = irr_derive_expected(vals)
print(f"\n36_irr items 41-46 = {vals}")
print("irr_derive_expected(41-46) =", expected36, "vs disclosed item36", item36, "diff", item36-expected36)

# ---- TFI 47-52 (백만원 -> 억원) ----
item47_pre, item47_post = 1024419/100, 734308/100
item48 = 3609338/100
item49 = 7025609/100
item50 = 5481545/100
item51 = 8050028/100
item52 = 13531573/100
print(f"\nTFI: item47 pre/post={item47_pre}/{item47_post} item48={item48} item49={item49}")
print("axis F (pre) min(47,48)+49 =", min(item47_pre,item48)+item49, "vs item51", item51)
print("axis F (post) min(47,48)+49 =", min(item47_post,item48)+item49, "vs item51", item51)
print("axis B (pre) vs item3 =", min(item47_pre,item48)+item49, "vs item3", item3)
print("axis B (post) vs item3(mirrored=80500) =", min(item47_post,item48)+item49, "vs", item3)
print("item48 vs item14_pre*50% check:", item14*0.5, "vs item48", item48)
print("item52 vs item1:", item52, "vs", item1)
