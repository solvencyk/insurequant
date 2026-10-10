# -*- coding: utf-8 -*-
"""Stage B for the income statement (PL_breakdown items 1, 16, 22, 23, 24 from the management-disclosure summary PL).

Source table: 요약 포괄손익계산서 (sum_pl, 억원, YTD) -- columns [current YTD, same period of the previous year, change];
year-end audit statement (pl_full from raw_aux, 원) as the exact source at Q4.
Verification (all in-table, nothing is guessed):
  * unit: printed caption; cross-checked against the independent KPI staging (data/reinsurer/kpi_summary_<KR>.json)
  * column semantics: current - previous == change for the rows that print three amounts
  * identities with the helper rows of the SAME column: 영업이익 = 보험손익 + 투자손익, 세전이익 = 영업이익 + 영업외손익,
    당기순이익 = 세전이익 - 법인세 (rounding tolerance 1.5 units)
  * signs: a minus printed in its own cell is handled in views.align_block (flagged `unsure` otherwise -> value dropped)
"""
from __future__ import annotations

from dataclasses import dataclass

from .stage_b import UNIT_FACTOR, UNIT_PREC
from .views import view_all

PL_ITEM = {"보험손익": 1, "기타사업비용": 16, "세전이익": 22, "법인세": 23, "당기순이익": 24}
HELPERS = ("투자손익", "영업이익", "영업외손익", "보험수익", "보험서비스비용", "재보험수익", "재보험서비스비용",
           "투자수익", "투자비용", "영업외수익", "영업외비용")


@dataclass
class PLObs:
    item: int
    quarter: str            # period the value belongs to
    pdf_quarter: str        # filing it was read from
    col: int                # 0 = current YTD, 1 = same period of the previous year
    value_mn: float         # 백만원
    prec_mn: float
    unit: str
    page: int
    kind: str               # sum_pl | pl_full
    src_pdf: str | None
    src_sha: str | None
    ident_ok: object        # True / False / None (not judgeable) for the column it was read from
    sem_ok: object          # column semantics (current - previous == change); None when not judgeable
    label: str = ""


def _cell(r, c):
    """printed amount of column c: float; 0.0 for a printed dash (nil); None when the cell is absent or its sign is unknown"""
    if len(r["vals"]) <= c:
        return None
    if r.get("unsure") and len(r["unsure"]) > c and r["unsure"][c]:
        return None
    if r["dash"][c]:
        return 0.0
    return r["vals"][c]


def _pick(doc: dict, kind: str, audit_only: bool = False):
    for t in doc.get("tables", []):
        if t["kind"] != kind:
            continue
        if audit_only and t.get("src") != "audit":
            continue
        va = view_all(t)
        if "보험손익" in va and "당기순이익" in va:
            return t
    return None


def _checks(raw: dict, ncols: int):
    """raw: {canon: [c0, c1, c2...]} in printed units.  Returns ({col: identity ok/None}, semantics ok/None)."""
    tol = 1.5

    def g(name, c):
        v = raw.get(name)
        return None if v is None or len(v) <= c else v[c]

    ident = {}
    for c in range(min(ncols, 2)):
        res = []
        a, b, d = g("보험손익", c), g("투자손익", c), g("영업이익", c)
        if None not in (a, b, d):
            res.append(abs(a + b - d) <= tol)
        d, e, f = g("영업이익", c), g("영업외손익", c), g("세전이익", c)
        if None not in (d, e, f):
            res.append(abs(d + e - f) <= tol)
        f, t_, n = g("세전이익", c), g("법인세", c), g("당기순이익", c)
        if None not in (f, t_, n):
            res.append(abs(f - t_ - n) <= tol)
        ident[c] = all(res) if res else None
    sem = []
    if ncols >= 3:
        for v in raw.values():
            if len(v) >= 3 and None not in v[:3]:
                sem.append(abs(v[0] - v[1] - v[2]) <= tol)
    sem_ok = (sum(sem) / len(sem) >= 0.8) if len(sem) >= 3 else None
    return ident, sem_ok


def _item16(raw: dict, c: int):
    """기타사업비용 in the master's convention (an expense is positive).  Some summary tables print every component line with
    a leading minus (KR0050 2023.1Q, KR1103 2024.4Q), others print a genuine negative (KR1101 2025.2Q: -8).  The sign is
    therefore decided by the definition  보험손익 = (보험수익-보험서비스비용) + (재보험수익-재보험서비스비용) - 기타사업비용  on the
    printed MAGNITUDES of the same column; when the four component rows are not all printed the printed value is kept only if no
    revenue line of the column is negative (no minus-artefact), otherwise the cell is not read (None)."""
    def g(name):
        v = raw.get(name)
        return None if v is None or len(v) <= c else v[c]
    x, tot = g("기타사업비용"), g("보험손익")
    if x is None:
        return None
    parts = [g(n) for n in ("보험수익", "보험서비스비용", "재보험수익", "재보험서비스비용")]
    if tot is not None and None not in parts:
        base = abs(parts[0]) - abs(parts[1]) + abs(parts[2]) - abs(parts[3])
        ok = [sgn for sgn in (1, -1) if abs(tot - (base - sgn * abs(x))) <= 3.0]
        if len(ok) == 1:
            return ok[0] * abs(x)
        if len(ok) == 2:              # |x| ~ 0
            return abs(x) if abs(x) < 1.0 else x
        return None
    rev = [g(n) for n in ("보험수익", "재보험수익", "투자수익", "영업외수익")]
    if any(r is not None and r < 0 for r in rev):
        return None
    return x


def _read(table: dict, ncols: int):
    va = view_all(table)
    raw = {}
    for name in tuple(PL_ITEM) + HELPERS:
        rows = va.get(name)
        if not rows:
            continue
        r = rows[0]
        raw[name] = [_cell(r, c) for c in range(ncols)]
    return raw


def observations(doc: dict, q: str):
    """PLObs of the five loadable items from the summary PL (and the audit statement) of ONE filing (quarter q).
    Returns (obs, notes)."""
    out, notes = [], []
    for kind, audit_only, ncols in (("sum_pl", False, 3), ("pl_full", True, 2)):
        t = _pick(doc, kind, audit_only)
        if t is None:
            continue
        unit = t.get("unit")
        if unit not in UNIT_FACTOR:
            notes.append(f"{kind}@p{t['page']}: unit {unit!r} unresolved")
            continue
        f = UNIT_FACTOR[unit]
        raw = _read(t, ncols)
        ident, sem_ok = _checks(raw, ncols)
        for name, item in PL_ITEM.items():
            v = raw.get(name)
            if not v:
                continue
            for c in (0, 1):
                if len(v) <= c or v[c] is None:
                    continue
                if item == 16:
                    x = _item16(raw, c)
                    if x is None:
                        continue
                    v = list(v)
                    v[c] = x
                tq = q if c == 0 else f"{int(q[:4]) - 1}.{q[5:]}"
                out.append(PLObs(item, tq, q, c, v[c] * f, UNIT_PREC[unit], unit, t["page"], kind,
                                 t.get("pdf"), t.get("sha256"), ident.get(c), sem_ok if kind == "sum_pl" else None, name))
    return out, notes
