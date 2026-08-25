# -*- coding: utf-8 -*-
"""lob_sum_gap 5건의 raw 원문에서 '포괄손익계산서'(income statement) 표를 찾아
기타영업수익/기타사업비용 관련 행을 전부 덤프한다. item16(기타사업비용)=None 인 경우
그 라벨이 원문에 정말 없는지, 있는데 놓쳤는지 확인.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_lobsumgap_raw_search.py
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
    ("DB생명보험", "KR0082", "2023.1Q"),
    ("메리츠화재해상보험", "KR0001", "2023.1Q"),
    ("메리츠화재해상보험", "KR0001", "2023.2Q"),
    ("DB손해보험", "KR0011", "2023.2Q"),
    ("흥국화재", "KR0005", "2025.1Q"),
]


def dirs_for(code, name, q):
    y, qq = q.split(".")
    qn = qq[0]
    d = ROOT / f"data/dart/FY{y}_Q{qn}/raw/{code}_{name}"
    return [str(d)] if d.exists() else []


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
        # find income-statement-like tables (caption contains 포괄손익 or has 보험손익/영업이익 rows)
        hits = []
        for t in tables:
            capf = _norm(t.caption or "")
            row_labels = [_label(r) for r in t.rows]
            has_key_rows = any(("보험손익" in lb or "영업이익" in lb or "보험영업" in lb) for lb in row_labels)
            if "포괄손익계산서" in capf or has_key_rows:
                hits.append(t)
        print(f"  income-statement 후보 표 {len(hits)}건")
        for t in hits:
            print(f"\n  -- caption={t.caption[:80]!r}...  rows={len(t.rows)}")
            for r in t.rows:
                lab = _label(r)
                if "기타" in lab or "영업수익" in lab or "영업비용" in lab or "사업비" in lab \
                        or "보험손익" in lab or "영업이익" in lab:
                    print(f"      {lab!r:50s} nums={_row_nums(r)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
