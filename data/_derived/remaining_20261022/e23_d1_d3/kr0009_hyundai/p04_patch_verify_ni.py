# -*- coding: utf-8 -*-
"""patch the old-layout control: the net-income row of the old layout has no usable label, so item 24 is checked as 22 - 23 of the printed pre-tax profit and tax lines"""
from pathlib import Path
p = Path(__file__).resolve().parent / "kr0009_verify.py"
s = p.read_text(encoding="utf-8")
a = '        chk = [("영업이익", 20, None), ("법인세비용차감전순이익", 22, 50.0), ("법인세비용", 23, 50.0), ("분기순이익" if q == "2023.1Q" else "반기순이익", 24, 50.0)]\n'
b = '        chk = [("영업이익", 20, None), ("법인세비용차감전순이익", 22, 50.0), ("법인세비용", 23, 50.0)]\n'
assert s.count(a) == 1
s = s.replace(a, b)
a2 = '        try:\n            n4 = old_value(rows, un, "보험계약마진상각")[cum_idx]\n'
b2 = ('        try:\n'
      '            v22 = old_value(rows, un, "법인세비용차감전순이익")[cum_idx][2]\n'
      '            v23 = old_value(rows, un, "법인세비용")[cum_idx][2]\n'
      '            m24 = LIVE[(CODE, 24, q)]["값"]\n'
      '            say(f"      i24 (22 - 23 of the printed lines) = {r6(v22 - v23)} | live master {m24} | diff {m24 - (v22 - v23):+.3f} ({\'within the 경영공시 억원 rounding\' if abs(m24 - (v22 - v23)) <= 50.0 else \'OUTSIDE\'})")\n'
      '            if abs(m24 - (v22 - v23)) > 50.0:\n'
      '                problem(f"A {q}", f"item 24 original {v22 - v23} vs live master {m24}")\n'
      '        except RuntimeError as e:\n'
      '            say(f"      (item 24 control not readable: {e})")\n'
      '        try:\n            n4 = old_value(rows, un, "보험계약마진상각")[cum_idx]\n')
assert s.count(a2) == 1
s = s.replace(a2, b2)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
