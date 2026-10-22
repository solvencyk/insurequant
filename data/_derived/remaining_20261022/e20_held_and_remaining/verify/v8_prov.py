# -*- coding: utf-8 -*-
import json, subprocess, collections
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
def head(p): return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+p]).decode('utf-8'))
po = head('PL_breakdown_provenance.json'); pn = json.loads((ROOT/'PL_breakdown_provenance.json').read_text(encoding='utf-8'))
out = []
out.append('top keys old %s new %s' % (list(po)[:8], list(pn)[:8]))
def walk(a, b, path, acc, depth):
    if isinstance(a, dict) and isinstance(b, dict) and depth > 0:
        for k in sorted(set(a)|set(b), key=str):
            if k not in a: acc.append((path+[k], 'ADDED'))
            elif k not in b: acc.append((path+[k], 'REMOVED'))
            else: walk(a[k], b[k], path+[k], acc, depth-1)
    else:
        if a != b: acc.append((path, 'CHANGED'))
acc = []
walk(po, pn, [], acc, 3)
out.append('diff entries: %d' % len(acc))
for p, st in acc:
    out.append(f'{st}\t{p}')
(V/'v8_prov.txt').write_text('\n'.join(out), encoding='utf-8')
print(len(acc))
for k in list(po)[:6]:
    v = po[k]; print(k, type(v).__name__, (list(v)[:5] if isinstance(v, dict) else (len(v) if hasattr(v, '__len__') else v)))
