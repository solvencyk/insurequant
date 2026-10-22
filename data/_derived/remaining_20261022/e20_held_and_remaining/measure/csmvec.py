# -*- coding: utf-8 -*-
"""csmvec: latest-comparative CSM vectors (억원, items 1..6) per (company, quarter): the 2026-10-12 dry-run scan (csm_prior_scan_v2.csv) with the corrections found by
the e20 independent readers.  READ-ONLY.
prior(code,q) -> list[6] | None (no change / not readable).   status(code,q) -> 'SAME'|'DIFF'|'NO_PRIOR'|'OVERRIDE_SAME'|'OVERRIDE_DIFF'"""
from __future__ import annotations

import csv
from pathlib import Path

SCAN = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/csm_prior_scan_v2.csv")
_rows = {}
with open(SCAN, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        _rows[(r["kr"], r["prior_q"])] = r


def _vec(r, pre):
    out = []
    for i in range(1, 7):
        x = r.get(f"{pre}{i}")
        out.append(float(x) if x not in (None, "") else None)
    return out


# e20 corrections (independent readers; evidence file in brackets)
OVERRIDE = {
    # FY2025 annual prior (2024) == master: dry-run misread (chain_ok False)           [c4_KR0070_FY2025_Q4.txt, c5 output for KR0003]
    ("KR0070", "2024.4Q"): "SAME",
    ("KR0003", "2024.4Q"): "SAME",
    # 푸본현대 FY2025 annual: six product tables, prior == master                     [c2_KR0083_FY2025_Q4.txt]
    ("KR0083", "2024.4Q"): "SAME",
    # 미래에셋 FY2024 annual/quarterlies: 당기/전기 are row blocks inside one table    [c3_KR0079_FY2024_Q*.txt]
    ("KR0079", "2023.1Q"): "SAME", ("KR0079", "2023.2Q"): "SAME", ("KR0079", "2023.3Q"): "SAME", ("KR0079", "2023.4Q"): "SAME",
    ("KR0079", "2024.1Q"): [20214.5, 962.0, 118.2, 138.1, -507.6, 20925.2],
    # 현대해상 FY2024 annual '(2) 전기' table L76716 (천원): opening 8,351,537,263 new 1,679,236,885 int 263,632,290 amort -880,544,843 close 9,142,271,139
    ("KR0009", "2023.4Q"): [83515.4, 16792.4, 2636.3, -2716.0, -8805.4, 91422.7],
}


def prior(code: str, q: str):
    k = (code, q)
    if k in OVERRIDE:
        o = OVERRIDE[k]
        return None if o == "SAME" else list(o)
    r = _rows.get(k)
    if r is None or r["status"] != "DIFF":
        return None
    return _vec(r, "p")


def master_scan(code: str, q: str):
    r = _rows.get((code, q))
    return None if r is None else _vec(r, "m")


def status(code: str, q: str) -> str:
    k = (code, q)
    if k in OVERRIDE:
        return "OVERRIDE_SAME" if OVERRIDE[k] == "SAME" else "OVERRIDE_DIFF"
    r = _rows.get(k)
    return "-" if r is None else r["status"]
