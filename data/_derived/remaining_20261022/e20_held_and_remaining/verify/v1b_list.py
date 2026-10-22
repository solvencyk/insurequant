# -*- coding: utf-8 -*-
import json
from pathlib import Path
V = Path('C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/verify')
chg = json.loads((V/'v1_diff_cells.json').read_text(encoding='utf-8'))
new = json.loads(Path('C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json').read_text(encoding='utf-8'))
nm = {(r['원보험사코드'], r['항목번호']): r['항목명'] for r in new}
out = []
for k,f,a,b in chg:
    out.append(f'{k[0]}\t{k[2]}\t{k[1]}\t{nm.get((k[0],k[1]))}\t{f}\t{a}\t{b}')
(V/'v1b_list.txt').write_text('\n'.join(out), encoding='utf-8')
