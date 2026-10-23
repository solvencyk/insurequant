# -*- coding: utf-8 -*-
"""repair the backspace character (0x08) that the previous patch left inside the regex of all_tables()"""
from pathlib import Path

p = Path("kr0003_verify.py")
s = p.read_text(encoding="utf-8")
bad = "<TABLE" + chr(8) + '"'
good = "<TABLE" + chr(92) + 'b"'
assert s.count(bad) == 1, s.count(bad)
s = s.replace(bad, good)
assert chr(8) not in s
p.write_text(s, encoding="utf-8", newline="\n")
print("repaired")
