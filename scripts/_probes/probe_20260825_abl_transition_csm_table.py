# -*- coding: utf-8 -*-
"""ABL생명 '전환방법별 CSM 변동표' (transition-method CSM rollforward) 테이블을 FY2024
Q1~Q3, FY2025 Q1~Q3 raw 에서 직접 찾아 통째로 덤프한다. 2026-08-17 override
(data/_gold/user_pl_cells.json)가 이 표의 '제공된 서비스 관련 당기손익 인식' 행 합계열을
근거로 2024.1Q~3Q 원수CSM상각을 22447/44994/66762 로 정정했다고 주장한다 — 그 raw 근거를
연도별로 직접 재현해 진짜 그 값이 그 표에 있는지 확인한다.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_abl_transition_csm_table.py
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
from scripts.pl_breakdown.tier2 import _norm, _row_nums, _label, _is_rollforward  # noqa: E402

CODE = "KR0070"
NAME = "에이비엘생명보험"
QUARTERS = ["2023.1Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q",
            "2025.1Q", "2025.2Q", "2025.3Q"]


def dirs_for(q):
    y, qq = q.split(".")
    qn = qq[0]
    d = ROOT / f"data/dart/FY{y}_Q{qn}/raw/{CODE}_{NAME}"
    return [str(d)] if d.exists() else []


def main() -> int:
    for q in QUARTERS:
        dirs = dirs_for(q)
        print("\n" + "=" * 100)
        print(f"[{NAME} {q}]  dirs={dirs}")
        print("=" * 100)
        if not dirs:
            print("  NO RAW DIR")
            continue
        tables = []
        for d in dirs:
            xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
            xs = sorted(set(xs), key=lambda p: os.path.getsize(p), reverse=True)
            for x in xs:
                try:
                    tables.extend(_iter_tables_with_context(Path(x)))
                except Exception as e:
                    print(f"  ERR {x}: {e}")
        # find candidate tables whose caption mentions 전환 (transition) + CSM related terms
        cand = [t for t in tables if "전환" in _norm(t.caption or "")]
        print(f"  caption 에 '전환' 포함 표 {len(cand)}건")
        for t in cand:
            print(f"\n  -- caption={t.caption!r}  rollforward?={_is_rollforward(t)}  rows={len(t.rows)}")
            for r in t.rows:
                lab = _label(r)
                nums = _row_nums(r)
                if "서비스" in lab or "당기손익" in lab or "인식" in lab or "제공" in lab or nums:
                    print(f"      {lab!r:55s} nums={nums}")
        # Also broad-search any table (regardless of caption) with a row label containing
        # '제공된 서비스' or '당기손익' + '인식' as a fallback net.
        cand2 = []
        for t in tables:
            for r in t.rows:
                lab = _label(r)
                if "제공된서비스" in lab.replace(" ", "") and "당기손익" in lab.replace(" ", ""):
                    cand2.append((t, r))
        if cand2:
            print(f"\n  광역검색: caption 무관, 행라벨 '제공된 서비스...당기손익...' 매치 {len(cand2)}건")
            for t, r in cand2:
                print(f"    caption={t.caption!r}  label={_label(r)!r}  nums={_row_nums(r)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
