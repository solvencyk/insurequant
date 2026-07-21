#!/usr/bin/env python3
"""Triage the CHECK-5 generic anomaly candidates — the (b) layer of the discovery→triage→enforce
funnel (owner 2026-06-16). The generic scanner is high-recall/low-precision (192 raw candidates,
many are micro-insurer size artifacts). This step adds PRECISION deterministically by judging each
candidate against the COMPANY'S OWN history instead of the global cohort:

  PEER_OUTLIER  → NOISE  if |value| is consistent with that company's own median (it's just a
                         small/large company, not an anomaly);  REAL if it deviates from its OWN
                         history (a genuine jump/drop for that company).
  COHORT_ZERO   → REAL   if the company is nonzero for the item in OTHER quarters (a real
                         extraction miss);  NOISE if it is zero across ALL its quarters (structural
                         — the company genuinely doesn't have that line).
  thin own-history (<2 nonzero own quarters) → UNCERTAIN → hand to the LLM-skeptic residual pass.

Output: data/_derived/anomaly_triage.json  +  a console summary.
Run:    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/triage_anomaly_candidates.py
"""
from __future__ import annotations
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from validate_master_tables import load_long  # noqa: E402  (same loader the gate's CHECK 5 uses)

MASTERS = {"CSM_waterfall": "CSM_waterfall.json", "PL_breakdown": "PL_breakdown.json"}
OUT = ROOT / "data" / "_derived" / "anomaly_triage.json"
# owner-verified cells — values the owner hand-fixed/confirmed. Suppressed so the LLM-skeptic never
# re-flags them (stops the recurring whack-a-mole on owner-confirmed-but-statistically-odd values).
GOLD = ROOT / "data" / "_gold" / "user_pl_confirmed_cells.json"


def _norm(s):
    return re.sub(r"\s+", "", str(s or ""))


def _load_owner_confirmed():
    """-> ({(master, co_norm, quarter, item_norm): value}, tol_abs, tol_rel)."""
    if not GOLD.exists():
        return {}, 2.0, 0.01
    d = json.loads(GOLD.read_text(encoding="utf-8"))
    out = {(c["master"], _norm(c["company"]), str(c["quarter"]), _norm(c["item"])): float(c["value"])
           for c in d.get("cells", [])}
    return out, float(d.get("tolerance_abs", 2.0)), float(d.get("tolerance_rel", 0.01))


