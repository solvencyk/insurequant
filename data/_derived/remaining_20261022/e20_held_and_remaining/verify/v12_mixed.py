# -*- coding: utf-8 -*-
"""Blind-spot: within every changed cumulative block, do the NON-changed main items equal the same latest-comparative filing column (no mixed vintage)?"""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vx_reader as R
V = Path(__file__).parent
src = open(V/'v3_check_cum.py', encoding='utf-8').read()
ns = {}
exec("import re\nimport vx_reader as R\n" + src[src.index("STRIP = "):src.index("res_lines = []")], ns)
norm, LAB = ns['norm'], ns['LAB']
LAB = dict(LAB); LAB[21] = r'^영업외손익$'
newm = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in json.loads((R.ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))}
chg = json.loads((V/'v1_diff_cells.json').read_text(encoding='utf-8'))
cq = sorted({(k[0], k[2]) for k, f, a, b in chg if f == '값'})
def fy_for(q):
    y, qq = q.split('.'); return f'FY{int(y)+1}_Q{int(qq[0])}'
out = []; mism = 0; checked = 0
for code, q in cq:
    s = R.stmt(code, fy_for(q))[0]
    scale = 1e6 if (s['unit'] or '').startswith('원') else 1.0
    rows = []
    for lab, ln, vals in s['rows']:
        xs = [v for c, v in vals]
        x = xs[3] if len(xs) >= 4 else (xs[1] if len(xs) >= 2 else None)
        v = R.num(x) if x is not None else None
        rows.append((lab, v/scale if v is not None else None))
    # 영업외손익 for filings that print 영업외수익/영업외비용 separately
    for it, pat in LAB.items():
        r = newm.get((code, q, it))
        if r is None or r.get('값') is None: continue
        cand = [v for l, v in rows if re.search(pat, norm(l)) and v is not None][:1]
        if not cand and it == 21:
            a = [v for l, v in rows if norm(l) == '영업외수익' and v is not None][:1]; b = [v for l, v in rows if norm(l) == '영업외비용' and v is not None][:1]
            if a and b: cand = [a[0] - b[0]]
        if not cand:
            out.append(f'NOLABEL\t{code} {q} item{it} master={r["값"]}'); continue
        checked += 1
        d = r['값'] - cand[0]
        tol = 1.0
        if abs(d) > tol:
            mism += 1
            out.append(f'MISMATCH\t{code} {q} item{it}\tmaster={r["값"]}\tlatest-comparative={cand[0]}\tdiff={d:.4f}')
        elif abs(d) > 1e-5:
            out.append(f'rounding\t{code} {q} item{it}\tdiff={d:.6f}')
out.append(f'checked {checked} main-item cells in {len(cq)} blocks; MISMATCH(>1.0 백만원) = {mism}')
(V/'v12_mixed.txt').write_text('\n'.join(out), encoding='utf-8')
print(out[-1])
