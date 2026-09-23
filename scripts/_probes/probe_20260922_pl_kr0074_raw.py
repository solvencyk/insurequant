# -*- coding: utf-8 -*-
"""KR0074(라이나생명) FY2023 감사보고서 원문에서 포괄손익계산서 표를 찾아 그대로 인쇄한다.

읽기 전용. 2024.4Q·2025.4Q 는 _GOLD_CELL_OVERRIDE 로 채워져 있고 2023.4Q 만 비어 있어서,
같은 표가 원문에 실제로 있는지, 라벨이 어떻게 다른지 눈으로 보려는 목적.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

XML = sys.argv[1] if len(sys.argv) > 1 else (
    "data/dart/FY2023_Q4/raw/KR0074_라이나생명보험_20240409003674/20240409003674_00760.xml")
NEEDLE = sys.argv[2] if len(sys.argv) > 2 else "포괄손익계산서"

hits = 0
for t in _iter_tables_with_context(XML):
    ctx, tbl = t.caption, (t.header or []) + (t.rows or [])
    flat = " ".join(" ".join(str(c) for c in row) for row in tbl)
    blob = (ctx or "") + " " + flat
    if NEEDLE not in blob:
        continue
    hits += 1
    print("=" * 100)
    print(f"[{hits}] ctx: {(ctx or '')[:240]}")
    print(f"    rows={len(tbl)}")
    for row in tbl[:60]:
        cells = [str(c).strip() for c in row]
        if any(cells):
            print("      " + " | ".join(cells))
    if hits >= 4:
        break
print(f"\n표 {hits}개")
