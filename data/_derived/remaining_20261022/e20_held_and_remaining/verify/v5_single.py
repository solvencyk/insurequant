# -*- coding: utf-8 -*-
"""Check 4: single-quarter identity for every changed company/quarter/item (new master) + seam registry coverage."""
import json, subprocess, collections
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant')
V = Path(__file__).parent
def head(p): return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+p]).decode('utf-8'))
oldm = head('PL_breakdown.json'); newm = json.loads((ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))
gold = json.loads((ROOT/'data/_gold/user_pl_cells.json').read_text(encoding='utf-8'))
oldgold = head('data/_gold/user_pl_cells.json')
K = lambda r: (r['원보험사코드'], r['항목번호'], r['공시분기'])
O = {K(r): r for r in oldm}; N = {K(r): r for r in newm}
chg = json.loads((V/'v1_diff_cells.json').read_text(encoding='utf-8'))
nullset = {tuple(c) for c in gold['null_dangi']['cells']}
setd = {(c[0], c[1], c[2]): c[3] for c in gold['set_dangi']['cells']}
def prevq(q):
    y, n = q.split('.'); n = int(n[0])
    return None if n == 1 else f'{y}.{n-1}Q'
cells = sorted({(k[0], k[1], k[2]) for k, f, a, b in chg}, key=lambda x: (x[0], x[2], str(x[1])))
out = []; cnt = collections.Counter()
for code, item, q in cells:
    n = N[(code, item, q)]; o = O[(code, item, q)]
    pq = prevq(q)
    v = n.get('값'); d = n.get('값_당분기')
    if pq is None:
        exp = v; src = 'Q1(=cum)'
    else:
        pn = N.get((code, item, pq)); po = O.get((code, item, pq))
        exp = None if (pn is None or pn.get('값') is None or v is None) else v - pn['값']
        src = f'{q}-{pq}'
    # which cumulatives are new vintage?
    cur_new = (code, item, q) in {(k[0], k[1], k[2]) for k, f, a, b in chg if f == '값'}
    prv_new = pq is not None and (code, item, pq) in {(k[0], k[1], k[2]) for k, f, a, b in chg if f == '값'}
    key = (code, q, item)
    if key in nullset:
        st = 'NULL-REG' if d is None else 'NULL-REG-BUT-VALUE'
    elif key in setd:
        st = 'SET-REG' if (d is not None and abs(d - setd[key]) < 1e-9) else 'SET-REG-MISMATCH'
    elif d is None and exp is None:
        st = 'BOTH-NULL'
    elif d is not None and exp is not None and abs(d - exp) < 1e-5:
        st = 'DERIVED-OK'
    else:
        st = 'MISMATCH'
    # seam heuristic: cur_new xor prv_new  (Q1 has no prev)
    seam = (pq is not None) and (cur_new != prv_new)
    cnt[(st, 'seam' if seam else 'same')] += 1
    out.append(f'{st}\t{"SEAM" if seam else "same"}\t{code} {q} item{item}\tcur_new={cur_new} prev_new={prv_new}\t값_당분기={d}\tderived={exp}\tset={setd.get(key)}')
out.append(str(dict(cnt)))
(V/'v5_single.txt').write_text('\n'.join(out), encoding='utf-8')
print(dict(cnt))
