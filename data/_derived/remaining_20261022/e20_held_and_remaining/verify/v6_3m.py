# -*- coding: utf-8 -*-
"""Compare master 값_당분기 (2Q cells, KR0083 3Q, KR0082 2Q) with the 3-month PRIOR column printed in the next-year filing."""
import sys, re, json, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vx_reader as R
V = Path(__file__).parent
exec(open(V/'v3_check_cum.py', encoding='utf-8').read().split("res_lines = []")[0].split("chg = json")[0])  # imports only
chg = json.loads((V/'v1_diff_cells.json').read_text(encoding='utf-8'))
newm = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in json.loads((R.ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))}
src = open(V/'v3_check_cum.py', encoding='utf-8').read()
# reuse helpers
ns = {}
code_helpers = src[src.index("STRIP = "):src.index("res_lines = []")]
exec("import re\nimport vx_reader as R\n" + code_helpers, ns)
norm, LAB = ns['norm'], ns['LAB']
def fy_for(q):
    y, qq = q.split('.'); return f'FY{int(y)+1}_Q{int(qq[0])}'
cells = sorted({(k[0], k[2], k[1]) for k, f, a, b in chg if k[2].endswith('2Q') or (k[0] == 'KR0083' and k[2] == '2024.3Q')}, key=lambda x: (x[0], x[1], str(x[2])))
out = []; bad = 0
for code, q, item in cells:
    ss = R.stmt(code, fy_for(q)); s = ss[0]
    scale = 1e6 if (s['unit'] or '').startswith('원') else 1.0
    rows = []
    for lab, ln, vals in s['rows']:
        xs = [v for c, v in vals]
        v3 = R.num(xs[2]) if len(xs) >= 4 and R.num(xs[2]) is not None else None
        rows.append((lab, ln, v3/scale if v3 is not None else None))
    d = newm[(code, q, item)].get('값_당분기')
    cand = None
    if item in LAB:
        cand = [v for l, ln, v in rows if re.search(LAB[item], norm(l)) and v is not None]
        cand = cand[:1]
    elif item == 18:
        r17 = [v for l, ln, v in rows if re.search(LAB[17], norm(l)) and v is not None][0]
        fin = [(l, v) for l, ln, v in rows if re.search(r'(재)?보험금융(수익|비용)', norm(l)) and v is not None]
        inc = sum(v for l, v in fin if '수익' in l); exp = sum(v for l, v in fin if '비용' in l)
        cand = [r17 - (inc - exp)]
    elif item == 19:
        fin = [(l, v) for l, ln, v in rows if re.search(r'(재)?보험금융(수익|비용)', norm(l)) and v is not None]
        cand = [sum(v for l, v in fin if '수익' in l) - sum(v for l, v in fin if '비용' in l)]
    else:
        hit = [v for l, ln, v in rows if v is not None and d is not None and abs(v - d) < 1e-5]
        cand = hit[:1] if hit else []
        if item == 32: cand = ['(residual)']
    ok = cand and cand[0] != '(residual)' and d is not None and abs(cand[0] - d) < 1e-5
    st = 'OK' if ok else ('RESID' if cand == ['(residual)'] else 'DIFF')
    if st == 'DIFF': bad += 1
    out.append(f'{st}\t{code} {q} item{item}\t값_당분기={d}\tprinted3M={cand}')
out.append(f'DIFF count={bad} of {len(cells)}')
(V/'v6_3m.txt').write_text('\n'.join(out), encoding='utf-8')
print(out[-1])
