# -*- coding: utf-8 -*-
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vx_reader as R
V = Path(__file__).parent
jobs = [('KR0069','FY2026_Q1'),('KR0068','FY2025_Q4'),('KR0068','FY2026_Q1'),('KR0087','FY2025_Q4'),('KR0104','FY2025_Q4'),('KR0072','FY2025_Q4'),('KR0070','FY2026_Q1'),('KR0071','FY2026_Q1'),('KR0094','FY2026_Q2'),('KR0083','FY2025_Q3'),('KR0082','FY2024_Q1'),('KR0032','FY2024_Q1')]
out = []
for code, fy in jobs:
    p = R.main_xml(code, fy)
    lines = p.read_text(encoding='utf-8', errors='replace').split('\n')
    out.append(f'### {code} {fy} {p.name}')
    n = 0
    for i, l in enumerate(lines, 1):
        t = re.sub(r'<[^>]+>', ' ', l)
        if re.search(r'재작성|재표시|소급', t) and re.search(r'포괄|기타포괄|보험금융|투자|비교|전기|OCI', t) and len(t.strip()) > 40:
            out.append(f'L{i}: ' + re.sub(r'\s+', ' ', t).strip()[:330])
            n += 1
            if n >= 10: break
    if n == 0: out.append('  (no matching restatement line)')
(V/'v10_restate.txt').write_text('\n'.join(out), encoding='utf-8')
print(len(out))
