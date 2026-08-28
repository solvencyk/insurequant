"""Dump the FULL header + all rows of whatever table _ma_find_product_table matches for the
ACT_NEEDLE row in KR0079 2025.2Q / 2025.3Q, to check whether the loose 사망보험+건강보험 header
cue is really matching the LRC/LIC rollforward note (as in 2026.2Q) or a false positive (both
product category names appear in MANY of this filer's notes, not just the one we want).
Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis  # noqa: E402
from scripts.pl_breakdown.companies import _MA_ACT4_ROW, _MA_EXP4_ROW  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402

QUARTERS = [
    ("2025.2Q", ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml"),
    ("2025.3Q", ROOT / "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml"),
]


def dump(label, xml_path):
    print(f"\n{'=' * 70}\n=== {label} ===")
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    ofs_tables = _prefer_ofs(tables)

    # replicate _ma_find_product_table's candidate gathering, but print ALL candidates
    # (not just the lowest line_no) so we can see what's being discarded too.
    for needle, tag in ((_MA_ACT4_ROW, "ACT"), (_MA_EXP4_ROW, "EXP")):
        cands = [t for t in ofs_tables
                  if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
                  and any(needle in "".join(r[:2]) for r in t.rows)]
        cands.sort(key=lambda t: t.line_no)
        print(f"\n  [{tag}] candidates matching needle={needle!r}: {len(cands)}")
        for t in cands:
            print(f"    line={t.line_no} caption={t.caption!r}")

        if cands:
            t = cands[0]
            print(f"\n  --- FULL DUMP of first {tag} candidate (line={t.line_no}) ---")
            print(f"  caption: {t.caption!r}")
            print(f"  header ({len(t.header)} row(s)):")
            for hrow in t.header:
                print(f"    {hrow}")
            print(f"  rows ({len(t.rows)}):")
            for i, r in enumerate(t.rows):
                print(f"    [{i}] {r}")


for label, path in QUARTERS:
    dump(label, path)
