# -*- coding: utf-8 -*-
"""patch n02_is_read.py: also read FY2024_Q3 (2023.3Q prior column) for the single-quarter seam 3Q - 2Q and the vintage-equality proof (prior cum == live master)"""
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/kr0032_nhfire/n02_is_read.py")
s = p.read_text(encoding="utf-8")
a = 'for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2")):\n    d = O.read(CODE, q, fy)'
assert s.count(a) == 1
s = s.replace(a, 'for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2"), ("2023.3Q", "FY2024_Q3")):\n    d = O.read(CODE, q, fy)')
b = '''# OCI vectors (pass2 reader)
oci = {}
for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2")):'''
assert s.count(b) == 1
s = s.replace(b, '''# single quarter 2023.3Q (live 3Q cumulative - new 2Q cumulative) vs the printed prior 3M column of FY2024_Q3, and the vintage proof (FY2024_Q3 prior cumulative == live master 2023.3Q)
r3 = res["2023.3Q"]
seam3 = {}
for k in ("22", "23", "24"):
    live3 = live[("2023.3Q", int(k))]["값"]
    d_ = live3 - r2["vals_mn"][k]
    seam3[k] = dict(derived=d_, printed_3m=r3["vals_3m_mn"][k], diff=d_ - r3["vals_3m_mn"][k], prior_cum=r3["vals_mn"][k], live_master_3Q=live3, prior_cum_minus_master=r3["vals_mn"][k] - live3)
res["seam_3Q_minus_2Q"] = seam3
PR("single quarter 2023.3Q (live cum3Q - new cum2Q, 백만원) vs printed prior 3M of FY2024_Q3: " + "; ".join(f"{k}: {x['derived']:,.6f} vs {x['printed_3m']:,.6f} (diff {x['diff']:+.6f}; FY2024_Q3 prior cum - live master {x['prior_cum_minus_master']:+.6f})" for k, x in seam3.items()))
# OCI vectors (pass2 reader)
oci = {}
for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2"), ("2023.3Q", "FY2024_Q3")):''')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
