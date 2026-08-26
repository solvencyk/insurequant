#!/usr/bin/env python3
"""Tier-1(포괄손익계산서) 에도 basis 필터가 없다 — 한화손해 2023.1Q 로 확인."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_pl_breakdown as BP
from scripts.pl_breakdown.common import _prefer_ofs, _tag_basis, _iter_tables_by_basis, _ofs_line_boundary
from scripts.pl_breakdown.tier1 import extract_tier1
from src.ifrs17.csm_extractor import _iter_tables_with_context

KEEP = (1, 15, 16, 17, 19, 20, 21, 22, 23, 24)
filings = BP.discover_filings()
for code, name, q in [("KR0002", "한화손해보험", "2023.1Q"), ("KR0002", "한화손해보험", "2023.2Q")]:
    dirs = filings[code][q]
    tables = []
    for d in dirs:
        for x in BP._xmls_in(d):
            print(f"   file={Path(x).name} boundary={_ofs_line_boundary(x)}")
            tables += _tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x)
    n_ofs = sum(1 for t in tables if getattr(t, "_basis", None) == "OFS")
    n_cfs = sum(1 for t in tables if getattr(t, "_basis", None) == "CFS")
    print(f"### {name} {q}  tables={len(tables)} OFS={n_ofs} CFS={n_cfs}")
    for tag, pool in (("현재(무필터)", tables), ("별도필터", _prefer_ofs(tables))):
        t1 = extract_tier1(pool, code=code) or {}
        v = {k: round(t1[k], 1) for k in KEEP if t1.get(k) is not None}
        i20, i21, i22 = t1.get(20), t1.get(21), t1.get(22)
        gap = None if None in (i20, i21, i22) else round(i22 - (i20 + i21), 1)
        print(f"  {tag:10s} {v}")
        print(f"  {'':10s} 세전이익 - (영업이익+영업외손익) = {gap}")
