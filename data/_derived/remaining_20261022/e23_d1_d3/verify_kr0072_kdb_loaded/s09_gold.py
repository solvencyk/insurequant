# s09: gold / ledger diff. (a) pre-load backup vs live: ONLY KR0072 may differ; (b) HEAD vs live for KR0072: classify; (c) compare with approved list.
import json, csv, collections
R = 'C:/Users/sangwook.cho/Desktop/insurequant/'
E = R + 'data/_derived/remaining_20261022/'
V = E + 'e23_d1_d3/verify_kr0072_kdb_loaded/'
B = E + 'e23_d1_d3/backup_before_apply/kr0072_kdb_load2/data/_gold/'
H = V + 'head/'
def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)
out = open(V + 's09_gold.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def walk(d, path=''):
    """flatten json into {path: leaf}; lists of cells keyed by their content tuple when they look like cells"""
    res = {}
    if isinstance(d, dict):
        for k, v in d.items():
            res.update(walk(v, path + '/' + str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            res[path + '[%d]' % i] = json.dumps(v, ensure_ascii=False, sort_keys=True)
    else:
        res[path] = json.dumps(d, ensure_ascii=False)
    return res
for name in ('user_pl_cells.json', 'user_csm_cells.json', 'gold_overlay_ledger.json'):
    new = load(R + 'data/_gold/' + name); pre = load(B + name); head = load(H + name)
    W('=====', name, 'top-level keys new:', list(new.keys()))
    # structure peek
    for k, v in new.items():
        if isinstance(v, dict):
            W('   key', k, 'dict keys', list(v.keys())[:8], 'sizes', {kk: (len(vv) if hasattr(vv, '__len__') else vv) for kk, vv in list(v.items())[:8]})
        elif isinstance(v, list):
            W('   key', k, 'list len', len(v), 'first', json.dumps(v[0], ensure_ascii=False)[:200] if v else None)
    # (a) pre vs new: collect differing top-level entries
    def entries(d):
        """yield (section, key, repr) for every set-cell / list-cell / dict entry"""
        res = {}
        for sec, v in d.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if isinstance(vv, list) and vv and isinstance(vv[0], list):
                        for c in vv:
                            res[(sec, kk, json.dumps(c[:3], ensure_ascii=False))] = json.dumps(c, ensure_ascii=False)
                    else:
                        res[(sec, kk, '')] = json.dumps(vv, ensure_ascii=False)
            elif isinstance(v, list):
                for c in v:
                    res[(sec, '', json.dumps(c if not isinstance(c, list) else c[:3], ensure_ascii=False))] = json.dumps(c, ensure_ascii=False)
            else:
                res[(sec, '', '')] = json.dumps(v, ensure_ascii=False)
        return res
    en, ep, eh = entries(new), entries(pre), entries(head)
    def diff(a, b):
        ks = set(a) | set(b)
        return sorted([(k, a.get(k), b.get(k)) for k in ks if a.get(k) != b.get(k)], key=lambda x: str(x[0]))
    d_pre = diff(ep, en)
    W('  (a) pre-load backup -> live: differing entries =', len(d_pre))
    non72 = [x for x in d_pre if 'KR0072' not in str(x[0]) and 'KR0072' not in str(x[1]) and 'KR0072' not in str(x[2]) and 'e23_kr0072' not in str(x[0])]
    W('      entries NOT mentioning KR0072 (must be 0 apart from doc keys):', len(non72))
    for x in non72[:20]:
        W('        NON72', str(x)[:400])
    for x in d_pre:
        k, o, n_ = x
        W('      ', 'ENTRY', k, '\n           pre :', (o or '')[:300], '\n           live:', (n_ or '')[:300])
    d_head = diff(eh, en)
    W('  (b) HEAD -> live, KR0072-only entries:', len([x for x in d_head if 'KR0072' in str(x)]), '| all differing entries vs HEAD:', len(d_head), '(other companies from the four earlier loads)')
