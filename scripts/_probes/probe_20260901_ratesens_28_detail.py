"""Read-only detail dump for the 28-company FY2026_Q2 rate-sensitivity scoped run:
per-company diag + emitted row values, so they can be eyeballed against the hand
derivation before anything gets written to the master.

Usage: PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
       scripts/_probes/probe_20260901_ratesens_28_detail.py
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import extract_kics_rate_sensitivity as ex  # noqa: E402

PERIOD = "FY2026_Q2"
QUARTER = "2026.2Q"
CODES = """KR0001 KR0003 KR0004 KR0009 KR0011 KR0029 KR0032 KR0051 KR0068 KR0069
KR0070 KR0071 KR0072 KR0073 KR0079 KR0080 KR0082 KR0083 KR0087 KR0094
KR0097 KR0099 KR0100 KR0104 KR0150 KR1010 KR1011 KR1098""".split()

disc = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
prefix = {}
anchor = {}
for r in disc:
    prefix.setdefault(r["원보험사코드"], {
        "원보험사코드": r["원보험사코드"], "원수사명": r["원수사명"],
        "티커": r["티커"], "생손보여부": r["생손보여부"]})
    if r["항목번호"] in (1, 14, 27):
        anchor[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = ex.parse_value(str(r["값"]))
anchor_item = {"지급여력금액": 1, "지급여력기준금액": 14, "지급여력비율": 27}

for code in CODES:
    name = prefix.get(code, {}).get("원수사명", code)
    md = ex.pick_md(code, PERIOD)
    tbl = ex.find_section_table(Path(md).read_text(encoding="utf-8")) if md else None
    method = "md"
    if not tbl:
        fb = ex.extract_from_raw_pdf(code, PERIOD)
        if fb is not None:
            rows = fb
            method = "pdf_fallback"
        else:
            ov = ex.MANUAL_OVERRIDE.get((code, QUARTER))
            if ov is not None:
                rows = []
                for ph, measures in ov.items():
                    for m, vals in measures.items():
                        rows.append((ph, m, list(vals)))
                method = "manual_override"
            else:
                print(f"{code:8s} {name:16s} ABSENT (no md table, no fallback)")
                continue
    else:
        rows = ex.measure_rows(tbl)
    blocks = ex.split_blocks(rows)
    assigned = []
    for blk in blocks:
        ph = ex.block_phase(blk)
        if ph is None:
            ph = "적용전" if not any(p == "적용전" for p, _ in assigned) else "적용후"
        assigned.append((ph, ex.block_dict(blk)))
    print(f"{code:8s} {name:16s} method={method:16s} n_blocks={len(blocks)}")
    for ph, d in assigned:
        if d is None:
            print(f"    {ph}: EMPTY (all-dash)")
            continue
        rd, enc = ex.resolve_block(d)
        print(f"    {ph} [{enc}]:")
        for m, vals in rd.items():
            print(f"       {m:10s} {vals}")
        if ph == "적용전":
            for m, item in anchor_item.items():
                a = anchor.get((code, QUARTER, item))
                bv = rd.get(m, [None])[0]
                if a is not None and bv is not None:
                    tol = 0.5 if m == "지급여력비율" else 2.0
                    flag = "OK" if abs(a - bv) <= tol else f"DIFF(Δ{a-bv:+.2f})"
                    print(f"         RS2 vs disclosure item: {m} base={bv} disclosure={a}  {flag}")
