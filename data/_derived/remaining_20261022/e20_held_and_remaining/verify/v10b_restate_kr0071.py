# -*- coding: utf-8 -*-
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vx_reader as R
V = Path(__file__).parent
out = []
for code, fy in [('KR0071','FY2026_Q1'),('KR0071','FY2026_Q2'),('KR0071','FY2025_Q4'),('KR0094','FY2026_Q1'),('KR0094','FY2026_Q2'),('KR0032','FY2024_Q1'),('KR0082','FY2024_Q1'),('KR0082','FY2024_Q2')]:
    p = R.main_xml(code, fy)
    if p is None: out.append(f'### {code} {fy} no file'); continue
    lines = p.read_text(encoding='utf-8', errors='replace').split('\n')
    out.append(f'### {code} {fy} {p.name}')
    n = 0
    pat = r'일탈회계|계약자지분조정|질의회신|회계정책의? ?변경|분류.{0,6}변경|재분류|오류수정|비교표시'
    for i, l in enumerate(lines, 1):
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', l)).strip()
        if len(t) > 60 and re.search(pat, t) and re.search(r'재작성|소급|변경|재분류', t) and re.search(r'기타포괄|포괄손익|비교|전기|보험손익|투자손익|사업비', t):
            out.append(f'L{i}: ' + t[:300]); n += 1
            if n >= 8: break
    if n == 0: out.append('  (none)')
(V/'v10b_restate_kr0071.txt').write_text('\n'.join(out), encoding='utf-8')
