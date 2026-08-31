# -*- coding: utf-8 -*-
"""Recursively scan the ENTIRE gate report (not just findings[]) for any
occurrence of KR0075 + 2026.2Q, in both before/after reports, and diff --
to catch other census-style gate sections (parent_present_child_incomplete,
post_transition_parent_census, axis_evaluation_census, etc.) that are
independent of the findings[] list but still feed the exit code.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
BEFORE = REPO / "artifacts" / "kics_validation" / "report_20260831T053500Z.json"
AFTER = REPO / "artifacts" / "kics_validation" / "report_20260831T054238Z.json"

CODE = "KR0075"
QUARTER = "2026.2Q"


def hits(obj, path=""):
    """Yield (path, obj) for every dict/list node that mentions both CODE and
    QUARTER somewhere inside it, but only report the SMALLEST (leaf-most)
    such node to avoid duplicate parent-container noise."""
    if isinstance(obj, dict):
        blob = json.dumps(obj, ensure_ascii=False)
        if CODE in blob and QUARTER in blob:
            child_hit = False
            for k, v in obj.items():
                sub_blob = json.dumps(v, ensure_ascii=False)
                if CODE in sub_blob and QUARTER in sub_blob:
                    child_hit = True
                    yield from hits(v, f"{path}.{k}")
            if not child_hit:
                yield (path, obj)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            blob = json.dumps(item, ensure_ascii=False)
            if CODE in blob and QUARTER in blob:
                yield from hits(item, f"{path}[{i}]")


def collect(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for k, v in d.items():
        if k == "findings":
            continue  # already diffed separately
        blob = json.dumps(v, ensure_ascii=False)
        if CODE in blob and QUARTER in blob:
            out.extend(hits(v, k))
    return out


before = collect(BEFORE)
after = collect(AFTER)

print(f"=== BEFORE: {len(before)} non-findings report sections mention {CODE} {QUARTER} ===")
for p, obj in before:
    print(f"  {p}: {json.dumps(obj, ensure_ascii=False)[:400]}")

print()
print(f"=== AFTER: {len(after)} non-findings report sections mention {CODE} {QUARTER} ===")
for p, obj in after:
    print(f"  {p}: {json.dumps(obj, ensure_ascii=False)[:400]}")
