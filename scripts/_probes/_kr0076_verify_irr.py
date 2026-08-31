# -*- coding: utf-8 -*-
import sys, io
sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from solvency.validation.kics_json_rules import irr_derive_expected

# raw MD 백만원 values (line 677-698, 당기 2026.2Q, "Ⅲ. 순자산가치" row)
raw = {
    41: 761131,  # 충격전
    42: 796525,  # 평균회귀
    43: 627461,  # 금리상승
    44: 858921,  # 금리하락
    45: 742007,  # 금리평탄
    46: 772508,  # 금리경사
}
# convert to 억원 (/100) as stored elsewhere in the master
vals_eok = {k: v / 100.0 for k, v in raw.items()}
for k, v in vals_eok.items():
    print(f"item{k} = {v:.2f}")

expected36 = irr_derive_expected(vals_eok)
print(f"\nexpected item36 (derived from 41-46) = {expected36:.4f}")
print(f"stored item36                         = 996.36")
print(f"diff = {expected36 - 996.36:.4f}")
