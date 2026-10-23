# -*- coding: utf-8 -*-
"""patch a01_read_abl_fy2023.py: (1) missing optional rows count as 0 like _abl_row(...) or 0 in the production reader (first row of each group stays required);
(2) exclude 합계/기타사업비용 rows from the section subtotal check."""
import re
p = "a01_read_abl_fy2023.py"
s = open(p, encoding="utf-8").read()
old1 = '''        v[6] = sum(c[0] for c in exp) - sum(c[0] for c in inc)'''
new1 = '''        assert exp[0] is not None and inc[0] is not None, "claim rows missing"
        v[6] = sum(c[0] for c in exp if c) - sum(c[0] for c in inc if c)'''
assert s.count(old1) == 1
s = s.replace(old1, new1)
old2 = '''        v[11] = sum(c[0] for c in rinc) - sum(c[0] for c in rexp)'''
new2 = '''        assert rinc[0] is not None and rexp[0] is not None, "reinsurance claim rows missing"
        v[11] = sum(c[0] for c in rinc if c) - sum(c[0] for c in rexp if c)'''
assert s.count(old2) == 1
s = s.replace(old2, new2)
old3 = '''            rows_ = {k: x for k, x in d[sec].items() if k != "소계"}'''
new3 = '''            rows_ = {k: x for k, x in d[sec].items() if k not in ("소계", "합계", "기타사업비용")}'''
assert s.count(old3) == 1
s = s.replace(old3, new3)
# printing of exp4/inc4 with possible None
s = s.replace("[x[0] for x in vp['exp4']]", "[x[0] if x else 0 for x in vp['exp4']]").replace("[x[0] for x in vp['inc4']]", "[x[0] if x else 0 for x in vp['inc4']]")
s = s.replace("[x[1] for x in vp['exp4']]", "[x[1] if x else None for x in vp['exp4']]").replace("[x[1] for x in vp['inc4']]", "[x[1] if x else None for x in vp['inc4']]")
s = s.replace("[x[0] for x in vp['rinc2']]", "[x[0] if x else 0 for x in vp['rinc2']]").replace("[x[0] for x in vp['rexp2']]", "[x[0] if x else 0 for x in vp['rexp2']]")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
