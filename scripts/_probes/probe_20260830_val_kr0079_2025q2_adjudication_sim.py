"""validation 2026-08-30 — simulate BOTH candidates for KR0079 2025.2Q item4/item5
against every rule that reads those two cells. Read-only: no master or gold write.

Candidates
  A (current gold, on screen today):  item4 = -886.27  item5 = -791.30
  B (raw / fixed builder):            item4 = -685.50  item5 = -992.07

Rules exercised
  1. closing identity   item6 == item1+item2+item3+item4+item5   (both must close)
  2. CSM_AMORT identity PL(원수+수재) CSM상각 == |워터폴 CSM상각|, incl. the ledger verdict
  3. YTD monotonicity   |item5| must be non-decreasing across 1Q->2Q->3Q->4Q of the FY
  4. 값_당분기 sign      the quarterly flow implied by each candidate

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/_probes/probe_20260830_val_kr0079_2025q2_adjudication_sim.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.validate_master_tables import (  # noqa: E402
    CSM_AMORT_TOL_ABS_EOK,
    CSM_AMORT_TOL_REL,
    csm_amort_ledger,
    csm_amort_ledger_verdict,
    csm_amort_pl_side_eok,
    csm_amort_tol,
)

CO, Q = "KR0079", "2025.2Q"
CAND = {"A_gold": (-886.27, -791.30), "B_raw": (-685.50, -992.07)}


def wf_rows():
    rows = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
    return [r for r in rows if r.get("원보험사코드") == CO]


def pl_map():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    out = {}
    for r in rows:
        if r.get("원보험사코드") != CO:
            continue
        out.setdefault(r.get("공시분기"), {})[r.get("항목명")] = r.get("값")
    return out


def main() -> int:
    wf = wf_rows()
    by_q = {}
    for r in wf:
        by_q.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
    pl = pl_map()

    print(f"== {CO} {Q} — two-candidate simulation ==\n")
    base = dict(by_q[Q])
    print("current master row:", {k: base[k] for k in sorted(base)})
    print()

    ledger = csm_amort_ledger().get("entries", {})
    lkey_candidates = [k for k in ledger if k.endswith(f"|{Q}") and "미래에셋" in k]
    lkey = lkey_candidates[0] if lkey_candidates else None
    entry = ledger.get(lkey) if lkey else None
    print(f"ledger key = {lkey!r}  pinned residual = "
          f"{entry.get('residual_eok') if entry else None}  cause = "
          f"{entry.get('cause') if entry else None}\n")

    # PL side (억) — the gate's own helper, not a re-implementation
    plm_raw = pl.get(Q, {})
    plm = {"원수CSM상각": plm_raw.get("원수 CSM상각"),
           "수재CSM상각": plm_raw.get("수재 CSM상각")}
    pl_eok = csm_amort_pl_side_eok(plm)
    print(f"PL side (gate helper) = {pl_eok}억   "
          f"[원수 CSM상각={plm_raw.get('원수 CSM상각')} 백만]\n")

    prevq_amort = by_q.get("2025.1Q", {}).get(5)
    nextq_amort = by_q.get("2025.3Q", {}).get(5)
    print(f"YTD chain: 2025.1Q item5 = {prevq_amort}   2025.3Q item5 = {nextq_amort}")
    print(f"PL  chain: 1Q={pl.get('2025.1Q', {}).get('원수 CSM상각')} "
          f"2Q={plm_raw.get('원수 CSM상각')} "
          f"3Q={pl.get('2025.3Q', {}).get('원수 CSM상각')}  (백만원)\n")

    for name, (i4, i5) in CAND.items():
        print("-" * 72)
        print(f"CANDIDATE {name}:  item4={i4}  item5={i5}")
        # 1. closing identity
        lhs = base[1] + base[2] + base[3] + i4 + i5
        print(f"  1) closing identity  1+2+3+4+5 = {lhs:.2f}  vs item6 = {base[6]}  "
              f"-> residual {lhs - base[6]:+.2f}억  "
              f"{'CLOSES' if abs(lhs - base[6]) <= 0.05 else 'BREAKS'}")
        # 2. CSM_AMORT identity
        amort_eok = abs(i5)
        resid = round((pl_eok or 0) - amort_eok, 2)
        tol = csm_amort_tol(amort_eok)
        verdict = csm_amort_ledger_verdict(entry, resid)
        within = abs(resid) <= tol
        print(f"  2) CSM_AMORT identity  PL {pl_eok:,.2f} vs |상각| {amort_eok:,.2f} "
              f"-> 잔차 {resid:+,.2f}억 ({abs(resid) / amort_eok * 100:.3f}%), "
              f"허용 {tol:,.2f}억")
        if within:
            print(f"       => PASS (no finding). ledger line {lkey!r} becomes "
                  f"CSM_AMORT_IDENTITY_LEDGER_STALE (YELLOW) until removed.")
        else:
            print(f"       => finding, ledger verdict = {verdict} "
                  f"({'YELLOW' if verdict == 'PINNED' else 'RED'})")
        # 3. YTD monotonicity of |item5|
        chain = [abs(prevq_amort), amort_eok, abs(nextq_amort)]
        mono = all(chain[i] <= chain[i + 1] + 1e-9 for i in range(len(chain) - 1))
        print(f"  3) YTD |item5| chain 1Q/2Q/3Q = "
              f"{chain[0]:,.2f} / {chain[1]:,.2f} / {chain[2]:,.2f}  "
              f"-> {'monotone' if mono else 'NOT monotone'}")
        q2_flow = amort_eok - abs(prevq_amort)
        q3_flow = abs(nextq_amort) - amort_eok
        print(f"     implied quarterly amortisation  Q2={q2_flow:,.2f}억  "
              f"Q3={q3_flow:,.2f}억  (Q1={abs(prevq_amort):,.2f}억)")
        # 4. PL quarterly cross-check
        pl_q2_flow = None
        p1 = pl.get("2025.1Q", {}).get("원수 CSM상각")
        p2 = plm_raw.get("원수 CSM상각")
        if isinstance(p1, (int, float)) and isinstance(p2, (int, float)):
            pl_q2_flow = (p2 - p1) / 100.0
        print(f"  4) PL-implied Q2 amortisation = {pl_q2_flow:,.2f}억  "
              f"-> gap vs candidate = {q2_flow - (pl_q2_flow or 0):+,.2f}억")
    print("-" * 72)
    print(f"\n(tolerance constants: abs={CSM_AMORT_TOL_ABS_EOK} rel={CSM_AMORT_TOL_REL})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
