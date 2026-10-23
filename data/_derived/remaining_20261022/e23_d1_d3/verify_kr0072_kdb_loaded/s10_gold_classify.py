# s10: compact classification of KR0072 gold entries HEAD -> live; compare to approved list; check nothing else (other companies, other quarters) touched in this load.
import json, csv
R = 'C:/Users/sangwook.cho/Desktop/insurequant/'
E = R + 'data/_derived/remaining_20261022/'
V = E + 'e23_d1_d3/verify_kr0072_kdb_loaded/'
B = E + 'e23_d1_d3/backup_before_apply/kr0072_kdb_load2/data/_gold/'
def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)
out = open(V + 's10_gold_classify.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
# approved list
appr = set()
with open(E + 'e20_held_and_remaining/measure/gold_cells_replaced.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['code'] == 'KR0072':
            appr.add((r['sheet'], r['quarter'], str(r['item'])))
W('approved KR0072 gold replacements (11):', sorted(appr))
def key(c):
    return (c['원보험사코드'], c['공시분기'], str(c['항목번호']))
res = {}
for sheet, fn in (('PL', 'user_pl_cells.json'), ('CSM', 'user_csm_cells.json')):
    live = load(R + 'data/_gold/' + fn); head = load(V + 'head/' + fn); pre = load(B + fn)
    L = {key(c): c for c in live['set']}; Hh = {key(c): c for c in head['set']}; P = {key(c): c for c in pre['set']}
    W('\n=====', sheet, 'set sizes head/pre/live:', len(Hh), len(P), len(L), '| dup keys live', len(live['set']) - len(L))
    # (a) this load: pre -> live changes anywhere
    chg_pre = [k for k in set(P) | set(L) if P.get(k) != L.get(k)]
    W('entries changed pre-load -> live:', len(chg_pre), '| of those not KR0072:', [k for k in chg_pre if k[0] != 'KR0072'])
    # (b) KR0072 classification vs HEAD
    new = []; repl = []; rem = []; same = []
    for k in sorted(set(Hh) | set(L), key=str):
        if k[0] != 'KR0072':
            continue
        if k not in Hh:
            new.append(k)
        elif k not in L:
            rem.append(k)
        elif Hh[k]['값'] != L[k]['값']:
            repl.append(k)
        elif Hh[k] != L[k]:
            repl.append(k)   # same value, other field changed
        else:
            same.append(k)
    W('KR0072 gold HEAD->live: new', len(new), 'replaced', len(repl), 'removed', len(rem), 'unchanged', len(same))
    W('  replaced (old -> new | HEAD was | HEAD note[:70]):')
    for k in repl:
        W('    ', sheet, k[1], k[2], Hh[k]['값'], '->', L[k]['값'], '| head was', Hh[k].get('was'), '| live was', L[k].get('was'), '| note:', (Hh[k].get('note') or '')[:90])
    W('  removed:')
    for k in rem:
        W('    ', sheet, k[1], k[2], Hh[k]['값'], '| was', Hh[k].get('was'), '| note:', (Hh[k].get('note') or '')[:120])
    W('  approved set vs actual replaced+removed:')
    act = {(sheet, k[1], k[2]) for k in repl + rem}
    ap = {a for a in appr if a[0] == sheet}
    W('    approved-but-not-touched:', sorted(ap - act), '| touched-but-not-approved:', sorted(act - ap))
    W('  new entries (', len(new), '): by quarter', {q: sum(1 for k in new if k[1] == q) for q in sorted({k[1] for k in new})}, 'quarters outside FY2023:', [k for k in new if not k[1].startswith('2023.')])
    # master value consistency: each live gold KR0072 entry equals master cum
    mfile = 'PL_breakdown.json' if sheet == 'PL' else 'CSM_waterfall.json'
    M = {(r['원보험사코드'], r['공시분기'], str(r['항목번호'])): r['값'] for r in load(R + mfile) if r['원보험사코드'] == 'KR0072'}
    bad = [(k, L[k]['값'], M.get(k)) for k in L if k[0] == 'KR0072' and (M.get(k) is None or abs(M[k] - L[k]['값']) > 1e-6)]
    W('  live KR0072 gold entries whose value != live master:', bad)
    # gold entries (live) for KR0072 beyond FY2023
    beyond = [k for k in L if k[0] == 'KR0072' and not k[1].startswith('2023.')]
    W('  live KR0072 gold entries outside FY2023 (pre-existing?):', len(beyond), 'unchanged vs HEAD:', all(Hh.get(k) == L[k] for k in beyond))
    # all non-KR0072 identical to pre
    # null/set dangi
    if sheet == 'PL':
        for sec in ('set_dangi', 'null_dangi'):
            lc = {tuple(c[:3]): c for c in live[sec]['cells']}; hc = {tuple(c[:3]): c for c in head[sec]['cells']}; pc = {tuple(c[:3]): c for c in pre[sec]['cells']}
            W(sec, 'head/pre/live sizes', len(hc), len(pc), len(lc))
            W('   pre->live changes:', sorted([(k, pc.get(k), lc.get(k)) for k in set(pc) | set(lc) if pc.get(k) != lc.get(k)], key=str))
            W('   head->live KR0072 changes:', sorted([(k, hc.get(k), lc.get(k)) for k in set(hc) | set(lc) if hc.get(k) != lc.get(k) and k[0] == 'KR0072'], key=str))
        W('doc keys added vs pre:', [k for k in live['set_dangi'] if k not in pre['set_dangi']], [k for k in live['null_dangi'] if k not in pre['null_dangi']], [k for k in live if k not in pre])
    else:
        W('doc keys added vs pre:', [k for k in live if k not in pre])
        for k in live:
            if k not in ('set',) and live[k] != pre.get(k):
                W('   top-level key changed vs pre:', k, str(live[k])[:200])
# ledger
ll = load(R + 'data/_gold/gold_overlay_ledger.json'); lh = load(V + 'head/gold_overlay_ledger.json'); lp = load(B + 'gold_overlay_ledger.json')
W('\n===== ledger keys', list(ll.keys()))
def flat(d):
    r = {}
    for k, v in d.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                r[(k, kk)] = json.dumps(vv, ensure_ascii=False, sort_keys=True)
        elif isinstance(v, list):
            for i, vv in enumerate(v):
                r[(k, i)] = json.dumps(vv, ensure_ascii=False, sort_keys=True)
        else:
            r[(k, '')] = json.dumps(v, ensure_ascii=False)
    return r
fl, fp, fh = flat(ll), flat(lp), flat(lh)
W('ledger entries head/pre/live', len(fh), len(fp), len(fl))
W('ledger pre->live removed:', sorted(k for k in fp if k not in fl), 'added:', sorted(k for k in fl if k not in fp), 'changed:', sorted(k for k in fl if k in fp and fl[k] != fp[k]))
for k in sorted(k for k in fp if k not in fl):
    W('   removed entry', k, fp[k][:300])
