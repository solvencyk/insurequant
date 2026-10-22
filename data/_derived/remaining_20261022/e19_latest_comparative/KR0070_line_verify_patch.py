# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("KR0070_line_verify.py")
s = p.read_text(encoding="utf-8")
old_a = '''        txt = TAG.sub("", L[ln - 1]).strip()
        te = L[ln - 2]'''
new_a = '''        single = L[ln - 1].lstrip().startswith("<TE")          # single-line cell <TE ...>text</TE>
        txt = TAG.sub("", L[ln - 1]).strip()
        te = L[ln - 1] if single else L[ln - 2]'''
old_b = '''        for j in range(i + 1, i + 12):
            if L[j].startswith("<P>"):
                label = TAG.sub("", L[j]).strip()
                break'''
new_b = '''        for j in range(i + 1, i + 12):
            if L[j].startswith("<P>") or (single and L[j].lstrip().startswith("<TE")):
                label = TAG.sub("", L[j]).strip()
                break'''
assert s.count(old_a) == 1 and s.count(old_b) == 1
p.write_text(s.replace(old_a, new_a).replace(old_b, new_b), encoding="utf-8", newline="\n")
