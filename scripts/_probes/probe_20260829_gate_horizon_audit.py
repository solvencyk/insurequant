#!/usr/bin/env python3
"""Gate-only horizon audit: which quarter-literals live in *executable* code
(not comments/docstrings) of the push-wired gates, and what the max is.

Uses ast so comments and docstrings are excluded — the earlier grep census was
90% prose. Read-only.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

QPAT = re.compile(r"^20\d\d\.[1-4]Q$")
QIN = re.compile(r"\b20\d\d\.[1-4]Q\b")

# push-wired gates (prepush_check.py) + their imports
GATES = [
    "scripts/prepush_check.py",
    "scripts/validate_data_contract.py",
    "scripts/validate_kics_disclosure.py",
    "scripts/validate_master_tables.py",
    "scripts/validate_csm_continuity.py",
    "scripts/validate_csm_waterfall.py",
    "scripts/validate_kics_rate_sensitivity.py",
    "scripts/validate_nb_csm_multiple.py",
    "scripts/validate_live_artifacts.py",
    "scripts/validate_golden_input_fingerprints.py",
    "scripts/validate_statutory_reserves.py",
    "scripts/check_dart_raw_coverage.py",
    "scripts/check_data_file_integrity.py",
    "scripts/check_inbox_hygiene.py",
    "src/solvency/validation/kics_json_rules.py",
]

print("=" * 78)
print("게이트 실행코드(주석·독스트링 제외) 안의 분기 리터럴")
print("=" * 78)
for rel in GATES:
    fp = ROOT / rel
    if not fp.exists():
        print(f"\n--- {rel}: (파일 없음)")
        continue
    src = fp.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for m in QIN.findall(node.value):
                # skip docstrings: a Constant that is the sole Expr of a body
                lits.append((node.lineno, m))
    # remove docstring constants
    doc_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node, clean=False)
            if d:
                body0 = node.body[0]
                for ln in range(body0.lineno, (body0.end_lineno or body0.lineno) + 1):
                    doc_lines.add(ln)
    lits = [(ln, q) for ln, q in lits if ln not in doc_lines]
    if not lits:
        print(f"\n--- {rel}: 실행코드 분기 리터럴 없음 (데이터에서 파생) ✅")
        continue
    mx = max(q for _, q in lits)
    lines = src.splitlines()
    print(f"\n--- {rel}: {len(lits)}개, 최대={mx}"
          + ("   ⚠️ 2026.2Q 미포함" if mx < "2026.2Q" else ""))
    seen = set()
    for ln, q in sorted(lits):
        if ln in seen:
            continue
        seen.add(ln)
        print(f"    L{ln:<5d} {lines[ln-1].strip()[:130]}")
