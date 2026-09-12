# -*- coding: utf-8 -*-
"""Investigation-only probe (writes nothing). Root-causes the KR1010(교보라이프플래닛)
2023.4Q item2(-19,236.643649) vs item3+item8(-14,538.659979) gap flagged in
data/_gold/pl_bridge_baseline.json ("생명장기손익 = 원수손익+재보험손익", class lob_sum_gap).

Source: 연결포괄손익계산서(제11(당)기), data/dart/FY2023_Q4/raw/
KR1010_교보라이프플래닛생명보험_20240328001012/20240328001012_00761.xml. Ⅱ.영업비용 has
SEVEN sub-lines that year (unlike 2024/2025.4Q's 2-line '1.보험영업수익/2.보험서비스비용'
layout -- see data/_gold/pl_bridge_baseline.json `_round_20260826b`), and the extraction only
ever captured "3.기타사업비용" for item16, missing the SEPARATE "7.기타영업비용" line entirely.

Result: item1(=item20-item17, top-down, statement-anchored, unchanged) exactly equals
item2(=item3+item8, canonical formula) + item15 - item16 ONLY once item16 = 3.기타사업비용 +
7.기타영업비용. Residual is 0.000000 to the microwon. This is what
scripts/build_pl_breakdown.py's `_GOLD_CELL_OVERRIDE[("KR1010","2023.4Q")]` entry (item2, item16)
now encodes."""
import sys

sys.stdout.reconfigure(encoding="utf-8")

# CFS(연결) 제11(당)기 = FY2023, 원 단위, from the raw table dump (see this probe's docstring).
svc_rev = 21978740944.0       # 1.보험서비스수익
svc_cost = 37876245249.0      # 1.보험서비스비용
re_rev = 3546756258.0         # 2.재보험서비스수익
re_cost = 2187911932.0        # 2.재보험서비스비용
oth_rev7 = 1926930607.0       # 7.기타영업수익 (item15)
oth_cost3 = 1933610508.0      # 3.기타사업비용 (old item16 -- only this was captured)
oth_cost7 = 4691303769.0      # 7.기타영업비용 (MISSING sub-line, the root cause)
op_loss = -22094366544.0      # Ⅲ.영업손실 (item20)
fin_rev_ins = 3307614492.0    # 3.보험금융수익
fin_cost_ins = 24525861357.0  # 4.보험금융비용 (-> item19)
interest_rev = 16242568503.0  # 4.이자수익
div_rev = 22784250.0          # 5.배당금수익
fv_gain = 3953501996.0        # 6.금융상품평가및처분이익
interest_cost = 508711622.0   # 5.이자비용
fv_loss = 1349619157.0        # 6.금융상품평가및처분손실

f = 1e-6  # 원 -> 백만원

item3 = (svc_rev - svc_cost) * f
item8 = (re_rev - re_cost) * f
item15 = oth_rev7 * f
item16_old = oth_cost3 * f
item16_new = (oth_cost3 + oth_cost7) * f
item19 = (fin_rev_ins - fin_cost_ins) * f
item18 = (interest_rev + div_rev + fv_gain - interest_cost - fv_loss) * f
item17 = item18 + item19
item20 = op_loss * f
item1 = item20 - item17
item2_canonical = item3 + item8

print(f"item3={item3:.6f}  item8={item8:.6f}  item15={item15:.6f}")
print(f"item16_old(3.기타사업비용만)={item16_old:.6f}")
print(f"item16_new(3.기타사업비용+7.기타영업비용)={item16_new:.6f}")
print(f"item17={item17:.6f}  item18={item18:.6f}  item19={item19:.6f}  item20={item20:.6f}")
print(f"item1(=item20-item17, master, unchanged)={item1:.6f}")
print(f"item2(=item3+item8, canonical)={item2_canonical:.6f}")

bridge_old = item2_canonical + item15 - item16_old
bridge_new = item2_canonical + item15 - item16_new
print(f"\nbridge OLD item16: item2+15-16_old={bridge_old:.6f}  gap vs item1={item1 - bridge_old:.6f}")
print(f"bridge NEW item16: item2+15-16_new={bridge_new:.6f}  gap vs item1={item1 - bridge_new:.6f}")
assert abs(item1 - bridge_new) < 1e-6, "bridge should close to the microwon"
print("\nOK -- bridge closes exactly once item16 includes the missing 7.기타영업비용 line.")
