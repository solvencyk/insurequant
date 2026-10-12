"""a5: tier1 type test, sharpened from the memo's s6 delta test into a FEASIBILITY test over all 14 quarters (read-only).

Item 13 of the 4-2-2 table = 'Ⅲ. 보완자본으로 재분류하는 항목' = everything moved from 순자산 into 보완자본:
  (a) hybrid capital reclassified (supplementary-type securities in full; basic-type only the excess over SCR x 10%;
      legacy securities in full in the TFI-off basis, only the excess over SCR x 15% in the TFI-on basis)
  (b) 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 (= item49)
  (c) other non-negative reclassifications (담보제공자산 초과분, 순확정급여 50%, 순이연법인세자산 ...).
Subordinated debt is a liability, never in item 13.
So OTHERS = item13 - item49 - (a) must be >= 0 under the true hypothesis. A hypothesis that needs OTHERS < 0 in any
quarter (beyond tolerance) is rejected.

Basis of the 4-2-2 table per quarter: item2(기본자본) 값 == item50 값 (TFI-off column) or == item50 적용후 (TFI-on).

Hypotheses for the non-legacy part N = item6 - item53:
  H_t2 : N is supplementary-type (III.2.다.(2)) -> reclassified in full
  H_t1 : N is basic-type (III.2.다.(1)) -> only max(0, N - SCR x 10%) reclassified

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a5_tier1_type_feasibility.py
Output: a5_tier1_type_feasibility.txt (same folder)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CODES = ["KR1000", "KR0104", "KR0083", "KR0071",           # undetermined four
         "KR0097", "KR0072", "KR0050", "KR0032", "KR0068",  # memo-classified references
         "KR0005", "KR0073", "KR0011", "KR0002"]
TOL = 5.0


def f(v):
    try:
        return float(str(v).replace(",", "").replace("△", "-"))
    except (TypeError, ValueError):
        return None


def qkey(q):
    y, p = q.split(".")
    return int(y), int(p[0])


def main() -> int:
    kics = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    t: dict[tuple, dict] = {}
    names = {}
    for r in kics:
        c = r["원보험사코드"]
        if c in CODES and r["항목번호"] in (2, 6, 13, 14, 49, 50, 53):
            t.setdefault((c, r["공시분기"]), {})[r["항목번호"]] = (f(r.get("값")), f(r.get("값_적용후")))
            names[c] = r.get("원수사명")
    out = ["code q | basis | item6 item53 N | X=13-49 | SCRx10% SCRx15% | OTHERS if H_t2 / if H_t1"]
    verdict = {}
    for c in CODES:
        out.append(f"== {c} {names.get(c)}")
        mins = {"t2": None, "t1": None}
        for q in sorted({q for (cc, q) in t if cc == c}, key=qkey):
            v = t[(c, q)]
            g = lambda n, i=0: (v.get(n) or (None, None))[i]
            i2, i6, i13, i14, i49 = g(2), g(6), g(13), g(14), g(49)
            i50pre, i50post, i53 = g(50), g(50, 1), g(53) or 0.0
            if None in (i6, i13, i14) or i49 is None:
                out.append(f"  {q}: skip (missing)")
                continue
            basis = "?"
            if i2 is not None and i50pre is not None and abs(i2 - i50pre) <= TOL:
                basis = "OFF"
            if i2 is not None and i50post is not None and abs(i2 - i50post) <= TOL:
                basis = "ON" if basis == "?" else "OFF=ON"
            leg = min(i53, i6)
            n = max(0.0, i6 - leg)
            x = i13 - i49
            l10, l15 = i14 * 0.10, i14 * 0.15
            leg_recl = leg if basis in ("OFF", "OFF=ON", "?") else max(0.0, leg - l15)
            oth_t2 = x - leg_recl - n
            oth_t1 = x - leg_recl - max(0.0, n - l10)
            for k, o in (("t2", oth_t2), ("t1", oth_t1)):
                mins[k] = o if mins[k] is None else min(mins[k], o)
            out.append(f"  {q}: {basis:6s} | {i6:,.0f} {leg:,.1f} {n:,.1f} | {x:,.1f} | {l10:,.1f} {l15:,.1f} | "
                       f"{oth_t2:,.1f} / {oth_t1:,.1f}")
        rej = [k for k, m in mins.items() if m is not None and m < -TOL]
        verdict[c] = (mins, rej)
        out.append(f"  -> min OTHERS: H_t2 {mins['t2']:,.1f} · H_t1 {mins['t1']:,.1f}  rejected: {rej or 'none'}")
    out.append("")
    out.append("SUMMARY (rejected hypothesis = arithmetic impossible in at least one quarter)")
    for c, (mins, rej) in verdict.items():
        out.append(f"  {c} {names.get(c)}: rejected={rej or 'none'}  minOTHERS t2={mins['t2']:,.1f} t1={mins['t1']:,.1f}")
    txt = "\n".join(out) + "\n"
    (HERE / "a5_tier1_type_feasibility.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
