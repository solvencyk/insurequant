# -*- coding: utf-8 -*-
import sys, re
from pathlib import Path
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/verify')
import vx_reader as R
V = Path(R.__file__).parent
jobs = [('KR0032','FY2024_Q1'),('KR0032','FY2023_Q1'),
 ('KR0068','FY2025_Q4'),('KR0068','FY2026_Q1'),('KR0068','FY2026_Q2'),('KR0068','FY2025_Q1'),('KR0068','FY2025_Q2'),('KR0068','FY2024_Q4'),
 ('KR0069','FY2026_Q1'),('KR0069','FY2026_Q2'),('KR0069','FY2025_Q1'),('KR0069','FY2025_Q2'),
 ('KR0070','FY2026_Q1'),('KR0070','FY2026_Q2'),('KR0070','FY2025_Q1'),('KR0070','FY2025_Q2'),
 ('KR0071','FY2026_Q1'),('KR0071','FY2026_Q2'),('KR0071','FY2025_Q1'),('KR0071','FY2025_Q2'),
 ('KR0072','FY2025_Q4'),('KR0072','FY2024_Q4'),
 ('KR0082','FY2024_Q1'),('KR0082','FY2024_Q2'),
 ('KR0083','FY2025_Q3'),('KR0083','FY2024_Q3'),
 ('KR0087','FY2025_Q4'),('KR0087','FY2026_Q1'),('KR0087','FY2026_Q2'),('KR0087','FY2025_Q1'),('KR0087','FY2025_Q2'),('KR0087','FY2024_Q4'),
 ('KR0094','FY2026_Q2'),('KR0094','FY2025_Q2'),
 ('KR0104','FY2025_Q4'),('KR0104','FY2026_Q1'),('KR0104','FY2026_Q2'),('KR0104','FY2025_Q1'),('KR0104','FY2025_Q2'),('KR0104','FY2024_Q4')]
if len(sys.argv) > 1:
    jobs = [tuple(a.split(':')) for a in sys.argv[1:]]
out = []
for code, fy in jobs:
    try:
        ss = R.stmt(code, fy)
    except Exception as e:
        out.append(f'### {code} {fy} ERROR {e}'); continue
    if not ss: out.append(f'### {code} {fy} NO STATEMENT'); continue
    for s in ss:
        out.append(f'### {code} {fy} | {s["title"]} | line {s["title_line"]} | unit {s["unit"]} | {Path(s["path"]).name}')
        for lab, l, vals in s['rows']:
            tag = ' ; '.join(f"{(c or '-').split('_')[0]}={v}" for c, v in vals)
            out.append(f'{l} | {lab} | {tag}')
(V/'v2_dump.txt').write_text('\n'.join(out), encoding='utf-8')
print(len(out))
