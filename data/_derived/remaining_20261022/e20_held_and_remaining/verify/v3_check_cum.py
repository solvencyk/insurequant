# -*- coding: utf-8 -*-
"""Independent re-read of every changed cumulative (값) cell vs the NEXT-YEAR filing's prior cumulative column."""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vx_reader as R
V = Path(__file__).parent
ROOT = R.ROOT
chg = json.loads((V/'v1_diff_cells.json').read_text(encoding='utf-8'))
names = {}
for r in json.loads((ROOT/'PL_breakdown.json').read_text(encoding='utf-8')):
    names[r['원보험사코드']] = r['원수사명']
cum = {}   # (code,q,item) -> (old,new)
for k, f, a, b in chg:
    if f == '값':
        cum[(k[0], k[2], k[1])] = (a, b)
# new master full values for closure
newm = {}
for r in json.loads((ROOT/'PL_breakdown.json').read_text(encoding='utf-8')):
    newm[(r['원보험사코드'], r['공시분기'], r['항목번호'])] = r.get('값')
def fy_for(q):
    y, qq = q.split('.'); y = int(y); n = int(qq[0])
    return f'FY{y+1}_Q{n}'
STRIP = re.compile(r'^(?:[IVXⅠ-Ⅻ]+\.|\d+\.|\d+\)|\(\d+\)|[가-힣]\.)\s*')
def norm(l):
    l = re.sub(r'\([^)]*\)', '', l.replace(' ', ''))
    l = STRIP.sub('', l)
    return STRIP.sub('', l)
LAB = {1: r'^보험손익$', 16: r'^기타사업(비용|비)$', 17: r'^투자손익$', 20: r'^영업이익$', 22: r'^법인세(비용)?차감전(순)?(이익|손익)$',
       23: r'^법인세비용$', 24: r'^(당기|분기|반기)?순(이익|손익)$', 25: r'^(법인세비용차감후|당기)?(총)?기타포괄(손익|이익)$', 31: r'^(분기|반기|당기)?총포괄(손익|이익)$'}
res_lines = []
fails = 0; ok = 0
cache = {}
def get(code, fy):
    if (code, fy) not in cache:
        cache[(code, fy)] = R.stmt(code, fy)
    return cache[(code, fy)]
def pc(vals):
    xs = [v for c, v in vals]
    if len(xs) >= 4: return xs[3]
    if len(xs) >= 2: return xs[1]
    return None
bycq = {}
for (code, q, item), (old, new) in sorted(cum.items(), key=lambda x: (x[0][0], x[0][1], str(x[0][2]))):
    fy = fy_for(q)
    ss = get(code, fy)
    if not ss:
        res_lines.append(f'{code} {q} item{item}: NO STATEMENT in {fy}'); fails += 1; continue
    s = ss[0]
    scale = 1e6 if (s['unit'] or '').startswith('원') else 1.0
    rows = []
    for lab, ln, vals in s['rows']:
        v = R.num(pc(vals)) if pc(vals) is not None else None
        rows.append((lab, ln, v/scale if v is not None else None))
    # derived items
    def rv(pat):
        m = [(l, ln, v) for l, ln, v in rows if re.search(pat, norm(l)) and v is not None]
        return m
    cand = []
    if item in LAB:
        cand = rv(LAB[item])
        vals_ = sorted({round(v, 6) for _, _, v in cand})
        status = 'OK' if any(abs(v-new) < 1e-5 for v in vals_) else 'FAIL'
        # if multiple label matches, first match by position is the master item
        res_lines.append(f'{status}\t{code} {names[code]}\t{q}\titem{item}\tnew={new}\tfiling={fy} unit={s["unit"]}\tcand={[(l,ln,v) for l,ln,v in cand][:3]}')
    elif item == 19:
        a = lambda p: sum(v for l, ln, v in rows if re.search(p, norm(l)) and v is not None)
        rows_f = [(l, ln, v) for l, ln, v in rows if re.search(r'(재)?보험금융(수익|비용)', norm(l)) and v is not None]
        inc = sum(v for l, ln, v in rows_f if '수익' in l); exp = sum(v for l, ln, v in rows_f if '비용' in l)
        val = inc - exp
        status = 'OK' if abs(val-new) < 1e-5 else 'FAIL'
        res_lines.append(f'{status}\t{code} {names[code]}\t{q}\titem19\tnew={new}\tcalc={val}\trows={[(l,ln,v) for l,ln,v in rows_f]}')
    elif item == 18:
        # 18 = 17 - 19 (master definition per owner notes); recompute 17 and 19 from rows
        r17 = [v for l, ln, v in rows if re.search(LAB[17], norm(l)) and v is not None]
        rows_f = [(l, ln, v) for l, ln, v in rows if re.search(r'(재)?보험금융(수익|비용)', norm(l)) and v is not None]
        inc = sum(v for l, ln, v in rows_f if '수익' in l); exp = sum(v for l, ln, v in rows_f if '비용' in l)
        val = r17[0] - (inc - exp)
        status = 'OK' if abs(val-new) < 1e-5 else 'FAIL'
        res_lines.append(f'{status}\t{code} {names[code]}\t{q}\titem18\tnew={new}\tcalc={val} (17={r17[0]}, 19={inc-exp})')
    else:
        # 26, 27, 29, 32: find rows whose value equals new
        hit = [(l, ln, v) for l, ln, v in rows if v is not None and abs(v-new) < 1e-5]
        status = 'OK' if hit else ('RESID' if item == 32 else 'FAIL')
        res_lines.append(f'{status}\t{code} {names[code]}\t{q}\titem{item}\tnew={new}\tvalue-hits={hit[:4]}')
    st = res_lines[-1].split('\t')[0]
    if st == 'FAIL': fails += 1
    else: ok += 1
    bycq.setdefault((code, q), []).append(st)
res_lines.append(f'TOTAL OK/RESID={ok} FAIL={fails} cells={len(cum)}')
res_lines.append('company-quarters covered: %d' % len(bycq))
(V/'v3_check_cum.txt').write_text('\n'.join(res_lines), encoding='utf-8')
print(res_lines[-2:], )
