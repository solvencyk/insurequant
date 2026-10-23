# s08: items 5/6/9/10/11 (not loaded): print the insurance-revenue note table (prior cum column) of each later filing next to master values.
import sys, re, json
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
V = ROOT + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
out = open(V + 's08_items56.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def nz(s):
    return re.sub(r'\s+', '', s)
PL = json.load(open(ROOT + 'PL_breakdown.json', encoding='utf-8'))
M = {(r['공시분기'], r['항목번호']): r['값'] for r in PL if r['원보험사코드'] == 'KR0072'}
for q, p in FILES.items():
    W('=====', q, [M.get((q, i)) for i in (4, 5, 6, 9, 10, 11)], '(master items 4,5,6,9,10,11 mn)')
    done = 0
    for ln, rows in tables(read(p)):
        if any('제공된서비스의보험계약마진' in nz(r[0]) for r in rows):
            W(' note table L%d' % ln)
            for r in rows:
                W('    ', r)
            done += 1
            break
