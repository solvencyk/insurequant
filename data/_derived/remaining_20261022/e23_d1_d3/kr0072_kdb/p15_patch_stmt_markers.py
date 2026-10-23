# -*- coding: utf-8 -*-
"""patch kdb_stmt.py: row labels are compared WITHOUT leading numbering markers (the original FY2023 filings print 'Ⅰ.보험손익', '(1)보험영업수익', '1.보험수익', '가.유효이자율..')."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kdb_stmt.py"
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:80])
    s = s.replace(a, b)


sub('''PERIOD_RE = re.compile(''', '''MARK_RE = re.compile(r"^(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.|\(\d+\)|\d+\.|[가-힣]\.)+")


def rl(text):
    """normalised row label without leading numbering markers"""
    return MARK_RE.sub("", nspace(text))


PERIOD_RE = re.compile(''')
sub('''            labs = {nspace(r["cells"][0]["text"]) for r in table_rows(L, ta, tb) if r["cells"]}
            if "보험손익" in labs and ("법인세차감전순이익" in labs or "법인세차감전순이익(손실)" in labs):''',
    '''            labs = {rl(r["cells"][0]["text"]) for r in table_rows(L, ta, tb) if r["cells"]}
            if "보험손익" in labs and ("법인세차감전순이익" in labs or "법인세차감전순이익(손실)" in labs):''')
sub('''        return [(k, r) for k, r in enumerate(self.rows) if nspace(r["cells"][0]["text"]) in want]''',
    '''        return [(k, r) for k, r in enumerate(self.rows) if rl(r["cells"][0]["text"]) in want]''')
sub('''            lab = nspace(self.rows[k]["cells"][0]["text"])
            if lab == SUB_A:''', '''            lab = rl(self.rows[k]["cells"][0]["text"])
            if lab == SUB_A:''')
sub('''        for c in leaves["A"]:
            n = nspace(c["label"])''', '''        for c in leaves["A"]:
            n = rl(c["label"])''')
sub('''        for c in leaves["B"]:
            n = nspace(c["label"])''', '''        for c in leaves["B"]:
            n = rl(c["label"])''')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
