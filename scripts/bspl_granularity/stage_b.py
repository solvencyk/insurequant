# -*- coding: utf-8 -*-
"""Stage B: from extracted disclosure tables to calibrated, guarded BS cell candidates.

Inputs  : Stage-A table JSON (data/_derived/bspl_granularity_20261011/tables/<KR>_<q>.json), IFRS17_BS.json (read-only),
          bs_from_disclosure.json sidecar (to tell disclosure-sourced master cells from DART/owner cells).
Output  : in-memory structures; the CLI wrapper (scripts/bspl_granularity_candidates.py) writes JSON.

A cell is LOADED only if all hold
  1. its mapping concept (item <- canonical label(s) of a table) is *calibrated* for that company: it reproduces the
     company's DART/owner-sourced master value at every quarter where both exist (current column; for full statements
     also the prior-year-end column against the previous Q4 master value; for equity tables the two previous quarters),
     or no anchor exists and the item/table form is on the SAFE_UNTESTED list,
  2. the unit is verified against the master's own totals (items 1/2/3) or the printed caption (no master),
  3. the table's identities close (assets = liabilities + equity),
  4. the value passes a QoQ plausibility gate against the nearest known values,
  5. the master cell is empty (existing values are never touched; differing values are reported as conflicts).
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .views import view_all, cur, col

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "tables"

UNIT_FACTOR = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0, "억원": 100.0}
# printed-rounding half step (백만원) and the matching tolerance (a printed total can be off by one unit of rounding)
UNIT_PREC = {"원": 5e-7, "천원": 5e-4, "백만원": 0.5, "억원": 50.0}
UNIT_TOL = {"원": 0.02, "천원": 0.05, "백만원": 1.0, "억원": 100.5}
FORBIDDEN_ANCHOR_Q = {"2021.4Q", "2022.4Q"}
# (company, quarter) master cells that are known not to be on the disclosure's basis: never used as anchors
ANCHOR_EXCLUDE = {("KR0004", "2025.4Q")}      # DART 엠지 FY2025 (728억) vs 예별 경영공시 (38,191억): 계약이전 비교 단절

# concept = (item, labels, mode); evaluated on every applicable table kind
CONCEPTS = [
    (10, ("현금및예치금",), "first"), (10, ("현금및현금성자산",), "first"),
    (11, ("FVPL",), "first"), (11, ("FVPL",), "sum_all"),
    (12, ("FVOCI",), "first"), (12, ("FVOCI",), "sum_all"),
    (13, ("AC_SEC",), "first"), (13, ("AC_FA",), "first"), (13, ("AC_SEC", "대출채권"), "first"),
    (13, ("AC_CHILDREN",), "ac_children"),
    (14, ("재보험계약자산",), "first"), (15, ("유형자산",), "first"),
    (20, ("보험계약부채",), "first"), (20, ("보험계약부채", "특별계정부채"), "first"),
    (21, ("재보험계약부채",), "first"), (22, ("투자계약부채",), "first"),
    (23, ("차입부채",), "first"), (24, ("기타부채",), "first"),
    (30, ("자본금",), "first"), (31, ("이익잉여금",), "first"), (4, ("AOCI",), "first"),
    (1, ("자산총계",), "first"), (2, ("부채총계",), "first"), (3, ("자본총계",), "first"),
]
_KINDS_FOR = {1: ("sum_bs", "bs_full"), 2: ("sum_bs", "bs_full"), 3: ("sum_bs", "equity", "bs_full"),
              4: ("equity", "bs_full"), 30: ("equity", "bs_full"), 31: ("equity", "bs_full")}
_DETAIL_KINDS = ("sum_bs", "bs_full")
_FULL_ONLY = {14, 15, 20, 21, 22, 23, 24}

# untested-allowed lists (no DART anchor for that company/item)
SAFE_UNTESTED_S = {1, 2, 3, 30, 31, 4}                          # supervisory summary / equity tables
SAFE_UNTESTED_K = {1, 2, 3, 10, 11, 12, 14, 15, 20, 21, 22, 23, 30, 31, 4}   # K-IFRS statement lines (same lines as DART)
K_BLOCKED_UNTESTED_LABELS = {(10, ("현금및예치금",))}            # supervisory label inside a K-style statement is not a cash line


# the concept that reproduces the DART/master definition of an item on a K-IFRS statement (anchor concept)
_ANCHOR_CONCEPT = {10: ("현금및현금성자산",), 11: ("FVPL",), 12: ("FVOCI",), 13: ("AC_CHILDREN",)}


def is_anchor_concept(c) -> bool:
    item, labels, mode = c
    if item == 10:
        return labels == ("현금및현금성자산",)
    if item in (11, 12):
        return mode == "sum_all"
    if item == 13:
        return mode == "ac_children"
    return True


def cname(c) -> str:
    item, labels, mode = c
    return f"{item}:{'+'.join(labels)}" + ("" if mode == "first" else f"[{mode}]")


@dataclass
class Obs:
    concept: tuple
    item: int
    kind: str
    form: str               # 'S' supervisory (sum_bs / 8-1 with 운용자산) | 'K' K-IFRS statement | 'E' equity table
    page: int
    quarter: str            # the period the value belongs to (may differ from the PDF quarter for comparative columns)
    pdf_quarter: str
    col: int
    raw: float
    unit: str
    value_mn: float         # 백만원
    prec_mn: float          # half-step rounding of the printed unit (백만원)
    tol_mn: float
    how: str                # unit resolution method
    basis: str | None = None
    comparative: bool = False
    src_pdf: str | None = None
    src_sha: str | None = None


def qkey(q: str):
    y, n = q.split(".")
    return int(y), int(n[0])


def qidx(q: str) -> int:
    y, n = qkey(q)
    return y * 4 + n - 1


def prev_year_end(q: str) -> str:
    return f"{int(q[:4]) - 1}.4Q"


def prev_q(q: str, n: int = 1) -> str:
    i = qidx(q) - n
    return f"{i // 4}.{i % 4 + 1}Q"


def load_master():
    rows = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    side = json.loads((ROOT / "data" / "_derived" / "bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
    all_v = defaultdict(dict)       # code -> {(item,q): value}
    anchor = defaultdict(dict)      # non-disclosure sourced
    disc = defaultdict(dict)
    meta = {}
    for r in rows:
        c, it, q, v = r["원보험사코드"], r["항목번호"], r["공시분기"], r["값"]
        meta.setdefault(c, (r["원수사명"], r["티커"], r["생손보여부"]))
        if v is None:
            continue
        all_v[c][(it, q)] = v
        if f"{c}|{it}|{q}" in side:
            disc[c][(it, q)] = v
        elif q not in FORBIDDEN_ANCHOR_Q and (c, q) not in ANCHOR_EXCLUDE:
            anchor[c][(it, q)] = v
    return all_v, anchor, disc, meta


_KPI_METRIC = {"자산총계": 1, "total_assets": 1, "assets": 1, "부채총계": 2, "total_liabilities": 2, "liabilities": 2,
               "자본총계": 3, "total_equity": 3, "equity": 3}


def load_kpi_anchors(code: str) -> dict:
    """{(item, quarter): 백만원} totals from the earlier reinsurer KPI staging (data/reinsurer/kpi_summary_<KR>.json),
    an independent extraction from the same PDFs used as unit/total cross-check for companies without a master."""
    p = ROOT / "data" / "reinsurer" / f"kpi_summary_{code}.json"
    out = {}
    if not p.exists():
        return out
    d = json.loads(p.read_text(encoding="utf-8"))
    for r in d.get("rows", []):
        it = _KPI_METRIC.get(r.get("metric"))
        v = r.get("value")
        if it and isinstance(v, (int, float)) and r.get("unit", d.get("unit")) in ("억원", "억원(비율은 %)", None):
            out[(it, r["period"])] = float(v) * 100.0
    return out


def load_tables(code: str, q: str):
    p = TABLES / f"{code}_{q}.json"
    pa = TABLES / f"{code}_{q}__audit.json"
    if not p.exists() and not pa.exists():
        return None
    doc = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"pdf": None, "sha256": None, "pages": 0, "tables": []}
    if pa.exists():
        aux = json.loads(pa.read_text(encoding="utf-8"))
        for t in aux.get("tables", []):
            t["src"] = "audit"
        doc["tables"] = ([t for t in aux.get("tables", []) if t["kind"] == "bs_full"] + doc["tables"]
                         + [t for t in aux.get("tables", []) if t["kind"] == "pl_full"])
        doc["audit_pdf"] = aux.get("pdf")
    return doc


def table_form(t: dict) -> str:
    """'E' equity table, 'S' supervisory form (운용자산-based), 'K' K-IFRS statement lines.  Some 8-1 detail tables
    print the K-IFRS statement lines first and the supervisory breakdown after them: those count as 'K' (the first
    occurrence of every line is the statement line)."""
    if t["kind"] == "equity":
        return "E"
    if t["kind"] == "sum_bs":
        return "S"
    labs = [c for c in (canon_of_row(r) for r in t["rows"]) if c]
    try:
        i_cash = labs.index("현금및현금성자산")
    except ValueError:
        i_cash = None
    try:
        i_op = labs.index("운용자산")
    except ValueError:
        i_op = None
    if i_op is None:
        return "K"
    if i_cash is not None and i_cash < i_op:
        return "K"
    return "S"


def canon_of_row(r):
    from .views import canon
    return canon(r["label"], "bs")


def pick_tables(doc: dict, kind: str):
    """tables of a kind; for bs_full prefer 별도 (basis=='별도' or unknown) and drop invalid ones."""
    ts = [t for t in doc.get("tables", []) if t["kind"] == kind]
    if kind == "bs_full":
        ok = []
        for t in ts:
            va = view_all(t)
            if all(k in va for k in ("자산총계", "부채총계", "자본총계")) and len(va) >= 8:
                ok.append(t)
        sep = [t for t in ok if t.get("basis") == "별도"]
        non = [t for t in ok if t.get("basis") is None]
        con = [t for t in ok if t.get("basis") == "연결"]
        ts = sep + non
        if not ts and con:
            ts = []        # only a consolidated statement available -> not used (BS master is OFS)
    return ts


def _unit_from_total(raw, ref_mn, ref_tol=1.2):
    """units whose scaling of `raw` ties to the master total.  ref_tol: tolerance contributed by the master
    value itself (100.5 when the master cell is a disclosure-rounded 억원 value)."""
    cands = []
    for u, f in UNIT_FACTOR.items():
        if abs(raw * f - ref_mn) <= max(UNIT_TOL[u] + 1.0, ref_tol, 0.0015 * abs(ref_mn)):
            cands.append(u)
    return cands


def resolve_unit(table: dict, master_q: dict, caption_unit, mtol=None, peer_assets_mn=None):
    """unit name for a table.  Prefer the tie to the master's own totals of the same quarter; else tie to the total
    assets of another table of the same PDF whose unit is already verified (peer, within 3%); else the caption."""
    va = view_all(table)
    for key, item in (("자산총계", 1), ("부채총계", 2), ("자본총계", 3)):
        ref = master_q.get(item)
        rows = va.get(key)
        if not rows or not ref:
            continue
        raw = cur(rows[0])
        if raw is None:
            continue
        cands = _unit_from_total(raw, ref, (mtol or {}).get(item, 1.2))
        if len(cands) == 1:
            return cands[0], "master"
        if len(cands) > 1:
            if caption_unit in cands:
                return caption_unit, "master+caption"
            # keep the finest unit that still fits (exact units are never coarser than needed)
            return None, "ambiguous:" + ",".join(cands)
        # the total disagrees with the master in every unit: not this quarter's table / wrong column
        return None, f"total-mismatch:{key} raw={raw:g} master={ref:g}"
    if peer_assets_mn and not any(master_q.get(i) for i in (1, 2, 3)):
        rows = va.get("자산총계")
        raw = cur(rows[0]) if rows else None
        if raw is not None:
            cands = [u for u, f in UNIT_FACTOR.items() if abs(raw * f - peer_assets_mn) <= 0.03 * abs(peer_assets_mn) + 1.0]
            if len(cands) == 1:
                return cands[0], "peer"
            return None, f"peer-mismatch raw={raw:g} peer={peer_assets_mn:g}"
    if caption_unit in UNIT_FACTOR and not any(master_q.get(i) for i in (1, 2, 3)):
        return caption_unit, "caption"
    return None, "unresolved"


_AC_FAMILY = ("AC_SEC", "AC_LOAN", "AC_DEP", "AC_OTHER")


def _cv(r, c):
    """value of row r in value column c: float, 0.0 for a printed dash (nil), None if the cell is absent."""
    if len(r["vals"]) <= c:
        return None
    if r.get("unsure") and r["unsure"][c]:
        return None                 # separate dash cell left of the amount: sign unknown (see views.align_block)
    if r["dash"][c]:
        return 0.0
    return r["vals"][c]


def _eval(concept, table, col_idx):
    item, labels, mode = concept
    va = view_all(table)
    tot = 0.0
    if mode == "ac_children":
        if "AC_FA" in va:           # parent line present -> the builder uses the parent, never parent + children
            return _cv(va["AC_FA"][0], col_idx)
        # children are ASSET lines: a liability line such as 상각후원가측정금융부채 also canonicalises to AC_OTHER, so only rows
        # above the first liability / total line count (KR1108 2025.4Q: receivable 5.5억 + liability 33.6억 = 39.1억 was wrong)
        cut = [(r["page"], r["y"]) for k_ in ("자산총계", "부채총계", "보험계약부채", "재보험계약부채", "책임준비금", "투자계약부채",
                                              "차입부채", "기타부채", "특별계정부채", "계약자지분조정")
               for r in va.get(k_, [])]
        cutoff = min(cut) if cut else None
        got = False
        for fam in _AC_FAMILY:
            for r in va.get(fam, []):
                if cutoff is not None and (r["page"], r["y"]) >= cutoff:
                    continue
                v = _cv(r, col_idx)
                if v is not None:
                    tot += v
                    got = True
        return tot if got else None
    for lab in labels:
        rows = va.get(lab)
        if not rows:
            return None
        if mode == "sum_all":
            # combined tables print the statement lines first and the supervisory breakdown (from 운용자산 on) after
            # them: only the statement part may be summed, otherwise every line is counted twice
            op = (va.get("운용자산") or [None])[0]
            if op is not None:
                rows = [r for r in rows if (r["page"], r["y"]) < (op["page"], op["y"])]
            vs = [_cv(r, col_idx) for r in rows]
            vs = [v for v in vs if v is not None]
            if not vs:
                return None
            tot += sum(vs)
        else:
            v = _cv(rows[0], col_idx)
            if v is None:
                return None
            tot += v
    return tot


def observations(code: str, q: str, doc: dict, all_v: dict, disc=None, unit_ref=None):
    """Evaluate every concept on the tables of one PDF.  Returns (obs_list, unit_info, notes)."""
    out: list = []
    notes: list = []
    unit_info: dict = {}
    master_q = {it: v for (it, qq), v in all_v.get(code, {}).items() if qq == q}
    dset = (disc or {}).get(code, {})
    mtol = {it: (100.5 if (it, q) in dset else 1.2) for it in master_q}
    if unit_ref:                       # no master for this company: use the independent KPI totals as the unit tie
        for it, v in unit_ref.items():
            master_q.setdefault(it, v)
            mtol.setdefault(it, 100.5)
    sum_unit = None
    peer_assets_mn = None
    for kind in ("sum_bs", "bs_full", "equity"):
        tabs = pick_tables(doc, kind)
        if not tabs:
            continue
        # a PDF may print the statement lines (K) AND the supervisory 8-1 form (S): both are read, so that the S-form lines
        # can be calibrated against the K lines of the same filing
        cand_tabs = [tabs[0]]
        if kind == "bs_full" and len(tabs) > 1 and tabs[1].get("basis") == tabs[0].get("basis")                 and (table_form(tabs[1]) != table_form(tabs[0]) or tabs[1].get("src") != tabs[0].get("src")):
            cand_tabs.append(tabs[1])           # other form, or the filing's own 8-1 next to its audit report
        for ti, t in enumerate(cand_tabs):
            form = table_form(t)
            if kind == "equity":
                unit, how = _equity_unit(t, master_q, sum_unit, doc, mtol)
            else:
                unit, how = resolve_unit(t, master_q, t.get("unit"), mtol, peer_assets_mn)
            if ti == 0:
                unit_info[kind] = (unit, how)
            if kind == "sum_bs" and unit:
                sum_unit = unit
                if how in ("master", "master+caption", "caption") and not master_q.get(1):
                    rr = (view_all(t).get("자산총계") or [None])[0]
                    v0 = cur(rr) if rr else None
                    if v0 is not None:
                        peer_assets_mn = v0 * UNIT_FACTOR[unit]
            if unit is None:
                notes.append(f"{kind}@p{t['page']}: unit {how}")
                continue
            if ti == 1:
                ok_t, det_t = table_identity({"tables": [t]}, kind, unit)
                if ok_t is not True:
                    notes.append(f"{kind}@p{t['page']} (2nd table): identity {det_t}: skipped")
                    continue
            f = UNIT_FACTOR[unit]
            sumbs_py = (kind == "sum_bs" and ti == 0 and sumbs_prev_year_ok(t))
            eq_ok = {}
            if kind == "equity":
                eq_ok = {c: equity_col_ok(t, c) for c in (0, 1, 2)}
                for c, ok in eq_ok.items():
                    if ok is False:
                        notes.append(f"equity@p{t['page']}: column {c} does not close (자본총계 != components): dropped")
            for concept in CONCEPTS:
                item = concept[0]
                kinds = _KINDS_FOR.get(item, _DETAIL_KINDS)
                if item in _FULL_ONLY:
                    kinds = ("bs_full",)
                if kind not in kinds:
                    continue
                for c in (0, 1, 2):
                    if kind == "equity" and item in (3, 4, 30, 31) and eq_ok.get(c) is False:
                        continue
                    if kind == "sum_bs" and c == 1:
                        continue
                    if kind == "sum_bs" and c == 2 and not sumbs_py:
                        continue
                    if kind == "bs_full" and c == 2:
                        continue
                    if kind == "bs_full" and c == 1 and not _has_cols(t, 2):
                        continue
                    v = _eval(concept, t, c)
                    if v is None:
                        continue
                    if kind == "equity":
                        tq = q if c == 0 else prev_q(q, c)
                    elif kind == "bs_full":
                        tq = q if c == 0 else prev_year_end(q)
                    elif kind == "sum_bs" and c == 2:
                        tq = f"{int(q[:4]) - 1}.{q[5:]}"       # same quarter of the previous year
                    else:
                        tq = q
                    out.append(Obs(concept, item, kind, form, t["page"], tq, q, c, v, unit, v * f, UNIT_PREC[unit],
                                   UNIT_TOL[unit], how, t.get("basis"), comparative=(c > 0),
                                   src_pdf=t.get("pdf"), src_sha=t.get("sha256")))
    return out, unit_info, notes


def sumbs_prev_year_ok(table: dict):
    """True when the summary BS prints [current amount, share %, same period of the previous year amount, share %] and the
    previous-year amounts close (assets = liabilities + equity): then column 2 is a trustworthy 'same quarter, previous
    year' comparative (restatements show up here, e.g. RGA 2023.2Q total assets 2,705 -> 2,356)."""
    va = view_all(table)
    ra = (va.get("자산총계") or [None])[0]
    rl = (va.get("부채총계") or [None])[0]
    re_ = (va.get("자본총계") or [None])[0]
    if not (ra and rl and re_) or len(ra["vals"]) < 4:
        return False
    if ra["dash"][1] or ra["dash"][3] or abs((ra["vals"][1] or 0) - 100) > 1.5 or abs((ra["vals"][3] or 0) - 100) > 1.5:
        return False
    a, l, e = (col(r, 2) for r in (ra, rl, re_))
    if None in (a, l, e):
        return False
    return abs(a - l - e) <= 1.5


