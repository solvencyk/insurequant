# -*- coding: utf-8 -*-
"""Dump kics_disclosure.json rows for a given (code, quarter, item) or (code, quarter)."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"


def main():
    code = sys.argv[1]
    q = sys.argv[2]
    items = set(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    rows = [r for r in data if r["원보험사코드"] == code and r["공시분기"] == q]
    rows.sort(key=lambda r: int(r["항목번호"]))
    for r in rows:
        it = int(r["항목번호"])
        if items and it not in items:
            continue
        print(f"item{it:>2} {r.get('항목명',''):<30} 값={r.get('값')!r:>12} 값_적용후={r.get('값_적용후')!r:>12}")


if __name__ == "__main__":
    raise SystemExit(main())
