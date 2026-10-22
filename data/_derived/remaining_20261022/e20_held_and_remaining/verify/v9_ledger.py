# -*- coding: utf-8 -*-
import json, subprocess
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
def head(p): return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+p]).decode('utf-8'))
led0 = head('data/_gold/gold_overlay_ledger.json'); led1 = json.loads((ROOT/'data/_gold/gold_overlay_ledger.json').read_text(encoding='utf-8'))
gold = json.loads((ROOT/'data/_gold/user_pl_cells.json').read_text(encoding='utf-8'))
src = json.loads((ROOT/'data/dart/viz/pl_breakdown_master.json').read_text(encoding='utf-8'))
srcrows = src if isinstance(src, list) else src.get('rows', src)
idx = {(r['원보험사코드'], r['항목번호'], r['공시분기']): r for r in srcrows}
G = {(e['원보험사코드'], e['항목번호'], e['공시분기']): e for e in gold['set']}
e0 = led0['entries']; e1 = led1['entries']
out = []
out.append(f'ledger entries old {len(e0)} new {len(e1)}; removed {sorted(set(e0)-set(e1))}; added {sorted(set(e1)-set(e0))}')
changed = [k for k in e0 if k in e1 and e0[k] != e1[k]]
out.append(f'ledger entries modified (kept keys): {changed}')
other_top = {k: (led0[k] == led1[k]) for k in led0 if k != 'entries'}
out.append(f'ledger non-entry top-level keys unchanged: {other_top}')
def verdict(g, s):
    if g is None and s is None: return 'SAME_EXACT'
    if g is None or s is None: return 'LOAD_BEARING'
    d = round(abs(g - s), 9)
    return 'SAME_EXACT' if d <= 0.005 else ('SAME_AT_1DP' if d <= 0.05 else 'LOAD_BEARING')
for k in sorted(set(e0)-set(e1)):
    _, co, q, it = k.split('|'); it = int(it)
    g = G[(co, it, q)]['값']; s = idx[(co, it, q)]['값']
    out.append(f'REMOVED PIN {k}: pin(gold={e0[k]["gold"]}, src={e0[k]["src"]}) | now gold={g} builder-src(viz pl_breakdown_master)={s} diff={g-s:.6f} -> {verdict(g, s)} | master PL_breakdown 값 = ' + str({r["값"] for r in json.loads((ROOT/"PL_breakdown.json").read_text(encoding="utf-8")) if (r["원보험사코드"], r["항목번호"], r["공시분기"]) == (co, it, q)}))
# all remaining pins: still masked?
bad = []; masked_now = 0
for k, p in e1.items():
    parts = k.split('|')
    if parts[0] != 'PL': continue
    co, q, it = parts[1], parts[2], int(parts[3])
    g = G.get((co, it, q)); s = idx.get((co, it, q))
    if g is None or s is None: bad.append((k, 'missing')); continue
    v = verdict(g['값'], s['값'])
    if v == 'LOAD_BEARING': bad.append((k, v, g['값'], s['값']))
# census: all gold entries
cnt = {'SAME_EXACT': 0, 'SAME_AT_1DP': 0, 'LOAD_BEARING': 0, 'ABSENT': 0}
unpinned = []
for k, e in G.items():
    s = idx.get(k)
    if s is None: cnt['ABSENT'] += 1; continue
    gv, sv = e.get('값'), s.get('값')
    if gv is None or sv is None: cnt['LOAD_BEARING'] += 1; continue
    v = verdict(gv, sv); cnt[v] += 1
    if v != 'LOAD_BEARING' and f'PL|{k[0]}|{k[2]}|{k[1]}' not in e1: unpinned.append(k)
out.append(f'PL gold census (own computation): {len(G)} entries {cnt}; masked={cnt["SAME_EXACT"]+cnt["SAME_AT_1DP"]}; unpinned masked={unpinned}')
out.append(f'remaining PL pins no longer masked (would be DRIFT): {bad}')
(V/'v9_ledger.txt').write_text('\n'.join(out), encoding='utf-8')
print('\n'.join(out))
