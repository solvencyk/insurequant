# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
p = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\src\solvency\parser\kics_disclosure_parser.py")
raw = p.read_bytes()
print("BOM check (first 4 bytes):", raw[:4])
text = raw.decode("utf-8")
lines = text.splitlines()
for i in range(95, 120):
    print(i+1, repr(lines[i]))
