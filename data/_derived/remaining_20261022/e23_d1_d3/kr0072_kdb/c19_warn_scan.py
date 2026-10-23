# -*- coding: utf-8 -*-
"""read-only: list the .py files of this folder that raise a SyntaxWarning when compiled (invalid escape sequences in one-off patch scripts)"""
import sys
import warnings
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
for f in sorted(HERE.glob("*.py")):
    src = f.read_text(encoding="utf-8")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compile(src, str(f), "exec")
    if w:
        print(f.name, [(x.lineno, str(x.message)[:40]) for x in w])