_EQ_PARTS = ("자본금", "자본잉여금", "신종자본증권", "이익잉여금", "자본조정", "AOCI")


def equity_col_ok(table: dict, c: int):
    """closure of one column of the 4-1 'B/S상 자기자본' table: 자본총계 == sum of its component lines (rounding only).
    True / False, None when the column cannot be judged (a line of the block has a label we do not recognise, or the
    total is missing).  A blank cell is a nil line.  A column that does not close (a typo such as '2.585' for 2,585, or a
    lost minus sign) must not feed any equity cell."""
    from .views import canon, _slice
    rows = table["rows"]
    canons = [canon(r["label"], "bs") for r in rows]
    s_, e_ = _slice("equity", canons)
    if e_ <= s_:
        return None
    if any(cn is None for cn in canons[s_:e_]):
        return None
    va = view_all(table)
    tr = (va.get("자본총계") or [None])[0]
    if tr is None:
        return None
    tot = _cv(tr, c)
    if tot is None:
        return None
    s, n, unknown = 0.0, 0, False
    for k in _EQ_PARTS:
        rows_k = va.get(k)
        if not rows_k:
            continue
        r = rows_k[0]
        if r.get("unsure") and len(r["unsure"]) > c and r["unsure"][c]:
            unknown = True
            continue
        v = _cv(r, c)
        s += (v or 0.0)
        n += 1
    if n < 2:
        return None
    if unknown:
        return False
    return abs(tot - s) <= (n + 1) * 0.5 + 0.011


