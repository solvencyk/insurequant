# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
old = json.loads((V/'head_files'/'user_pl_cells.json').read_text(encoding='utf-8'))
new = json.loads((ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))
oldm = json.loads((V/'head_files'/'PL_breakdown.json').read_text(encoding='utf-8'))
N = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in new}; O = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in oldm}
newgold = json.loads((ROOT/'data/_gold/user_pl_cells.json').read_text(encoding='utf-8'))
nkeys = {tuple(c[:3]) for c in newgold['set_dangi']['cells']}
out = []
for c in old['set_dangi']['cells']:
    k = tuple(c[:3])
    if k in nkeys: continue
    n = N[k]; o = O[k]
    out.append(f'removed set_dangi {k}: registry printed 3M={c[3]} | HEAD master 값_당분기={o["값_당분기"]} | NEW master 값_당분기={n["값_당분기"]} | diff new-vs-printed={n["값_당분기"]-c[3]:.9f}')
(V/'v16_removed_setdangi.txt').write_text('\n'.join(out), encoding='utf-8'); print('\n'.join(out))
