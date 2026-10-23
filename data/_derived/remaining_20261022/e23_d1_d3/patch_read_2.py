# -*- coding: utf-8 -*-
"""fix control characters that a shell heredoc turned into escapes (backspace instead of the regex word boundary)"""
from pathlib import Path

p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/e23_read.py")
s = p.read_text(encoding="utf-8")
bad = {c: s.count(c) for c in set(s) if ord(c) < 32 and c not in "\n\t\r"}
print("control chars before:", {hex(ord(k)): v for k, v in bad.items()})
s = s.replace("\x08", "\\b")
bad2 = {c: s.count(c) for c in set(s) if ord(c) < 32 and c not in "\n\t\r"}
print("control chars after:", {hex(ord(k)): v for k, v in bad2.items()})
p.write_text(s, encoding="utf-8", newline="\n")
for i, line in enumerate(s.split("\n"), 1):
    if "CELL_OPEN =" in line or "CELL_CLOSE =" in line:
        print(i, line)
