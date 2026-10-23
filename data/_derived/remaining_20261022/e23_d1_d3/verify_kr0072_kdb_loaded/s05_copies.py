# s05: the two statement copies in the 1Q/2Q filings differ. Show titles/context of each and the row diffs.
import sys
sys.path.insert(0, 'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
import re
V = ROOT + 'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
out = open(V + 's05_copies.txt', 'w', encoding='utf-8')
def W(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
def nz(s):
    return re.sub(r'\s+', '', s)
for q in ('2023.1Q', '2023.2Q'):
    txt = read(FILES[q])
    lines = txt.split('\n')
    T = [(ln, rows) for ln, rows in tables(txt)
         if any(nz(r[0]) == '보험손익' for r in rows) and any(nz(r[0]).startswith('당기순이익') for r in rows)
         and any(nz(r[0]).startswith('당기총포괄') for r in rows)]
    for ln, rows in T:
        W('==', q, 'table at', ln, 'rows', len(rows))
        # context: previous 25 non-empty lines of text before the table
        ctx = []
        i = ln - 2
        while i >= 0 and len(ctx) < 14:
            s = strip(lines[i])
            if s:
                ctx.append((i + 1, s[:120]))
            i -= 1
        for c in reversed(ctx):
            W('   ctx', c)
    a, b = T[0][1], T[1][1]
    la = {nz(r[0]): r for r in a}
    W('-- row diffs first vs second copy (label: first | second)')
    for r in a:
        s = [x for x in b if nz(x[0]) == nz(r[0])]
        if not s or s[0] != r:
            W('  ', r, '|', s[:1])
    W('-- len', len(a), len(b))
