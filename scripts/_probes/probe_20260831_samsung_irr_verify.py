# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\sangwook.cho\Desktop\insurequant\scripts")
import fill_market_subitems_to_disclosure as fm

# order: 충격전, 평균회귀, 금리상승, 금리하락, 금리평탄, 금리경사 (백만원)
vals = [15691632, 15858496, 15863305, 14504781, 15692095, 15697182]
derived = fm.derive_irr(vals)
print("derive_irr =", derived, "vs disclosed Ⅳ.금리위험액=1,037,118")
print("rel diff:", abs(derived-1037118)/1037118*100, "%")
eok_vals = [float(fm._to_eok(v, "백만원")) for v in vals]
print("eok_vals:", eok_vals)
print("derive_irr(eok):", fm.derive_irr(eok_vals), "vs item36=10371.18")
