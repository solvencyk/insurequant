"""Read-only probe, ticket case DB손해보험 KR0011 2023.1Q-3Q (CSM_AMORT_IDENTITY pins, cause RESTATEMENT_BASIS):
read the Tier-2 PL note (extract_tier2_db = the production handler) from the 2024.1Q-3Q filings TWICE - as printed (current-year columns) and with the
period markers swapped (-> the prior-year columns, i.e. the latest comparative of 2023.1Q-3Q) - and compare with the PL master and the CSM waterfall.

The marker swap only exchanges the one-row period-marker tables ('전기','전반기','전분기' <-> '당기','당반기','당분기'); the handler's own
is_prior() then treats the comparative tables as current.  No production code or data is modified.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis, _norm  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402

PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
CUR = {"당기", "당반기", "당분기", "당기말"}


def load_tables(rd):
    xs = sorted(set(list(rd.glob("*.xml")) + list(rd.glob("xml/*.xml"))), key=lambda p: p.stat().st_size, reverse=True)
    tables = []
    for x in xs:
        tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
    return tables


def swap_markers(tables):
    n = 0
    for t in tables:
        if t.rows and len(t.rows) <= 1 and t.rows[0]:
            first = _norm(t.rows[0][0])
            if first in PRIOR:
                t.rows[0][0] = "당기"
                n += 1
            elif first in CUR:
                t.rows[0][0] = "전기"
                n += 1
    return n


pl = {(r["공시분기"], r["항목번호"]): r["값"] for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0011"}
wf = {(r["공시분기"], r["항목번호"]): r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0011"}
print("master PL item4 (원수CSM상각, 백만원) 2023.1Q/2Q/3Q:", [pl.get((q, 4)) for q in ("2023.1Q", "2023.2Q", "2023.3Q")])
print("master WF item5 (CSM상각, 억원)       2023.1Q/2Q/3Q:", [wf.get((q, 5)) for q in ("2023.1Q", "2023.2Q", "2023.3Q")])
res = {}
for later, prior_q in (("2024.1Q", "2023.1Q"), ("2024.2Q", "2023.2Q"), ("2024.3Q", "2023.3Q")):
    rd = next((ROOT / "data/dart" / f"FY{later[:4]}_Q{later[5]}" / "raw").glob("KR0011_*"))
    tables = load_tables(rd)
    t_cur = C.extract_tier2_old(tables)                       # what the production chain falls back to for DB 2024.xQ (extract_tier2_db returns {})
    orig_prior = C._old_prior
    C._old_prior = lambda tbls, i: not orig_prior(tbls, i)     # flip: keep only the comparative (전분기/전반기) tables
    try:
        t_pri = C.extract_tier2_old(tables)
    finally:
        C._old_prior = orig_prior
    nsw = 0
    keys = (4, 5, 6, 9, 10, 11, 13, 14, "_jang_rev", "_jang_cost")
    print("=" * 100)
    print(f"{later} filing: markers swapped={nsw}")
    print("  current-year columns :", {k: (round(t_cur.get(k), 1) if isinstance(t_cur.get(k), (int, float)) else None) for k in keys})
    print("  prior-year  columns  :", {k: (round(t_pri.get(k), 1) if isinstance(t_pri.get(k), (int, float)) else None) for k in keys})
    print(f"  master PL {prior_q}  :", {k: (round(pl.get((prior_q, k)), 1) if isinstance(pl.get((prior_q, k)), (int, float)) else None) for k in (4, 5, 6, 9, 10, 11, 13, 14)})
    print(f"  master PL {later}   :", {k: (round(pl.get((later, k)), 1) if isinstance(pl.get((later, k)), (int, float)) else None) for k in (4, 5, 6, 9, 10, 11, 13, 14)})
    res[later] = {"current": {str(k): t_cur.get(k) for k in keys}, "prior": {str(k): t_pri.get(k) for k in keys},
                  "master_prior_q": {str(k): pl.get((prior_q, k)) for k in (4, 5, 6, 9, 10, 11, 13, 14)}}
    amort_pl = t_pri.get(4)
    print(f"  --> prior-column 원수CSM상각 {amort_pl} 백만원 = {None if amort_pl is None else round(amort_pl/100.0, 2)} 억원  vs CSM waterfall(master, restated) {wf.get((prior_q, 5))} 억원")
(HERE / "db_pl_prior_probe.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
