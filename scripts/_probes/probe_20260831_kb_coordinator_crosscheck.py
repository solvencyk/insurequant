#!/usr/bin/env python3
"""Cross-check live kics_rate_sensitivity.json KR0010 2026.2Q rows against the coordinator's
independently-confirmed values (different agent, 220dpi render, page 45 reference)."""
from __future__ import annotations
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rs = json.loads((ROOT / "kics_rate_sensitivity.json").read_text(encoding="utf-8"))

COORD = {
    "지급여력비율":     {"base": 187.45, "-100bp": 195.26, "-50bp": 192.14, "+50bp": 182.33, "+100bp": 176.93},
    "지급여력금액":     {"base": 135316.0, "-100bp": 142859.0, "-50bp": 139638.0, "+50bp": 130950.0, "+100bp": 126669.0},
    "지급여력기준금액": {"base": 72187.0, "-100bp": 73164.0, "-50bp": 72674.0, "+50bp": 71821.0, "+100bp": 71591.0},
}

rows = [r for r in rs if r["원수사명"] == "KB손해보험" and r["공시분기"] == "2026.2Q"]
print(f"KB손해보험 2026.2Q rows in live master: {len(rows)}")
all_match = True
for r in rows:
    meas = r["measure구분"]
    expect = COORD[meas]
    mismatches = []
    for c in ("-100bp", "-50bp", "base", "+50bp", "+100bp"):
        live_v = r.get(c)
        exp_v = expect[c]
        if live_v is None or abs(float(live_v) - exp_v) > 1e-6:
            mismatches.append((c, live_v, exp_v))
    status = "MATCH" if not mismatches else "MISMATCH"
    if mismatches:
        all_match = False
    print(f"  {r['경과조치여부']:6s} {meas:10s} {status}  {mismatches if mismatches else ''}")

print()
print("ALL MATCH" if all_match else "SOME MISMATCH -- needs re-apply")

# also re-run RS1 identity check directly on live KB rows for sanity
print()
print("--- RS1 self-check on live KB rows ---")
by_meas_phase = {}
for r in rows:
    by_meas_phase[(r["경과조치여부"], r["measure구분"])] = r
for phase in ("적용전", "적용후"):
    rat = by_meas_phase.get((phase, "지급여력비율"))
    amt = by_meas_phase.get((phase, "지급여력금액"))
    bas = by_meas_phase.get((phase, "지급여력기준금액"))
    for c in ("-100bp", "-50bp", "base", "+50bp", "+100bp"):
        rv, av, bv = rat.get(c), amt.get(c), bas.get(c)
        exp = av / bv * 100.0
        diff = abs(exp - rv)
        flag = "OK" if diff <= max(0.5, 0.005 * abs(rv)) else "RED"
        print(f"  {phase} [{c}] 비율={rv} expected={exp:.4f} diff={diff:.4f} {flag}")
