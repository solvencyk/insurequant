"""Full dump (header + ALL row cells, not just col0/col1 labels) of the 7-component
'구성요소별 보험계약' candidate table found near the ACT table for KR0079 2025.2Q/2025.3Q, to
determine its true column width/shape before computing anything from it. Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402

QUARTERS = [
    ("2025.2Q", ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml"),
    ("2025.3Q", ROOT / "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml"),
]

ALT_NEEDLE = "발생한 보험금 및 그 밖의 발생한 보험서비스비용에 따른 증가분"


def dump(label, xml_path):
    print(f"\n{'=' * 70}\n=== {label} ===")
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    ofs_tables = _prefer_ofs(tables)

    cands = [t for t in ofs_tables
              if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
              and any(ALT_NEEDLE in "".join(r[:2]) for r in t.rows)]
    cands.sort(key=lambda t: t.line_no)
    print(f"  {len(cands)} candidates for ALT_NEEDLE")
    for t in cands:
        print(f"\n  --- line={t.line_no} caption={t.caption!r} ---")
        print(f"  header ({len(t.header)} rows):")
        for hrow in t.header:
            print(f"    {hrow}")
        print(f"  rows ({len(t.rows)}):")
        for i, r in enumerate(t.rows):
            print(f"    [{i}] len={len(r)} {r}")


for label, path in QUARTERS:
    dump(label, path)