def triage():
    real, noise, uncertain, confirmed = [], [], [], []
    owner_ok, tol_abs, tol_rel = _load_owner_confirmed()
    for master, fname in MASTERS.items():
        long = load_long(fname)  # {(원수사명, 공시분기): {item: val}}
        by_item: dict = defaultdict(list)
        own: dict = defaultdict(list)  # (co, item) -> [vals]
        for (co, q), m in long.items():
            if (q or "").startswith("2023."):  # 2023 known site-non-disclosure
                continue
            for item, v in m.items():
                if isinstance(v, (int, float)):
                    by_item[item].append((co, q, float(v)))
                    own[(co, item)].append((q, float(v)))
        for item, cells in by_item.items():
            if len(cells) < 8:
                continue
            nz = [v for v in (x for _, _, x in cells) if v != 0]
            if not nz:
                continue
            nz_frac = len(nz) / len(cells)
            cohort_med = statistics.median([abs(v) for v in nz])
            for co, q, v in cells:
                own_all = own[(co, item)]
                own_nz = [abs(x) for (_qq, x) in own_all if x != 0]
                own_med = statistics.median(own_nz) if own_nz else None
                qn = q.split(".")[1][0] if "." in q else "?"   # '2025.1Q' -> '1'
                same_pos = [abs(x) for (qq, x) in own_all
                            if x != 0 and "." in qq and qq.split(".")[1][0] == qn]
                own_med_pos = statistics.median(same_pos) if same_pos else None
                base = {"master": master, "item": item, "company": co, "quarter": q,
                        "value": round(v, 1), "cohort_median": round(cohort_med),
                        "own_median": round(own_med) if own_med else None,
                        "own_qpos_median": round(own_med_pos) if own_med_pos else None,
                        "own_nonzero_quarters": len(own_nz)}
                # --- OWNER_CONFIRMED: owner hand-verified this exact cell → never flag ---
                cval = owner_ok.get((master, _norm(co), q, _norm(item)))
                if cval is not None and abs(v - cval) <= max(tol_abs, tol_rel * abs(cval)):
                    confirmed.append({**base, "verdict": "OWNER_CONFIRMED",
                                      "reason": "owner-verified (data/_gold/user_pl_confirmed_cells.json) "
                                                "— suppressed from skeptic"})
                    continue
                # --- COHORT_ZERO (0 where the item is overwhelmingly nonzero) ---
                if v == 0 and nz_frac >= 0.7:
                    base["rule"] = "COHORT_ZERO"
                    if own_nz:
                        real.append({**base, "verdict": "REAL",
                                     "reason": f"0 here but this company is nonzero in "
                                               f"{len(own_nz)} other quarter(s) (own median "
                                               f"|{round(own_med)}|) — extraction miss"})
                    else:
                        noise.append({**base, "verdict": "NOISE",
                                      "reason": "company is 0 for this item across ALL its "
                                                "quarters — structural (genuinely no such line)"})
                # --- PEER_OUTLIER — judge vs SAME quarter-position own-history so the YTD-cumulative
                #     convention (Q1<Q4) is not mistaken for an anomaly ---
                elif v != 0 and (abs(v) > cohort_med * 50 or abs(v) < cohort_med / 50):
                    base["rule"] = "PEER_OUTLIER"
                    if not same_pos or len(same_pos) < 2:
                        uncertain.append({**base, "verdict": "UNCERTAIN",
                                          "reason": f"outlier vs cohort, <2 same-quarter ({qn}Q) own "
                                                    f"points to size/YTD-normalize — LLM residual"})
                    elif own_med_pos / 3 <= abs(v) <= own_med_pos * 3:
                        noise.append({**base, "verdict": "NOISE",
                                      "reason": f"|{round(abs(v))}| consistent with this company's own "
                                                f"{qn}Q median |{round(own_med_pos)}| — size/YTD-seasonal "
                                                f"normal, not an anomaly"})
                    else:
                        real.append({**base, "verdict": "REAL",
                                     "reason": f"|{round(abs(v))}| deviates from this company's own "
                                               f"{qn}Q median |{round(own_med_pos)}| (>3×) — genuine jump/drop"})
    return real, noise, uncertain, confirmed


def main():
    real, noise, uncertain, confirmed = triage()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"real": real, "uncertain": uncertain, "noise_count": len(noise),
         "noise_sample": noise[:10], "owner_confirmed": confirmed}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    total = len(real) + len(noise) + len(uncertain) + len(confirmed)
    print("#" * 72)
    print("ANOMALY TRIAGE  (CHECK-5 candidates → own-history precision filter)")
    print("#" * 72)
    print(f"candidates: {total}  →  REAL={len(real)}  UNCERTAIN={len(uncertain)}  "
          f"OWNER_CONFIRMED(suppressed)={len(confirmed)}  NOISE(suppressed)={len(noise)}")
    if confirmed:
        print("-" * 72)
        print(f"OWNER_CONFIRMED (suppressed — owner-verified, skeptic skips) — {len(confirmed)}:")
        for c in confirmed:
            print(f"  [{c['master']}] {c['item']}  {c['company']} {c['quarter']}  = {c['value']}")
    print(f"precision lift: {total} raw → {len(real) + len(uncertain)} to review "
          f"({100*(len(real)+len(uncertain))/total:.0f}% of raw), {len(noise)} auto-suppressed")
    print("-" * 72)
    print(f"REAL (actionable extraction-miss / genuine outlier) — {len(real)}:")
    for c in real:
        print(f"  [{c['master']}] {c['item']}  {c['company']} {c['quarter']}  = {c['value']}")
        print(f"        {c['reason']}")
    if uncertain:
        print("-" * 72)
        print(f"UNCERTAIN (LLM residual) — {len(uncertain)}:")
        for c in uncertain[:20]:
            print(f"  [{c['master']}] {c['item']}  {c['company']} {c['quarter']}  = {c['value']}  ({c['reason']})")
        if len(uncertain) > 20:
            print(f"  ...+{len(uncertain)-20} more")
    print("-" * 72)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
