"""Library (read-only dry run): read a LATEST-comparative PL block (items 1..32) of a company-quarter from the next-year filing.

 * Tier-1  : DART FS-API cache of the later filing, comparative columns (frmtrm_* swapped into thstrm_*), OFS first then CFS (production basis = 별도).
 * Tier-2  : production Tier-2 chain (build_pl_breakdown.parse_filing) with the comparative-column flips described in s76:
              companies._old_prior negated  (삼성/DB 'pre-2025.2Q 구분-rows' readers keep the 전기/전반기/전분기 tables)
              tier2._b_note_table -> second '보험손익 상세내역' table (메리츠 Format-B prints 당기 first, 전기 second)
 * optional patch 'sumcheck_lobcum': an irregular (dropped-zero) 재보 합계 row is resolved ONLY when exactly one slot assignment reproduces
              both the 3개월-sum and the 누적-sum identities (otherwise the production reader is kept) - dry-run-only, production code untouched.
All monkeypatches live in this process only.
"""
from __future__ import annotations

import itertools
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.chdir(ROOT)
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import build_pl_breakdown as BP  # noqa: E402
import fetch_dart_fs as F  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402
from scripts.pl_breakdown import tier2 as T2  # noqa: E402

REPRT = {"1": "11013", "2": "11012", "3": "11014", "4": "11011"}
LIFE = {"KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0073", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104"}
_orig_old_prior = C._old_prior
_orig_b = T2._b_note_table
_orig_lobcum = C._old_lobcum


def second_b(tables):
    seen = 0
    for t in tables:
        if "보험손익" in (t.caption or "") and "상세내역" in (t.caption or ""):
            if any(T2._row_matches(r, T2.B_CSM) for r in t.rows):
                seen += 1
                if seen == 2:
                    return t
    return None


def sumcheck_lobcum(total_nums, order, pres, st=2, _trace=None):
    """Exact-arithmetic resolver for a SHORT paired (st=2) total row; falls back to the production reader when not unique."""
    if st != 2 or not total_nums:
        return _orig_lobcum(total_nums, order, pres, st)
    full = (len(order) + 1) * 2
    k = len(total_nums)
    if k >= full or k < 2:
        return _orig_lobcum(total_nums, order, pres, st)
    miss = full - k
    sols = []
    slots = list(range(full))
    for dropped in itertools.combinations(slots, miss):
        vals = [None] * full
        it = iter(total_nums)
        for s in slots:
            vals[s] = 0.0 if s in dropped else next(it)
        m3 = sum(vals[2 * i] for i in range(len(order)))
        cm = sum(vals[2 * i + 1] for i in range(len(order)))
        if abs(m3 - vals[-2]) <= 1.0 and abs(cm - vals[-1]) <= 1.0:
            sols.append(tuple(vals))
    sols = list(dict.fromkeys(sols))
    if len(sols) == 1:
        vals = sols[0]
        if _trace is not None:
            _trace.append(("sumcheck-unique", total_nums, vals))
        return {lob: vals[2 * i + 1] for i, lob in enumerate(order)}
    if _trace is not None:
        _trace.append((f"sumcheck-{len(sols)}-solutions", total_nums, None))
    return _orig_lobcum(total_nums, order, pres, st)


def corp_of(kr, fy):
    for d in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*")):
        mp = d / "meta.json"
        if mp.exists():
            return json.loads(mp.read_text(encoding="utf-8")).get("corp_code")
    return None


def t1_prior(corp, year, reprt, divs=("OFS", "CFS")):
    for div in divs:
        f = ROOT / "data/dart/_fs_api_cache" / f"{corp}_{year}_{reprt}_{div}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        rows = []
        for a in d.get("list", []):
            b = dict(a)
            b["thstrm_amount"] = a.get("frmtrm_amount")
            b["thstrm_add_amount"] = a.get("frmtrm_add_amount")
            rows.append(b)
        t = F._parse({**d, "list": rows}, False)
        if t:
            return t, div
    return None, None


def latest_block(kr, name, later, sumcheck=False, trace=None):
    """-> (assembled {1..24} + tier1 extras {25..32}, tier1_basis, t2_raw)"""
    is_life = kr in LIFE
    fy = f"FY{later[:4]}_Q{later[5]}"
    dirs = [str(d) for d in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))]
    corp = corp_of(kr, fy)
    t1, div = t1_prior(corp, later[:4], REPRT[later[5]])
    C._old_prior = lambda tbls, i, _o=_orig_old_prior: not _o(tbls, i)
    T2._b_note_table = second_b
    if sumcheck:
        C._old_lobcum = lambda tn, o, p, st=2: sumcheck_lobcum(tn, o, p, st, trace)
    try:
        _t1x, t2 = BP.parse_filing(dirs, is_life, kr, name, later)
    finally:
        C._old_prior = _orig_old_prior
        T2._b_note_table = _orig_b
        C._old_lobcum = _orig_lobcum
    v = BP.assemble(t1, t2, is_life)
    return v, div, t2
