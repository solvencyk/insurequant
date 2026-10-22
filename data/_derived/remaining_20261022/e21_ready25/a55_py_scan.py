# -*- coding: utf-8 -*-
"""READ-ONLY: every .py in the e21 evidence folder: no BOM, valid UTF-8, ast.parse OK."""
import ast, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
bad = 0
n = 0
for p in sorted(Path(__file__).resolve().parent.rglob("*.py")):
    b = p.read_bytes()
    n += 1
    try:
        s = b.decode("utf-8")
        ast.parse(s)
        ok = not b.startswith(b"\xef\xbb\xbf")
    except Exception as e:
        ok = False
        print("FAIL", p.name, type(e).__name__, e)
    if not ok:
        bad += 1
        print("BAD", p)
print(f"scanned {n} .py files, bad {bad}")
