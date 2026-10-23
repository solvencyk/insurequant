# -*- coding: utf-8 -*-
"""relax the e21 pre-existing-drift guard for this load: a hand-blanked live 값_당분기 may be overwritten by the builder derivation when (a) the cell is a planned cell or the successor-quarter
single of a planned cell, and (b) the new derivation equals the printed prior 3-month column within the filing's rounding tolerance (3 mn).  e21 demanded 1e-6 and an unchanged cumulative."""
from pathlib import Path

p = Path("e23_apply.py")
s = p.read_text(encoding="utf-8")
a = '        if k in p3m and x[6] is not None and abs(x[6] - p3m[k]) <= 1e-6 and x[5] == x[3]:'
b = '        if k in p3m and x[6] is not None and abs(x[6] - p3m[k]) <= 3.0 and x[5] is not None and (k in want or is_derived_follow(k, want)):'
assert s.count(a) == 1
s = s.replace(a, b)
a2 = '    pr(f"pre-existing live blanks overwritten by a derivation that equals the printed 3-month column: {P[\'allowed_pre\']}")'
b2 = '    pr(f"pre-existing live blanks (hand-set 값_당분기 = None that a fresh build would derive) overwritten by the derivation that equals the printed prior 3-month column within 3 mn: {P[\'allowed_pre\']}")'
assert s.count(a2) == 1
s = s.replace(a2, b2)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
