# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
import fill_market_subitems_to_disclosure as fm

# 당기(2026.2Q) Ⅲ.순자산가치: 충격전,평균회귀,금리상승,금리하락,금리평탄,금리경사 (백만원)
vals = [1251731, 1297480, 1090583, 1449792, 1277665, 1247304]
derived = fm.derive_irr(vals)
print("derive_irr(당기 vals) =", derived, "vs disclosed Ⅳ.금리위험액=115,460")
print("rel diff:", abs(derived-115460)/115460*100, "%")

eok_vals = [float(fm._to_eok(v, "백만원")) for v in vals]
print("eok_vals:", eok_vals)
print("derive_irr(eok_vals):", fm.derive_irr(eok_vals), "vs item36=1154.60")
