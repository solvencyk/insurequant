# -*- coding: utf-8 -*-
import json, subprocess, collections
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant')
V = Path(__file__).parent
old = json.loads(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:data/_gold/user_pl_cells.json']).decode('utf-8'))
new = json.loads((ROOT/'data/_gold/user_pl_cells.json').read_text(encoding='utf-8'))
K = lambda e: (e['원보험사코드'], e['공시분기'], e['항목번호'])
od = {K(e): e for e in old['set']}; nd = {K(e): e for e in new['set']}
assert len(od) == len(old['set']) and len(nd) == len(new['set'])
out = []
added = sorted(set(nd)-set(od), key=str); removed = sorted(set(od)-set(nd), key=str); common = sorted(set(od)&set(nd), key=str)
changed = [k for k in common if od[k] != nd[k]]
out.append(f'set: old {len(od)} new {len(nd)} added {len(added)} removed {len(removed)} changed-existing {len(changed)}')
out.append('removed: %s' % removed)
for k in changed:
    o, n = od[k], nd[k]
    out.append(f'CHANGED {k}: old 값={o.get("값")} was={o.get("was")} estimate={o.get("estimate")} | new 값={n.get("값")} was={n.get("was")}')
    out.append('   old note: ' + str(o.get('note'))[:400])
    diffk = [f for f in set(o)|set(n) if o.get(f) != n.get(f)]
    out.append('   fields changed: %s' % diffk)
# added grouped
g = collections.Counter((k[0], k[1]) for k in added)
out.append('added by (code,quarter): %s' % dict(g))
# added entries' note presence + whether any added entry duplicates master value
for sec in ('null_dangi','set_dangi'):
    oc = {tuple(c[:3]) if sec=='null_dangi' else tuple(c[:3]) for c in old[sec]['cells']}
    nc = {tuple(c[:3]) for c in new[sec]['cells']}
    out.append(f'{sec}: old {len(oc)} new {len(nc)} added {len(nc-oc)} removed {len(oc-nc)}')
    out.append('  removed: %s' % sorted(oc-nc, key=str))
    out.append('  added: %s' % sorted(nc-oc, key=str))
# other top-level key differences (nonlisted)
for sec in ('null_dangi','set_dangi'):
    ok = {k:v for k,v in old[sec].items() if k != 'cells'}; nk = {k:v for k,v in new[sec].items() if k != 'cells'}
    out.append(f'{sec} non-cell keys changed: {ok != nk}')
(V/'v4_gold_diff.txt').write_text('\n'.join(out), encoding='utf-8')
json.dump({'changed': [list(k) for k in changed], 'added': [list(k) for k in added]}, (V/'v4_gold_keys.json').open('w', encoding='utf-8'))
