"""CSM continuity validator — catches off-by-one-year / basis-shift / single-period
magnitude errors that closing-identity is BLIND to.

Rationale (mutation test 2026, scripts/_probes/_mutation_test_csm.py):
closing-identity (기초+신계약+이자+가정+상각=기말) passes for off-year and uniform
basis/×N errors because everything scales together. The only INTERNAL signal
(no 2nd source needed) is time-continuity:
  - within a FY, 기초(opening) must be ~constant (YTD opening = year start)
  - at a FY boundary, 기말[prevFY.4Q] ≈ 기초[FY.1Q]

A break is a candidate off-year / 별도↔연결 / mis-pick — RED for review.
Runs on the long-format master CSM_waterfall.json (all periods per company).

Run:  python scripts/validate_csm_continuity.py
Exit: 0 if no breaks, else 2.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CSM_waterfall.json"
OUT = ROOT / "data" / "dart" / "viz" / "csm_continuity_validation.json"

OPENING, CLOSING = 1, 6
WITHIN_FY_TOL = 0.05   # 기초 spread within a FY
BOUNDARY_TOL = 0.10    # |기초[1Q] - 기말[prevFY.4Q]| / 기말

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def fy(p):  # "2024.3Q" -> 2024
    return int(p.split(".")[0])


def qn(p):  # "2024.3Q" -> 3
    return int(p.split(".")[1][0])


def load():
    rows = json.loads(SRC.read_text(encoding="utf-8"))
    by_co: dict[str, dict] = {}
    names: dict[str, str] = {}
    for r in rows:
        co = r["원보험사코드"]
        names[co] = r["원수사명"]
        by_co.setdefault(co, {}).setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
    return by_co, names


def check_company(co_data):
    """Return list of continuity findings for one company."""
    findings = []
    periods = sorted(co_data, key=lambda p: (fy(p), qn(p)))

    # within-FY 기초 constant
    by_fy: dict[int, list] = {}
    for p in periods:
        o = co_data[p].get(OPENING)
        if o is not None:
            by_fy.setdefault(fy(p), []).append((p, o))
    for y, lst in by_fy.items():
        if len(lst) >= 2:
            vals = [v for _, v in lst]
            m = statistics.fmean(vals)
            if m and (max(vals) - min(vals)) / abs(m) > WITHIN_FY_TOL:
                findings.append({
                    "rule": "WITHIN_FY_OPENING_DRIFT",
                    "fy": y,
                    "severity": "RED",
                    "detail": f"FY{y} 기초 CSM 변동 {min(vals):.0f}~{max(vals):.0f} "
                              f"(>{WITHIN_FY_TOL:.0%}) — 분기 간 basis/period mis-pick 의심",
                })

    # FY-boundary 기말 -> 기초 continuity
    for p in periods:
        if qn(p) == 1:
            prev = f"{fy(p) - 1}.4Q"
            cp = co_data.get(prev, {}).get(CLOSING)
            on = co_data[p].get(OPENING)
            if cp and on is not None and abs(on - cp) / abs(cp) > BOUNDARY_TOL:
                findings.append({
                    "rule": "FY_BOUNDARY_DISCONTINUITY",
                    "period": p,
                    "severity": "RED",
                    "detail": f"{prev} 기말 {cp:.0f} ≠ {p} 기초 {on:.0f} "
                              f"(Δ{abs(on - cp) / abs(cp):.1%}) — off-by-year / basis swap 의심",
                })
    return findings


def main():
    by_co, names = load()
    results = {}
    red = 0
    for co, data in by_co.items():
        f = check_company(data)
        if f:
            results[co] = {"name": names[co], "findings": f}
            red += len(f)

    report = {
        "_meta": {
            "validator": "csm_continuity",
            "rule": "within-FY opening constant + FY-boundary 기말→기초 continuity",
            "purpose": "catch off-year / basis-swap / mis-pick invisible to closing-identity",
            "companies_total": len(by_co),
            "companies_flagged": len(results),
            "red_findings": red,
        },
        "flagged": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[csm_continuity] companies={len(by_co)} flagged={len(results)} red={red}")
    for co, v in results.items():
        for f in v["findings"]:
            print(f"  RED {co} {v['name']}: {f['rule']} — {f['detail']}")
    print(f"[written] {OUT}")
    return 2 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
