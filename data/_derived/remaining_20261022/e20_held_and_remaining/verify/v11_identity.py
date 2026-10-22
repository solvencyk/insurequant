# -*- coding: utf-8 -*-
"""Check 6a: block identities before (HEAD) vs after (live) for every changed company/quarter, on 값 and 값_당분기. Also headline deltas in 억원."""
import json, subprocess
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant'); V = Path(__file__).parent
def head(p): return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+p]).decode('utf-8'))
old = head('PL_breakdown.json'); new = json.loads((ROOT/'PL_breakdown.json').read_text(encoding='utf-8'))
names = {r['원보험사코드']: r['원수사명'] for r in new}
def idx(rows): return {(r['원보험사코드'], r['공시분기'], r['항목번호']): r for r in rows}
O, N = idx(old), idx(new)
chg = json.loads((V/'v1_diff_cells.json').read_text(encoding='utf-8'))
cqs = sorted({(k[0], k[2]) for k, f, a, b in chg})
IDS = [
 ('31=24+25', lambda g: g(31) - (g(24) + g(25))),
 ('20=1+17', lambda g: g(20) - (g(1) + g(17))),
 ('22=20+21', lambda g: g(22) - (g(20) + g(21))),
 ('24=22-23', lambda g: g(24) - (g(22) - g(23))),
 ('18=17-19', lambda g: g(18) - (g(17) - g(19))),
 ('25=26..30+32', lambda g: g(25) - sum(g(i) for i in (26, 27, 28, 29, 30, 32))),
 ('1=2+15-16', lambda g: g(1) - (g(2) + g(15) - g(16))),
]
def run(M, code, q, fld):
    def g(i):
        r = M.get((code, q, i))
        if r is None or r.get(fld) is None: raise KeyError(i)
        return r[fld]
    out = {}
    for nm, f in IDS:
        try: out[nm] = f(g)
        except KeyError as e: out[nm] = None
    return out
lines = []; newfail = []
for code, q in cqs:
    for fld in ('값', '값_당분기'):
        a = run(O, code, q, fld); b = run(N, code, q, fld)
        for nm in a:
            ra, rb = a[nm], b[nm]
            fa = ra is not None and abs(ra) > 1.0; fb = rb is not None and abs(rb) > 1.0
            if fb or fa:
                lines.append(f'{"NEWFAIL" if fb and not fa else ("FIXED" if fa and not fb else ("STILL" if fa and fb else ""))}\t{code} {names[code]} {q} {fld} {nm}: before={ra} after={rb}')
            if rb is None and ra is not None and fld == '값':
                lines.append(f'NOW-UNCOMPUTABLE\t{code} {q} {fld} {nm}')
            if fb and not fa: newfail.append((code, q, fld, nm, rb))
lines.append(f'new identity failures (|res|>1 백만원): {len(newfail)}')
# headline deltas in 억원 (cumulative 값 and 값_당분기)
lines.append('--- headline deltas (억원) 값 / 값_당분기 : before -> after ---')
for code, q in cqs:
    parts = []
    for it, nm in ((1, '보험손익'), (17, '투자손익'), (24, '당기순이익'), (25, 'OCI'), (31, '총포괄')):
        for fld, tag in (('값', 'cum'), ('값_당분기', 'sgl')):
            a = O[(code, q, it)].get(fld); b = N[(code, q, it)].get(fld)
            if a != b:
                f = lambda x: 'null' if x is None else f'{x/100:,.1f}'
                parts.append(f'{nm}[{tag}] {f(a)}->{f(b)}' + ('' if (a is None or b is None) else f' ({(b-a)/100:+,.1f})'))
    lines.append(f'{code} {names[code]} {q}: ' + '; '.join(parts))
(V/'v11_identity.txt').write_text('\n'.join(lines), encoding='utf-8')
print([l for l in lines if l.startswith('new identity') ])
# coverage of evaluation (non-vacuity)
import collections
ev = collections.Counter(); tot = collections.Counter()
for code, q in cqs:
    for fld in ('값', '값_당분기'):
        b = run(N, code, q, fld)
        for nm, v in b.items():
            tot[nm] += 1
            if v is not None: ev[nm] += 1
cov = ['evaluated/total per identity (after): ' + str({nm: f'{ev[nm]}/{tot[nm]}' for nm in tot})]
with open(V/'v11_identity.txt', 'a', encoding='utf-8') as fh: fh.write('\n' + '\n'.join(cov))
print(cov)
