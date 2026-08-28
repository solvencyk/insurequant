"""For KR0079 2025.2Q / 2025.3Q, list every OFS table whose header carries the 5-product cue
(사망보험+건강보험), near the ACT (발생측) table found by mirae_2025q2q3_dump_tact.py, to search
for an EXP-side (예상측 7-component) note under a differently-worded exact label before
concluding the note is absent (per ticket: verify per-quarter, don't assume from 2026.1Q/
2025.4Q precedent). Prints caption + all row[0]/row[1] labels for each candidate table so a
human can visually scan for a 7-component P&L-shaped table near the LRC/LIC rollforward.
Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis, _norm  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402

QUARTERS = [
    ("2025.2Q", ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml"),
    ("2025.3Q", ROOT / "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml"),
]


def scan(label, xml_path):
    print(f"\n{'=' * 70}\n=== {label} ===")
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    ofs_tables = _prefer_ofs(tables)

    cands = [t for t in ofs_tables
              if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)]
    cands.sort(key=lambda t: t.line_no)
    print(f"  {len(cands)} OFS tables with 사망보험+건강보험 header cue:")
    for t in cands:
        row_labels = [(_norm(r[0]) if r else "", _norm(r[1]) if len(r) > 1 else "") for r in t.rows]
        print(f"\n  --- line={t.line_no}  caption={t.caption!r}  n_rows={len(t.rows)} "
              f"n_header_rows={len(t.header)} ---")
        print(f"    header[-2:]={t.header[-2:] if len(t.header) >= 2 else t.header}")
        for lbl0, lbl1 in row_labels:
            print(f"    row: [{lbl0!r}, {lbl1!r}]")


for label, path in QUARTERS:
    scan(label, path)
