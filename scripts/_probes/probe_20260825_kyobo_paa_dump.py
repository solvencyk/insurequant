# -*- coding: utf-8 -*-
"""교보라이프플래닛 2024.4Q PAA(보험료배분접근법) 표 전개 -- item3(생명장기원수손익)이
CSM/RA 노트(item4-7)만으로 6,261.42 모자란 이유가 PAA 별도 버킷인지 확인.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_kyobo_paa_dump.py
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.tier2 import _norm, _row_nums, _label  # noqa: E402

base = ROOT / "data/dart/FY2024_Q4/raw"
dirs = sorted(str(p) for p in base.glob("KR1010_*") if p.is_dir())
print("dirs:", dirs)


def main() -> int:
    tables = []
    for d in dirs:
        xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
        xs = sorted(set(xs), key=lambda p: os.path.getsize(p), reverse=True)
        for x in xs:
            try:
                tables.extend(_iter_tables_with_context(Path(x)))
            except Exception as e:
                print(f"ERR {x}: {e}")
    seen = set()
    for t in tables:
        capf = _norm(t.caption or "")
        if "보험료배분접근법" not in capf:
            continue
        cap60 = (t.caption or "")[:60]
        if cap60 in seen:
            continue
        seen.add(cap60)
        print(f"\n-- caption={t.caption[:100]!r}  rows={len(t.rows)}")
        for r in t.rows:
            lab = _label(r)
            nums = _row_nums(r)
            if lab.strip() or nums:
                print(f"    {lab!r:45s} nums={nums}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
