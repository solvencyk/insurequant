# -*- coding: utf-8 -*-
"""patch the verifier's old-layout control: accept the old-layout net-income label variants (분기순이익 / 반기순이익 / 당기순이익)"""
from pathlib import Path
p = Path(__file__).resolve().parent / "kr0009_verify.py"
s = p.read_text(encoding="utf-8")
a = '        chk = [("영업이익", 20, None), ("법인세비용차감전순이익", 22, 50.0), ("법인세비용", 23, 50.0), ("당기순이익", 24, 50.0)]\n'
b = '        chk = [("영업이익", 20, None), ("법인세비용차감전순이익", 22, 50.0), ("법인세비용", 23, 50.0), ("분기순이익" if q == "2023.1Q" else "반기순이익", 24, 50.0)]\n'
assert s.count(a) == 1
s = s.replace(a, b)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
