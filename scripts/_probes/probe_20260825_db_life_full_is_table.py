# -*- coding: utf-8 -*-
"""DB생명보험 2023.1Q '(2) 요약포괄손익계산서' 56행 표 전체를 순서대로 덤프
(계층 파악을 위해 필터링 없이 전 행).

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_db_life_full_is_table.py
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
from scripts.pl_breakdown.tier2 import _label, _row_nums  # noqa: E402

d = str(ROOT / "data/dart/FY2023_Q1/raw/KR0082_DB생명보험")


def main() -> int:
    tables = []
    xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
    xs = sorted(set(xs), key=lambda p: os.path.getsize(p), reverse=True)
    for x in xs:
        try:
            tables.extend(_iter_tables_with_context(Path(x)))
        except Exception as e:
            print(f"ERR {x}: {e}")
    for t in tables:
        if len(t.rows) == 56 and "요약포괄손익계산서" in (t.caption or ""):
            print(f"caption={t.caption!r}")
            for i, r in enumerate(t.rows):
                print(f"  [{i:2d}] {_label(r)!r:60s} nums={_row_nums(r)}")
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
