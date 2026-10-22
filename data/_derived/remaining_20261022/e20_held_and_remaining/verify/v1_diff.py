# -*- coding: utf-8 -*-
import json, subprocess, collections, sys
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant')
OUT = ROOT/'data/_derived/remaining_20261022/e20_held_and_remaining/verify'
def head(p):
    return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+p]).decode('utf-8'))
def live(p):
    return json.loads((ROOT/p).read_text(encoding='utf-8'))
old = head('PL_breakdown.json'); new = live('PL_breakdown.json')
def idx(rows):
    d = {}
    for r in rows:
        k = (r['원보험사코드'], r['항목번호'], r['공시분기'])
        assert k not in d, k
        d[k] = r
    return d
o, n = idx(old), idx(new)
lines = []
lines.append(f'rows old={len(o)} new={len(n)} added={len(set(n)-set(o))} removed={len(set(o)-set(n))}')
chg = []
fieldcnt = collections.Counter()
other_field = collections.Counter()
for k in sorted(set(o)&set(n), key=lambda x:(x[0],x[2],str(x[1]))):
    a, b = o[k], n[k]
    for f in set(a)|set(b):
        if a.get(f) != b.get(f):
            chg.append((k, f, a.get(f), b.get(f)))
            fieldcnt[f] += 1
lines.append('field change counts: '+str(dict(fieldcnt)))
bycq = collections.defaultdict(lambda: collections.Counter())
for k,f,a,b in chg:
    bycq[(k[0],k[2])][f] += 1
lines.append('company-quarters with changes: %d' % len(bycq))
for (c,q),cn in sorted(bycq.items(), key=lambda x:(x[0][0], x[0][1])):
    lines.append(f'  {c} {q}: {dict(cn)}')
comps = sorted({k[0] for k,_,_,_ in chg})
lines.append('companies: '+str(comps))
(OUT/'v1_diff_cells.json').write_text(json.dumps([[list(k),f,a,b] for k,f,a,b in chg], ensure_ascii=False, indent=0), encoding='utf-8')
# provenance
po = head('PL_breakdown_provenance.json'); pn = live('PL_breakdown_provenance.json')
lines.append('provenance types: %s %s' % (type(po).__name__, type(pn).__name__))
(OUT/'v1_diff.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines))
