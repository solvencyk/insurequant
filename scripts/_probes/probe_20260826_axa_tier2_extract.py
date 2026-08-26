# -*- coding: utf-8 -*-
"""악사 2023.4Q 에서 `extract_tier2_axa` 가 정확히 어디서 죽는지 (validation, 2026-08-26).

성공하는 2024.4Q 와 나란히 돌려 차이만 인쇄한다. 파서에게 '노트가 있다' 만 넘기면
같은 자리를 다시 뒤지게 되므로 실패 지점까지 특정해 넘긴다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from pl_breakdown.common import _iter_tables_by_basis, _prefer_ofs, _tag_basis  # noqa: E402
from pl_breakdown.companies import extract_tier2_axa  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

FILES = {
    "2023.4Q(RED)": "data/dart/FY2023_Q4/raw/KR0049_악사손해보험_20240402002008/20240402002008_00760.xml",
    "2024.4Q(성공)": "data/dart/FY2024_Q4/raw/KR0049_악사손해보험_20250407003441/20250407003441_00760.xml",
}


def main() -> None:
    for label, rel in FILES.items():
        p = ROOT / rel
        tables = list(_iter_tables_by_basis(p, _iter_tables_with_context))
        tables = _prefer_ofs(_tag_basis(tables, p))
        print(f"\n{'=' * 78}\n{label}  tables={len(tables)}\n{'=' * 78}")
        hits = [t for t in tables if "보험손익상세내역" in (t.caption or "").replace(" ", "")]
        print(f"캡션 '보험손익상세내역' 매칭 표 = {len(hits)}")
        for i, t in enumerate(hits):
            print(f"\n  [{i}] caption={t.caption!r}")
            print(f"      rows={len(t.rows)}  header={t.header}")
            for r in t.rows[:6]:
                print(f"        {r}")
        got = extract_tier2_axa(tables)
        print(f"\n  extract_tier2_axa -> {got}")


if __name__ == "__main__":
    main()
