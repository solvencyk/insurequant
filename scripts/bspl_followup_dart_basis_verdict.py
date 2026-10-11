#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One verdict per listed company x (2023.1Q, 2023.2Q): is the master's total assets (item 1) equal to a SEPARATE (OFS) or a CONSOLIDATED (CFS) DART table? (read-only)"""
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

out = []
for code in LISTED:
    for fy, q in (("FY2023_Q1", "2023.1Q"), ("FY2023_Q2", "2023.2Q")):
        dirs = sorted((ROOT / "data" / "dart" / fy / "raw").glob(f"{code}_*"))
        if not dirs:
            continue
        xml = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)[0]
        raw_lines = xml.read_text(encoding="utf-8", errors="replace").split("\n")
        bmarks = T._bs_basis_markers(raw_lines)
        m1 = mv.get((code, 1, q))
        src = "disc" if f"{code}|1|{q}" in side else "dart"
        hits, ofs_assets, cfs_assets = [], None, None
        for t in _iter_tables_with_context(xml):
            rows = {}
            for r in t.rows:
                if r and r[0]:
                    lab = re.sub(r"\s+", "", T._bs_label(r[0]))
                    if lab not in rows:
                        rows[lab] = [num(c) for c in r[1:4]]
            if not all(k in rows for k in ("자산총계", "부채총계", "자본총계")) or rows["자산총계"][0] is None:
                continue
            basis = T._find_basis(bmarks, t.line_no)
            cap = t.caption or ""
            if not any(k in cap for k in ("요약", "재무상태표")):
                continue
            kind = "CFS" if (basis == "CFS" or "연결재무상태표" in cap and "별도" not in cap and "요약연결" in cap) else ("OFS" if basis == "OFS" else "?")
            raw = rows["자산총계"][0]
            if m1 is not None and abs(raw - m1) <= max(1.5, 0.0002 * abs(m1)):
                hits.append((t.line_no, kind, raw))
            if kind == "OFS" and ofs_assets is None:
                ofs_assets = raw
            if kind == "CFS" and cfs_assets is None:
                cfs_assets = raw
        kinds = {h[1] for h in hits}
        verdict = "NO_MATCH" if not hits else ("MATCH_CFS_ONLY" if kinds == {"CFS"} else ("MATCH_OFS" if "OFS" in kinds else "MATCH_UNKNOWN_BASIS"))
        out.append((code, q, src, verdict, m1, ofs_assets, cfs_assets, hits[:2]))
        print(f"{code} {q} [{src}] {verdict:<20} master {m1:,.0f}  | first OFS summary assets {ofs_assets}  first CFS summary assets {cfs_assets}  hits {hits[:2]}")
