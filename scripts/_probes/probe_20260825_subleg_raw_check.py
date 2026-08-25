# -*- coding: utf-8 -*-
"""sub_leg_gap 3건 raw 점검 -- 교보라이프플래닛 2024.4Q, BNP카디프 2024.4Q/2025.4Q 의
CSM/RA 분해 노트에서 PAA(보험료배분접근법) 등 item3/8 분해에서 빠질 수 있는 성분을 찾는다.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_subleg_raw_check.py
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

TARGETS = [
    ("교보라이프플래닛생명보험", "KR1010", "2024.4Q"),
    ("비엔피파리바카디프생명보험", "KR0075", "2024.4Q"),
    ("비엔피파리바카디프생명보험", "KR0075", "2025.4Q"),
]


def dirs_for(code, name, q):
    y, qq = q.split(".")
    qn = qq[0]
    base = ROOT / f"data/dart/FY{y}_Q{qn}/raw"
    return sorted(str(p) for p in base.glob(f"{code}_*") if p.is_dir())


def main() -> int:
    for name, code, q in TARGETS:
        dirs = dirs_for(code, name, q)
        print("\n" + "=" * 100)
        print(f"[{name} {q}]  dirs={dirs}")
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
        # PAA mentions anywhere
        paa_hits = 0
        for t in tables:
            capf = _norm(t.caption or "")
            if "보험료배분접근법" in capf or "PAA" in capf:
                paa_hits += 1
                print(f"  [PAA caption] {t.caption[:120]!r}")
        print(f"  PAA caption 언급: {paa_hits}건")

        # find CSM/RA rollforward-style tables (원수), dump fully
        cand = [t for t in tables if any(
            k in _norm(t.caption or "") for k in ("보험계약마진", "위험조정", "잔여보장"))]
        print(f"  CSM/RA 관련 caption 표 {len(cand)}건 (중복 캡션 스킵, 최초 3개만 전개)")
        seen_caps = set()
        shown = 0
        for t in cand:
            capkey = (t.caption or "")[:60]
            if capkey in seen_caps:
                continue
            seen_caps.add(capkey)
            if shown >= 5:
                continue
            shown += 1
            print(f"\n  -- caption={t.caption[:100]!r}  rows={len(t.rows)}")
            for r in t.rows:
                lab = _label(r)
                nums = _row_nums(r)
                if lab.strip() or nums:
                    print(f"      {lab!r:45s} nums={nums}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
