# -*- coding: utf-8 -*-
import json, subprocess, collections
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
def head(p): return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+p]).decode('utf-8'))
po = head('PL_breakdown_provenance.json'); pn = json.loads((ROOT/'PL_breakdown_provenance.json').read_text(encoding='utf-8'))
K = lambda e: (e['company_code'], e['quarter'], e['item_block'])
O = {K(e): e for e in po['cells']}; N = {K(e): e for e in pn['cells']}
assert len(O) == len(po['cells']) and len(N) == len(pn['cells'])
out = [f'blocks old {len(O)} new {len(N)} added {len(set(N)-set(O))} removed {len(set(O)-set(N))}']
ch = sorted(k for k in O if k in N and O[k] != N[k])
out.append(f'changed blocks {len(ch)}')
# master changed cq
chg = json.loads((V/'v1_diff_cells.json').read_text(encoding='utf-8'))
cq_cum = {(k[0], k[2]) for k, f, a, b in chg if f == '값'}
cq_all = {(k[0], k[2]) for k, f, a, b in chg}
chcq = {(k[0], k[1]) for k in ch}
out.append(f'master cq with 값 change: {len(cq_cum)}; any change: {len(cq_all)}; provenance cq changed: {len(chcq)}')
out.append('prov changed not in master-cum cq: %s' % sorted(chcq - cq_cum))
out.append('master-cum cq with no prov change: %s' % sorted(cq_cum - chcq))
# other keys differ in non-cells top-level
for k in sorted(set(po)|set(pn), key=str):
    if k in ('cells',): continue
    if po.get(k) != pn.get(k): out.append(f'top-level diff: {k}')
# detail
for k in ch:
    o, n = O[k], N[k]
    dif = [f for f in set(o)|set(n) if o.get(f) != n.get(f)]
    out.append(f'{k}: fields {dif}')
    for f in dif:
        if f == 'source_files':
            out.append('   old: ' + json.dumps(o.get(f), ensure_ascii=False)[:500])
            out.append('   new: ' + json.dumps(n.get(f), ensure_ascii=False)[:500])
        else:
            out.append(f'   {f}: {o.get(f)} -> {n.get(f)}')
(V/'v8_prov3.txt').write_text('\n'.join(out), encoding='utf-8')
print('\n'.join(out[:8]))
