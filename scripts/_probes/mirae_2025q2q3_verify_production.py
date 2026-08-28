"""Final verification: call the ACTUAL production _ma_yesilcha_direct() (post-edit) for
2025.2Q, 2025.3Q, and 2026.2Q (regression check) directly off raw XML. Read-only, no master
touched.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _iter_tables_by_basis  # noqa: E402
from scripts.pl_breakdown.companies import _ma_yesilcha_direct, extract_tier2_miraeasset  # noqa: E402

QUARTERS = [
    ("2025.2Q", ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml"),
    ("2025.3Q", ROOT / "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml"),
    ("2026.2Q(regression)", ROOT / "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml"),
]

for label, xml_path in QUARTERS:
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    item6 = _ma_yesilcha_direct(tables)
    out = extract_tier2_miraeasset(tables)
    print(f"{label}: _ma_yesilcha_direct = {item6}")
    print(f"  extract_tier2_miraeasset() -> {out}")
