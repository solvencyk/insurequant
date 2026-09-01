# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src")
from solvency.parser.company_handlers import LABEL_FIXES, apply_label_fixes

for wrong, right, note in LABEL_FIXES:
    print(f"{note}: wrong={wrong!r} right={right!r}")

s = "2. 비례성원칙을 적용한 종속회사의 요구 자본 대응치"
print()
print("input:", repr(s))
out = apply_label_fixes(s)
print("output:", repr(out))
