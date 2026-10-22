# -*- coding: utf-8 -*-
import json, subprocess
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
old = json.loads((V/'head_files'/'PL_breakdown.json').read_text(encoding='utf-8')); new = json.loads((ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))
def cnt(rows, it):
    r = [x for x in rows if x['항목번호'] == it]
    return len(r), sum(1 for x in r if x.get('값_당분기') is None), sum(1 for x in r if x.get('값') is None)
out = []
for it in (25, 26, 31, 17, 24):
    out.append(f'item{it}: rows/null_dangi/null_cum old={cnt(old, it)} new={cnt(new, it)}')
# the gate counts "within tol" = len(pl_dangi) - n_skip - flagged, where pl_dangi includes None-dangi rows
a = {(r['원수사명'], r['공시분기']): r.get('값_당분기') for r in new if r['항목번호'] == 25}
out.append(f'item25 pl_dangi dict size {len(a)}; None entries {sum(1 for v in a.values() if v is None)} (these are counted into the gate\'s "비교가능 N건은 tol 이내")')
(V/'v14_nullcount.txt').write_text('\n'.join(out), encoding='utf-8'); print('\n'.join(out))
