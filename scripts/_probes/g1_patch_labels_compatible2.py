# -*- coding: utf-8 -*-
"""Patch labels_compatible(): whitespace-tolerant substring checks.
Derives the exact OLD block from the live file itself (byte-exact slice, no
retyped Korean text) and rewrites ONLY the `if "..." in baseline_name/table_label`
condition lines to compare against whitespace-stripped `bn`/`tl` locals, leaving
every comment and the function signature untouched.
"""
from __future__ import annotations
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "src" / "solvency" / "parser" / "kics_disclosure_parser.py"

src = TARGET.read_text(encoding="utf-8")
start = src.index("def labels_compatible(baseline_name: str, table_label: str) -> bool:\n")
end = src.index("\n\n\ndef build_label_lookups(")
old_block = src[start:end + 1]  # include trailing \n, exclude the blank-line separator
print("--- old_block (first 200 chars) ---")
print(repr(old_block[:200]))
print(f"old_block length: {len(old_block)}")

lines = old_block.split("\n")
sig = lines[0]
assert sig == 'def labels_compatible(baseline_name: str, table_label: str) -> bool:'
body = lines[1:]

new_body = []
n_code_lines = 0
for ln in body:
    stripped = ln.strip()
    if stripped.startswith('if "') and (" baseline_name" in ln or " table_label" in ln):
        new_ln = ln.replace("baseline_name", "bn").replace("table_label", "tl")
        new_body.append(new_ln)
        n_code_lines += 1
    else:
        new_body.append(ln)

print(f"rewrote {n_code_lines} condition lines")
assert n_code_lines == 10, f"expected 10 condition lines, got {n_code_lines}"

guard_comment = (
    "    # Compare on whitespace-stripped copies: Docling occasionally inserts a\n"
    "    # stray space mid-word when a long label wraps across two PDF lines\n"
    '    # (e.g. a "요구자본" label rendering as "요구자 본" / "요 구자본") — a raw\n'
    "    # substring check below would then wrongly reject an otherwise-identical\n"
    "    # label even though normalise_label() already treats the two as equal\n"
    "    # (item24-26 종속회사/관계회사 요구자본 rows going row-absent in the master,\n"
    '    # 2026-09-01 item23 자식 칸 감사 — KR0051 2023.1Q\'s own "요구자 본"/"요 구자본").\n'
    '    bn = baseline_name.replace(" ", "")\n'
    '    tl = table_label.replace(" ", "")\n'
)

new_block = sig + "\n" + guard_comment + "\n".join(new_body)

assert old_block in src, "old_block not found verbatim in src (should be impossible, we sliced it out)"
n = src.count(old_block)
if n != 1:
    raise SystemExit(f"ABORT: old_block occurs {n} times, expected 1")

new_src = src.replace(old_block, new_block)
TARGET.write_text(new_src, encoding="utf-8")
print("patched OK. new_block:")
print(new_block)
