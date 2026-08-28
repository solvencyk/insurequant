"""Read-only: verify _ofs_line_boundary / _tag_basis / _prefer_ofs correctly isolate the
별도 (OFS) section of the KR0079 2026.2Q filing, and that filtering to OFS-only leaves
exactly the target rows for item6's 표2/표3 (no 연결 duplicates left ambiguous).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import (  # noqa: E402
    _ofs_line_boundary, _tag_basis, _prefer_ofs, _iter_tables_by_basis,
)

XML = ROOT / "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml"

boundary = _ofs_line_boundary(XML)
print(f"_ofs_line_boundary = {boundary}")

tables = list(_tag_basis(list(_iter_tables_by_basis(XML, _iter_tables_with_context)), XML))
print(f"total tables: {len(tables)}")
basis_counts = {}
for t in tables:
    basis_counts[getattr(t, "_basis", None)] = basis_counts.get(getattr(t, "_basis", None), 0) + 1
print("basis counts:", basis_counts)

ofs_only = _prefer_ofs(tables)
print(f"ofs_only count: {len(ofs_only)}")

needle_exp = "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가"
needle_act = "발생한 보험금 및 기타 보험서비스비용"
exp_hits = [t.line_no for t in ofs_only if any(needle_exp in "".join(r[:2]) for r in t.rows)]
act_hits = [t.line_no for t in ofs_only if any(needle_act in "".join(r[:2]) for r in t.rows)]
print("exp_hits (OFS-only, line_no):", exp_hits)
print("act_hits (OFS-only, line_no):", act_hits)

# also show what CFS-only would have given, for contrast
cfs_only = [t for t in tables if getattr(t, "_basis", None) == "CFS"]
exp_hits_cfs = [t.line_no for t in cfs_only if any(needle_exp in "".join(r[:2]) for r in t.rows)]
print("exp_hits (CFS, for contrast):", exp_hits_cfs)

print("\n--- act_hits header content check ---")
for ln in act_hits:
    t = next(tb for tb in ofs_only if tb.line_no == ln)
    flat_header = " ".join(" ".join(hr) for hr in t.header)
    has_products = ("사망보험" in flat_header) and ("건강보험" in flat_header)
    print(f"line={ln}  has_5products={has_products}  header_sample={flat_header[:80]!r}")

print("\n--- exp_hits header content check ---")
for ln in exp_hits:
    t = next(tb for tb in ofs_only if tb.line_no == ln)
    flat_header = " ".join(" ".join(hr) for hr in t.header)
    print(f"line={ln}  header_sample={flat_header[:80]!r}")
