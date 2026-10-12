# -*- coding: utf-8 -*-
"""One-off text patch of scripts/extract_chubb_d2_20261012.py (print the LRC+LIC-D1 difference instead of a literal check mark)."""
import io
p = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/extract_chubb_d2_20261012.py"
s = open(p, encoding="utf-8", newline="").read()
a = 'LRC {fmt(lrc)} + LIC {fmt(lic)} = D1 ✓  "'
b = 'LRC {fmt(lrc)} + LIC {fmt(lic)} - D1 = {lrc + lic - d1} won  "'
assert s.count(a) == 1
s = s.replace(a, b)
a2 = "D1_won=d1, SA_won=sa, D2_won=d1 + sa, LRC_won=lrc, LIC_won=lic,"
b2 = "D1_won=d1, SA_won=sa, D2_won=d1 + sa, LRC_won=lrc, LIC_won=lic, lrc_plus_lic_minus_d1_won=lrc + lic - d1,"
assert s.count(a2) == 1
s = s.replace(a2, b2)
open(p, "w", encoding="utf-8", newline="").write(s)
print("patched")
