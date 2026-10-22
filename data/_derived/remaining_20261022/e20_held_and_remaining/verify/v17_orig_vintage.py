# -*- coding: utf-8 -*-
"""Is the OLD (HEAD) master value == the ORIGINAL filing's own current-period cumulative print?  (proves the move is a vintage change, not repair of an earlier mis-extraction)"""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vx_reader as R
V = Path(__file__).parent
src = open(V/'v3_check_cum.py', encoding='utf-8').read()
ns = {}
exec("import re\nimport vx_reader as R\n" + src[src.index("STRIP = "):src.index("res_lines = []")], ns)
norm, LAB = ns['norm'], ns['LAB']
chg = json.loads((V/'v1_diff_cells.json').read_text(encoding='utf-8'))
cum = {(k[0], k[2], k[1]): (a, b) for k, f, a, b in chg if f == '값'}
def fy_same(q):
    y, qq = q.split('.'); return f'FY{int(y)}_Q{int(qq[0])}'
out = []; ok = bad = skip = 0
cache = {}
for (code, q, item), (old, new) in sorted(cum.items(), key=lambda x: (x[0][0], x[0][1], str(x[0][2]))):
    if q.startswith('2023.'):
        skip += 1; out.append(f'SKIP(2023 flat layout; DB생명 done separately)\t{code} {q} item{item}'); continue
    fy = fy_same(q)
    if (code, fy) not in cache: cache[(code, fy)] = R.stmt(code, fy)
    ss = cache[(code, fy)]
    if not ss: skip += 1; out.append(f'NOSTMT\t{code} {q} {fy}'); continue
    s = ss[0]; scale = 1e6 if (s['unit'] or '').startswith('원') else 1.0
    rows = []
    for lab, ln, vals in s['rows']:
        xs = [v for c, v in vals]
        x = xs[1] if len(xs) >= 4 else (xs[0] if len(xs) >= 1 else None)
        v = R.num(x) if x else None
        rows.append((lab, v/scale if v is not None else None))
    if item in LAB:
        c = [v for l, v in rows if re.search(LAB[item], norm(l)) and v is not None][:1]
    elif item in (26, 27, 29, 32, 18, 19):
        if item == 32 or item in (18, 19):
            c = []   # derived: judged by neighbours
        else:
            c = [v for l, v in rows if v is not None and abs(v - old) < 1.0][:1]
    else: c = []
    if not c:
        skip += 1; out.append(f'DERIVED/NA\t{code} {q} item{item}\told={old}'); continue
    tol = 1.0
    st = 'OK' if abs(c[0] - old) <= tol else 'DIFF'
    if st == 'OK': ok += 1
    else: bad += 1
    out.append(f'{st}\t{code} {q} item{item}\told master={old}\toriginal filing print={c[0]}\tdiff={old-c[0]:.4f}')
out.append(f'old==original print: ok={ok} diff={bad} not-testable={skip}')
(V/'v17_orig_vintage.txt').write_text('\n'.join(out), encoding='utf-8'); print(out[-1])