def _has_cols(table, n):
    va = view_all(table)
    r = (va.get("자산총계") or [None])[0]
    return bool(r) and len(r["vals"]) >= n


def _equity_unit(t, master_q, sum_unit, doc, mtol=None):
    va = view_all(t)
    r = (va.get("자본총계") or [None])[0]
    ref = master_q.get(3)
    cap = t.get("unit")
    if r is not None and ref:
        raw = cur(r)
        cands = _unit_from_total(raw, ref, (mtol or {}).get(3, 1.2)) if raw is not None else []
        if len(cands) == 1:
            return cands[0], "master"
        if len(cands) > 1 and cap in cands:
            return cap, "master+caption"
        if not cands:
            return None, f"total-mismatch:자본총계 raw={raw} master={ref:g}"
    if sum_unit:
        return sum_unit, "borrowed:sum_bs"
    if cap in UNIT_FACTOR and not ref:
        return cap, "caption"
    return None, "unresolved"


def match(obs_value_mn: float, tol_mn: float, anchor_mn: float, comparative: bool = False) -> bool:
    """exact tie for the same-period column; comparatives (prior year-end / prior quarter columns) may have been
    restated slightly, so they are allowed 0.15% (or 1.5 억) -- gross differences still fail."""
    if abs(obs_value_mn - anchor_mn) <= tol_mn:
        return True
    if comparative:
        return abs(obs_value_mn - anchor_mn) <= max(0.0015 * abs(anchor_mn), 150.0 if tol_mn >= 50 else 5.0)
    return False


def table_identity(doc: dict, kind: str, unit: str):
    """(ok, detail): assets == liabilities + equity for the picked table of this kind (raw units)."""
    tabs = pick_tables(doc, kind)
    if not tabs:
        return None, "no table"
    va = view_all(tabs[0])
    a, l, e = (cur((va.get(k) or [None])[0]) for k in ("자산총계", "부채총계", "자본총계"))
    if None in (a, l, e):
        return None, "totals missing"
    tol_raw = UNIT_TOL[unit] / UNIT_FACTOR[unit]
    ok = abs(a - l - e) <= tol_raw * 1.0
    return ok, f"a={a:g} l={l:g} e={e:g} resid={a - l - e:g} unit={unit}"
