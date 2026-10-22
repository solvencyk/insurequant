# -*- coding: utf-8 -*-
"""e21 independent life-insurer readers (own code; helpers from e21_read / e21_t2 / measure-phase mlib only; no scripts/ or src/ imports).
  life_is_items(code, fy, role, kind)  -> items 3 / 8 / 2 (+ their four statement lines) from the SEPARATE income statement of a filing
  presence_015(st)                     -> item 15 (기타영업수익) = printed value, or the builder default 0.0 when the statement carries no such line
Item definitions follow scripts/build_pl_breakdown.py::assemble (read, not imported):
  3 = jang_rev - jang_cost ; 8 = jang_rerev - jang_recost ; 2 = 3 + 8
  KR0079 (일반보험서비스수익/비용 + 출재보험서비스수익/비용 lines, tier1 `_life_*`): all four taken as magnitudes
  others (`_is_*` fallback): rev signed, cost |.|, rerev signed (can be negative), recost |.|
"""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R  # noqa: E402
from e21_t2 import part, total  # noqa: E402

# code -> list of (key, normalised statement label, nth occurrence among the pre-OCI rows, sign, magnitude?)
SPEC = {
    "KR0104": [("rev", "보험수익", 1, 1, False), ("cost", "발행한보험계약에서생기는보험서비스비용", 1, -1, True), ("rerev", "재보험수익", 1, 1, False), ("recost", "재보험비용", 1, -1, True)],
    "KR0083": [("rev", "보험수익", 1, 1, False), ("cost", "보험비용", 1, -1, True), ("rerev", "재보험수익", 1, 1, False), ("recost", "재보험비용", 1, -1, True)],
    "KR0070": [("rev", "보험수익", 1, 1, False), ("cost", "보험비용", 1, -1, True), ("rerev", "재보험수익", 1, 1, False), ("recost", "재보험비용", 1, -1, True)],
    "KR0068": [("rev", "보험수익", 1, 1, False), ("cost", "보험비용", 1, -1, True), ("rerev", "재보험수익", 1, 1, False), ("recost", "재보험비용", 1, -1, True)],
    "KR0079": [("rev", "일반보험서비스수익", 1, 1, True), ("cost", "일반보험서비스비용", 1, -1, True), ("rerev", "출재보험서비스수익", 1, 1, True), ("recost", "출재보험서비스비용", 1, -1, True)],
    "KR0099": [("rev", "보험영업수익", 2, 1, False), ("cost", "보험영업비용", 2, -1, True), ("rerev", "재보험영업수익", 1, 1, False), ("recost", "재보험영업비용", 1, -1, True)],
}


def _row(st, label, nth):
    hit = [r for r in st.rows if not r.oci and r.lab == label]
    if len(hit) < nth:
        raise KeyError(f"{st.rel}: label {label!r} occurs {len(hit)} times (< {nth})")
    return hit[nth - 1]


def life_is_items(code, fy, role="prior", kind="cum", st=None):
    """-> dict item -> dict(val (백만원), parts, formula, src) for items 3, 8, 2 and the raw lines under key 'lines'"""
    st = st or R.Stmt(code, fy)
    div = st.scale
    got = {}
    parts = {}
    for key, label, nth, sign, mag in SPEC[code]:
        row = _row(st, label, nth)
        c = st.pick_cell(row, role, kind)
        if c is None:
            raise RuntimeError(f"{st.rel}: no {role}/{kind} cell on row {row.raw!r} L{row.line}")
        v = R.cellnum(c)
        if v is None:
            raise RuntimeError(f"{st.rel}: row {row.raw!r} cell {c['text']!r} not numeric")
        parts[key] = part(f"{row.raw.replace(chr(0x3000), ' ').strip()}", (v, c["line"], c["text"]), sign, mag, None, div)
        got[key] = v / div
    out = {}
    out[3] = dict(val=total([parts["rev"], parts["cost"]]), parts=[parts["rev"], parts["cost"]],
                  formula="보험수익계열 - |보험비용계열| (장기/발행)" if code != "KR0079" else "|일반보험서비스수익| - |일반보험서비스비용|")
    out[8] = dict(val=total([parts["rerev"], parts["recost"]]), parts=[parts["rerev"], parts["recost"]],
                  formula="재보험수익계열 - |재보험비용계열|" if code != "KR0079" else "|출재보험서비스수익| - |출재보험서비스비용|")
    out[2] = dict(val=out[3]["val"] + out[8]["val"], parts=out[3]["parts"] + out[8]["parts"], formula="3 + 8")
    return {i: dict(v, src=f"{st.rel} {role}/{kind} unit {st.unit}") for i, v in out.items()}


def presence_015(st, role="prior", kind="cum"):
    """item 15: the printed 기타영업수익 line if the statement has one (pre-OCI), else the builder default 0.0 (assemble(): statement found, no such line -> 0)"""
    hit = [r for r in st.rows if not r.oci and r.lab == "기타영업수익"]
    if not hit:
        return dict(val=0.0, parts=[], formula="no 기타영업수익 line in the statement -> builder default 0.0", src=f"{st.rel}", present=False)
    if len(hit) > 1:
        raise RuntimeError(f"{st.rel}: several 기타영업수익 rows")
    c = st.pick_cell(hit[0], role, kind)
    v = R.cellnum(c)
    p = part("기타영업수익", (v, c["line"], c["text"]), 1, False, None, st.scale)
    return dict(val=total([p]), parts=[p], formula="printed 기타영업수익", src=f"{st.rel}", present=True)
