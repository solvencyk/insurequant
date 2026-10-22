# -*- coding: utf-8 -*-
import json, subprocess, collections
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
def head(p): return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+p]).decode('utf-8'))
po = head('PL_breakdown_provenance.json'); pn = json.loads((ROOT/'PL_breakdown_provenance.json').read_text(encoding='utf-8'))
out = []
c0 = po['cells']; c1 = pn['cells']
out.append(f'cells type {type(c0).__name__} old {len(c0)} new {len(c1)}')
if isinstance(c0, list):
    out.append('sample: ' + json.dumps(c0[0], ensure_ascii=False)[:600])
    keyf = lambda e: json.dumps({k: e[k] for k in e if k in ('원보험사코드','공시분기','항목번호','code','quarter','item','block','field')}, sort_keys=True, ensure_ascii=False)
    out.append('keys of entry: ' + str(list(c0[0])))
else:
    out.append('sample keys: ' + str(list(c0)[:3]))
    k0 = list(c0)[0]; out.append('sample: ' + k0 + ' -> ' + json.dumps(c0[k0], ensure_ascii=False)[:600])
out.append('merge_note: ' + json.dumps(pn['merge_note_20261022_e20_latest_comparative_held_remaining'], ensure_ascii=False)[:1500])
(V/'v8_prov2.txt').write_text('\n'.join(out), encoding='utf-8')
