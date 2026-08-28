#!/usr/bin/env python3
"""Smoke-test tier1_for() now returning items 25-31, cross-checked against the pass-2 census
values computed independently.  Read-only. Ticket: inbox/parser/20260828T0113Z."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import tier1_for  # noqa: E402

CASES = [
    ("삼성화재해상보험", "2026.2Q", "KR0008"),
    ("삼성화재해상보험", "2024.2Q", "KR0008"),   # pre-breakdown quarter: 26-30 expect missing
    ("한화생명", "2023.3Q", "KR0068"),
    ("교보생명보험", "2025.4Q", "KR0073"),        # hedge-tag fallback quarter
    ("교보생명보험", "2026.1Q", "KR0073"),
    ("삼성생명보험", "2023.4Q", "KR0069"),        # pre-label-switch (기타포괄손익)
    ("삼성생명보험", "2024.4Q", "KR0069"),        # post-label-switch (법인세비용차감후...)
    ("흥국화재", "2024.4Q", "KR0005"),            # no equity FVOCI tag ever
]
for name, q, code in CASES:
    t1 = tier1_for(name, q, code) or {}
    line = " ".join(f"{i}={t1.get(i)}" for i in range(25, 32))
    ident = None
    if t1.get(24) is not None and t1.get(25) is not None and t1.get(31) is not None:
        ident = round((t1[24] + t1[25]) - t1[31], 3)
    print(f"{code} {name} {q}: 24={t1.get(24)}  {line}  | 24+25-31={ident}")
