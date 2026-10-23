# -*- coding: utf-8 -*-
"""read-only: what changed in a golden fixture (JSON key level, and inside the SUMMARY line field by field)"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BKP = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0009_hyundai"


def walk(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                yield (f"{path}/{k}", "<absent>", b[k])
            elif k not in b:
                yield (f"{path}/{k}", a[k], "<absent>")
            else:
                yield from walk(a[k], b[k], f"{path}/{k}")
    elif a != b:
        yield (path, a, b)


def fields(s):
    return [x.strip() for x in re.split(r"\s\|\s", s)]


for before, after in (("tests/fixtures/master_tables_golden.json", "tests/fixtures/master_tables_golden.json"), ("tests/fixtures/builder_input_fingerprints.json", "tests/fixtures/builder_input_fingerprints.json")):
    a = json.loads((BKP / before).read_text(encoding="utf-8"))
    b = json.loads((ROOT / after).read_text(encoding="utf-8"))
    d = list(walk(a, b))
    print(f"== {after}: {len(d)} differing leaf(s)")
    for path, x, y in d:
        if isinstance(x, str) and isinstance(y, str) and "SUMMARY" in x and x.count("|") > 3:
            fa, fb = fields(x), fields(y)
            print(f"   {path}: SUMMARY fields changed:")
            for p, q in zip(fa, fb):
                if p != q:
                    print(f"      {p}   ->   {q}")
            if len(fa) != len(fb):
                print("      (field count differs)")
        else:
            print(f"   {path}: {str(x)[:160]!r} -> {str(y)[:160]!r}")
