# -*- coding: utf-8 -*-
p = "k01_read_kblife.py"
s = open(p, encoding="utf-8").read()
a = '''        assert E.nl(heads[6]) == "합계" and E.nl(heads[12]) == "합계", heads'''
b = '''        assert E.nl(heads[5]) == "합계" and E.nl(heads[11]) == "합계", heads'''
assert s.count(a) == 1
s = s.replace(a, b)
a2 = '''        assert E.nl(heads[6]) == "합계", heads'''
b2 = '''        assert E.nl(heads[5]) == "합계", heads'''
assert s.count(a2) == 1
s = s.replace(a2, b2)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
