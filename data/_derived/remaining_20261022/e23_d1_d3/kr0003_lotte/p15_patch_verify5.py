# -*- coding: utf-8 -*-
"""(1) LOB unit from the table's own THEAD first cell, (2) item 2 legs = legs of 3 + legs of 8, (3) label alternatives (분기순이익 / 반기순이익) for item 24 in the quarterly filings"""
from pathlib import Path

p = Path("kr0003_verify.py")
s = p.read_text(encoding="utf-8")


def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)


# (1) unit
sub('    unit, ul = unit_above(L, t["a"] + 1, span=60)\n',
    '    hp = header_paths(L, t["a"], t["b"])\n'
    '    m_u = re.search(r"(백만원|천원|원)", hp[0][0]) if hp and hp[0] else None\n'
    '    unit, ul = (m_u.group(1), t["a"] + 1) if m_u and "단위" in hp[0][0] else unit_above(L, t["a"] + 1, span=60)\n')
# (2) item 2 legs
sub('    it[2] = dict(val=it[3]["val"] + it[8]["val"], legs=[], how="3 + 8")',
    '    it[2] = dict(val=it[3]["val"] + it[8]["val"], legs=it[3]["legs"] + it[8]["legs"], how="3 + 8")')
# (3) label alternatives in Stmt.row: nl may be a tuple of alternatives (the first one that exists wins)
sub('''    def row(self, nl, nth=0, expect_count=1):
        c = [r for r in self.rows if r["nl"] == norm_label(nl)]''',
    '''    def row(self, nl, nth=0, expect_count=1):
        alts = nl if isinstance(nl, (tuple, list)) else (nl,)
        c = []
        for a_ in alts:
            c = [r for r in self.rows if r["nl"] == norm_label(a_)]
            if c:
                break''')
sub('    item(24, [one(24, "당기순이익")], "statement line")', '    item(24, [one(24, ("당기순이익", "분기순이익", "반기순이익"))], "statement line")')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
