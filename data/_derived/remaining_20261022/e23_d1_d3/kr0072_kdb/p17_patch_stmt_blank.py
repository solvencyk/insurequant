# -*- coding: utf-8 -*-
"""patch kdb_stmt.py: OCI leaf rows may print a blank cell for a period in which the item does not exist (original FY2023 filings: 매도가능/만기보유 in the 2023 column) -> 0.0 with printed ''."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kdb_stmt.py"
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:80])
    s = s.replace(a, b)


sub('''    def cell_at(self, k, j):
        r = self.rows[k]
        cs = r["cells"]
        if len(cs) != len(self.paths):
            raise RuntimeError(f"{self.rel}: row {cs[0]['text']!r} has {len(cs)} cells, header {len(self.paths)}")
        c = cs[j]
        v = mn(c["text"], self.unit)''', '''    def cell_at(self, k, j, blank_ok=False):
        r = self.rows[k]
        cs = r["cells"]
        if len(cs) != len(self.paths):
            raise RuntimeError(f"{self.rel}: row {cs[0]['text']!r} has {len(cs)} cells, header {len(self.paths)}")
        c = cs[j]
        if blank_ok and c["text"] == "":
            return dict(label=cs[0]["text"], label_line=cs[0]["line"], printed="", line=c["line"], unit=self.unit, mn=0.0, col=j, header=self.paths[j], row=k, blank=True)
        v = mn(c["text"], self.unit)''')
sub('''            leaves[block].append(self.cell_at(k, j))''', '''            leaves[block].append(self.cell_at(k, j, blank_ok=True))''')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
