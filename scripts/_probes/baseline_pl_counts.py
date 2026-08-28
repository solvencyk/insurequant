#!/usr/bin/env python3
"""Print row / company-quarter counts for the PL master files, before/after comparisons."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def report(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    cq = {(r["원보험사코드"], r["공시분기"]) for r in d}
    items = sorted({r["항목번호"] for r in d}, key=str)
    print(f"{path}: {len(d)} rows, {len(cq)} company-quarters, items={items}")
    return d, cq


if __name__ == "__main__":
    for p in sys.argv[1:]:
        report(p)
