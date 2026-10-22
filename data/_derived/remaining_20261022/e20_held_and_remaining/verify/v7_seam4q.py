# -*- coding: utf-8 -*-
"""For the 2024.4Q null_dangi cells: is the 9M master cumulative the same vintage as the new annual?  Compare master 2024.3Q with FY2025_Q3 prior 9M."""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vx_reader as R
V = Path(__file__).parent
src = open(V/'v3_check_cum.py', encoding='utf-8').read()
ns = {}
exec("import re\nimport vx_reader as R\n" + src[src.index("STRIP = "):src.index("res_lines = []")], ns)
norm, LAB = ns['norm'], ns['LAB']
newm = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in json.loads((R.ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))}
gold = json.loads((R.ROOT/'data/_gold/user_pl_cells.json').read_text(encoding='utf-8'))
cells = [tuple(c) for c in gold['null_dangi']['cells'] if c[1] == '2024.4Q' and c[0] in ('KR0068','KR0072','KR0087','KR0104')]
out = []
for code, q, item in cells:
    ss = R.stmt(code, 'FY2025_Q3'); s = ss[0]
    scale = 1e6 if (s['unit'] or '').startswith('원') else 1.0
    rows = []
    for lab, ln, vals in s['rows']:
        xs = [v for c, v in vals]
        v = R.num(xs[3]) if len(xs) >= 4 and R.num(xs[3]) is not None else None
        rows.append((lab, ln, v/scale if v is not None else None))
    m9 = newm[(code, '2024.3Q', item)].get('값'); a_new = newm[(code, '2024.4Q', item)].get('값')
    if item in LAB:
        c = [v for l, ln, v in rows if re.search(LAB[item], norm(l)) and v is not None][:1]
    else:
        c = [v for l, ln, v in rows if v is not None and m9 is not None and abs(v-m9) < 0.5][:1]
        if not c and item == 32: c = ['resid']
        if not c:
            c = [v for l, ln, v in rows if v is not None and item in (26,29) and re.search('채무|지분|금융자산|유가증권', l)][:1] if item in (26, 29) else []
    out.append(f'{code} item{item}\t9M master={m9}\tFY2025_Q3 prior 9M={c}\tsame={bool(c) and c[0] != "resid" and m9 is not None and abs(c[0]-m9) < 1e-5}\tannual_new={a_new}')
(V/'v7_seam4q.txt').write_text('\n'.join(out), encoding='utf-8')
print(len(out))
