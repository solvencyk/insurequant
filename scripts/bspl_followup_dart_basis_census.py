#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""For every listed company and 2023.1Q / 2023.2Q: which DART table does the master's total assets (item 1) equal -- the SEPARATE (OFS) or the CONSOLIDATED
(CFS) statement?  (read-only)  Lists every table with 자산총계/부채총계/자본총계 of the report with its scaled total assets."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from scripts import build_equity_composition_tier2 as T  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

LISTED = ["KR0001", "KR0002", "KR0003", "KR0005", "KR0008", "KR0009", "KR0010", "KR0011", "KR0032", "KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0073",
          "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104", "KR1000"]
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs if r["값"] is not None}
side = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]

def num(s):
    s = str(s).strip().replace(",", "")
    if s in ("", "-"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v

only = set(sys.argv[1:])
for code in LISTED:
    if only and code not in only:
        continue
    for fy, q in (("FY2023_Q1", "2023.1Q"), ("FY2023_Q2", "2023.2Q")):
        dirs = sorted((ROOT / "data" / "dart" / fy / "raw").glob(f"{code}_*"))
        if not dirs:
            continue
        xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
        xml = xmls[0]
        raw_lines = xml.read_text(encoding="utf-8", errors="replace").split("\n")
        markers = T._unit_markers_by_line(raw_lines)
        bmarks = T._bs_basis_markers(raw_lines)
        m1 = mv.get((code, 1, q))
        src = "disclosure*" if f"{code}|1|{q}" in side else "DART/other"
        print(f"== {code} {q} master item1 = {m1} ({src})")
        for t in _iter_tables_with_context(xml):
            rows = {}
            for r in t.rows:
                if r and r[0]:
                    lab = re.sub(r"\s+", "", T._bs_label(r[0]))
                    if lab not in rows:
                        rows[lab] = [num(c) for c in r[1:4]]
            if not all(k in rows for k in ("자산총계", "부채총계", "자본총계")) or rows["자산총계"][0] is None:
                continue
            scale = T._find_unit(markers, t.line_no) or 1.0
            basis = T._find_basis(bmarks, t.line_no)
            raw = rows["자산총계"][0]
            cand = [raw * f for f in (1.0, 1e-3, 1e-6, 1e-8)]
            hit = [f for f, v in zip((1.0, 1e-3, 1e-6, 1e-8), cand) if m1 is not None and abs(v - m1) <= max(1.5, 0.0002 * abs(m1))]
            cap = (t.caption or "")[:50].replace("\n", " ")
            print(f"   line {t.line_no:>6} {str(basis):<4} assets_raw={raw:>20,.0f} {'<== EQUALS MASTER (factor %s)' % hit[0] if hit else ''} {cap!r}")
