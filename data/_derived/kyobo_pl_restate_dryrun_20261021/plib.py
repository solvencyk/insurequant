"""Read-only harness (KR0073 PL refresh dry run, 2026-10-21).

Reuses the production PL pipeline pieces (build_pl_breakdown.parse_filing / assemble, fetch_dart_fs._parse,
pl_breakdown.companies handlers) WITHOUT writing any repo file.  All monkeypatches live in the calling process only.

  parse_tables(dirs)                       production table list of a filing (separate/consolidated tagged)
  kyobo_picks(tables)                      the 4 note tables extract_tier2_kyobo picks (rev / cost / rerev / recost)
  t1_block(corp, year, reprt, prior)       Tier-1 dict from the cached FS-API json: prior=False -> thstrm (production), prior=True -> frmtrm columns
  kyobo_t2(tables, prior)                  Tier-2 dict of the production Kyobo handler; prior=True reads the PRIOR-period cumulative column
  block(later_q, prior)                    assembled 32-item vector for the filing of quarter `later_q` (prior=False reproduces production)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
os.chdir(ROOT)
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import build_pl_breakdown as BP  # noqa: E402
import fetch_dart_fs as F  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

CODE, NAME = "KR0073", "교보생명보험"
REPRT = {"1": "11013", "2": "11012", "3": "11014", "4": "11011"}
DART = ROOT / "data" / "dart"
_orig_first_num = C._life_first_num


def raw_dirs(q):
    fy = f"FY{q[:4]}_Q{q[5]}"
    return [str(d) for d in sorted((DART / fy / "raw").glob(f"{CODE}_*"))]


def corp_code(q):
    for d in raw_dirs(q):
        mp = Path(d) / "meta.json"
        if mp.exists():
            return json.loads(mp.read_text(encoding="utf-8")).get("corp_code")
    # some annual dirs (e.g. FY2025_Q4) carry no meta.json: same company, take the code from any other filing dir
    for mp in sorted(DART.glob(f"FY*_Q*/raw/{CODE}_*/meta.json")):
        return json.loads(mp.read_text(encoding="utf-8")).get("corp_code")
    return None


def parse_tables(dirs):
    tables = []
    for d in dirs:
        for x in BP._xmls_in(d):
            tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
    return tables


def t1_block(q, prior, divs=("OFS", "CFS")):
    """Tier-1 of the filing of quarter q.  prior=True: the comparative (frmtrm_*) columns are swapped into thstrm_*."""
    cc = corp_code(q)
    for div in divs:
        f = DART / "_fs_api_cache" / f"{cc}_{q[:4]}_{REPRT[q[5]]}_{div}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if prior:
            rows = []
            for a in d.get("list", []):
                b = dict(a)
                b["thstrm_amount"] = a.get("frmtrm_amount")
                b["thstrm_add_amount"] = a.get("frmtrm_add_amount")
                rows.append(b)
            d = {**d, "list": rows}
        t = F._parse(d, q[5] == "4" and not prior)
        if t:
            return t, div, f
    return None, None, None


def _prior_first_num(t, label_variants):
    """Prior-period CUMULATIVE cell of the first matching row.
    plain [당기, 전기] row (2 numbers) -> index 1;  [당기 3개월, 당기 누적, 전기 3개월, 전기 누적] (4 numbers) -> index 3."""
    if t is None:
        return None
    for r in t.rows:
        lf = C._life_label_flat(r)
        nums = C._row_nums(r)
        if not nums:
            continue
        for v in label_variants:
            if v.replace(" ", "") in lf:
                if len(nums) >= 4:
                    return nums[3]
                if len(nums) >= 2:
                    return nums[1]
                return None
    return None


def _with_alt_label(fn):
    """wrap a first-num reader so that the label '발생한보험서비스비용' also matches '발생한보험서비스수익' (same row, other wording)."""
    def inner(t, label_variants):
        v = fn(t, label_variants)
        if v is None and "발생한보험서비스비용" in label_variants:
            v = fn(t, [x if x != "발생한보험서비스비용" else "발생한보험서비스수익" for x in label_variants])
        return v
    return inner


def kyobo_t2(tables, prior, alt_label=False):
    base = _prior_first_num if prior else _orig_first_num
    C._life_first_num = _with_alt_label(base) if alt_label else base
    try:
        return C.extract_tier2_kyobo(tables)
    finally:
        C._life_first_num = _orig_first_num


def kyobo_picks(tables):
    def pick(cap_contains_all, must_row):
        for t in tables:
            cap = t.caption or ""
            if all(s in cap for s in cap_contains_all) and "당사" in cap and not C._life_is_rollforward(t):
                if must_row.replace(" ", "") in C._life_flat(t):
                    return t
        return None
    return {
        "rev": pick(("발행한 보험계약", "보험수익"), "당기손익에인식한보험계약마진"),
        "cost": pick(("발행한 보험계약", "보험서비스비용"), "보험계약에대한보험비용"),
        "rerev": pick(("재보험계약", "재보험수익"), "발생재보험금"),
        "recost": pick(("재보험계약", "재보험비용"), "보험계약마진상각"),
    }


def block(q, prior, tables=None, zero_fill_ok=frozenset(), alt_label=False):
    """assembled item vector (1..24 + OCI 25..32) for the filing of quarter q (prior=True -> comparative columns)."""
    t1, div, src = t1_block(q, prior)
    if tables is None:
        tables = parse_tables(raw_dirs(q))
    t2 = kyobo_t2(tables, prior, alt_label=alt_label)
    v = BP.assemble(t1, t2 or None, True, zero_fill_ok=zero_fill_ok)
    out = {n: v.get(n) for n in range(1, 33)}
    out["_reconciled"] = v.get("_reconciled")
    return out, {"t1_div": div, "t1_src": str(src.relative_to(ROOT)).replace("\\", "/") if src else None, "t1": t1, "t2": t2}
