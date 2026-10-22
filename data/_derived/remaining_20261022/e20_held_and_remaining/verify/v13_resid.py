# -*- coding: utf-8 -*-
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vx_reader as R
V = Path(__file__).parent
newm = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in json.loads((R.ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))}
out = []
for code, q, fy in (('KR0071', '2025.1Q', 'FY2026_Q1'), ('KR0068', '2024.4Q', 'FY2025_Q4'), ('KR0087', '2025.1Q', 'FY2026_Q1')):
    out.append(f'## {code} {q}: master items 24..32 (new 값): ' + str({i: newm[(code, q, i)]['값'] for i in range(24, 33)}))
    s = R.stmt(code, fy)[0]
    scale = 1e6 if (s['unit'] or '').startswith('원') else 1.0
    on = False
    for lab, ln, vals in s['rows']:
        if lab.replace(' ', '').startswith('기타포괄손익') and not on and ('(' in lab or lab.replace(' ', '') in ('기타포괄손익',)) : on = True
        xs = [v for c, v in vals]
        x = xs[3] if len(xs) >= 4 else (xs[1] if len(xs) >= 2 else None)
        v = R.num(x) if x else None
        if on:
            out.append(f'   L{ln} {lab} = {None if v is None else round(v/scale, 6)}')
        if lab.replace(' ', '').startswith('총포괄손익'): break
(V/'v13_resid.txt').write_text('\n'.join(out), encoding='utf-8')
