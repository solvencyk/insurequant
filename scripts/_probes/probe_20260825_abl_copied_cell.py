# -*- coding: utf-8 -*-
"""ABL생명(KR0070) 원수CSM상각 copied-cell 진단.

FY2024 Q1~Q3 배포본 값이 FY2025 Q1~Q3 와 완전히 같다. 원인 후보:
  A. 당기/전기 컬럼 순서가 분기보고서(반기/3분기)에서 뒤집혀 있어 잘못된 컬럼을 읽는다
  B. FY2024 raw 에 담긴 표 자체가 이미 FY2025 숫자를 담고 있다(원본 문제)
  C. 파서가 엉뚱한 표/캡션을 골랐다

각 분기의 '잔여보장' 표를 통째로 덤프하고, dangi() 가 실제로 무엇을 골랐는지 재현한다.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_abl_copied_cell.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.build_pl_breakdown import discover_filings, parse_filing  # noqa: E402
from scripts.pl_breakdown.tier2 import _is_rollforward, _norm, _row_nums, _label  # noqa: E402

CODE = "KR0070"
NAME = "에이비엘생명보험"
QUARTERS = ["2024.1Q", "2024.2Q", "2024.3Q", "2025.1Q", "2025.2Q", "2025.3Q"]


def dump_table(t, tag):
    print(f"    -- table caption={t.caption!r} rows={len(t.rows)}")
    for r in t.rows:
        lab = _label(r)
        nums = _row_nums(r)
        if nums or lab.strip():
            print(f"    [{tag}] {lab!r:60s} nums={nums}")


def main() -> int:
    filings = discover_filings()
    dirs_by_q = filings.get(CODE, {})
    for q in QUARTERS:
        dirs = dirs_by_q.get(q)
        print("\n" + "=" * 100)
        print(f"[{NAME} {q}]  dirs={dirs}")
        print("=" * 100)
        if not dirs:
            print("  NO RAW DIRS FOUND")
            continue
        # Re-run parse_filing (life) to get t2 result
        t1, t2 = parse_filing(dirs, is_life=True, code=CODE, name=NAME, quarter=q)
        print(f"  t2 result: {t2}")

        # Now dump the underlying tables directly to see the 잔여보장 note.
        import glob
        from src.ifrs17.csm_extractor import _iter_tables_with_context
        tables = []
        for d in dirs:
            xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
            xs = sorted(set(xs), key=lambda p: __import__("os").path.getsize(p), reverse=True)
            for x in xs:
                try:
                    tables.extend(_iter_tables_with_context(Path(x)))
                except Exception as e:
                    print(f"  ERR parsing {x}: {e}")
        cand = []
        for t in tables:
            if _is_rollforward(t):
                continue
            capf = _norm(t.caption or "").replace(" ", "")
            needs = ["잔여보장", "회수", "보험수익"]
            excl = ["재보험"]
            if all(n in capf for n in needs) and not any(e in capf for e in excl):
                cand.append(t)
        print(f"  matched {len(cand)} '보험수익' 잔여보장 table(s)")
        for t in cand:
            dump_table(t, q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
