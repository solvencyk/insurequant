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
sys.path.insert(0, str(ROOT / "scripts"))
from validate_master_tables import WFY_EXCEPTIONS  # noqa: E402  (면제 정본은 한 곳)

SRC = ROOT / "CSM_waterfall.json"
OUT = ROOT / "data" / "dart" / "viz" / "csm_continuity_validation.json"

OPENING, CLOSING = 1, 6
# 2026-08-25: 이 두 축은 **이 파일이 유일한 구현이 아니다**.
#   · within-FY 기초 동일성  → `validate_master_tables._check_plausibility` 의 WFY 가
#     max(0.5%, 2억) + 문서화된 소급재작성 면제셋으로 이미 엄격하게 검사한다.
#   · FY 경계 연속성          → `validate_data_contract` CSM_CONT 가 max(0.5%, 2억) +
#     건별 면제 등재부로 검사한다(하나생명 2024.4Q Δ+73억이 그 경로로 잡혀 있다).
# 이 파일의 역할은 그 미세 항등식이 아니라 **off-by-year / 별도↔연결 / ×N basis swap**
# 같은 총량 오류의 그물이다(파일 docstring 참조) — 그래서 경계 축은 의도적으로 넓다.
# within-FY 는 5% → 1% 로 조였다. 전 버킷 시뮬(92 FY-그룹): 5% 위반 0 → 1% 위반 1
# (메리츠화재 FY2023, 100,383.8 → 96,376.4). 그 1건은 master_tables 의 WFY_EXCEPTIONS 에
# 이미 '소급재작성' 으로 등재된 건이라 새 blocking RED 는 0 이다.
WITHIN_FY_TOL = 0.01   # 기초 spread within a FY (2026-08-25: 0.05 → 0.01)
BOUNDARY_TOL = 0.10    # |기초[1Q] - 기말[prevFY.4Q]| / 기말 — RANGE(총량 오류 그물)

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


def check_company(co_data, co_name=None):
    """Return list of continuity findings for one company.

    `co_name` 은 WFY 면제 대조용(원수사명 키). None 이면 면제를 적용하지 않는다 —
    면제는 **이름이 확인될 때만** 걸린다(조용히 전부 통과시키지 않기 위해).
    """
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
                excepted = (co_name, str(y)) in WFY_EXCEPTIONS
                findings.append({
                    "rule": ("WITHIN_FY_OPENING_DRIFT_EXCEPTED" if excepted
                             else "WITHIN_FY_OPENING_DRIFT"),
                    "fy": y,
                    "severity": "YELLOW" if excepted else "RED",
                    "detail": f"FY{y} 기초 CSM 변동 {min(vals):.0f}~{max(vals):.0f} "
                              f"(>{WITHIN_FY_TOL:.0%}) — 분기 간 basis/period mis-pick 의심"
                              + (" [문서화된 면제: 원천 소급재작성, "
                                 "validate_master_tables.WFY_EXCEPTIONS]" if excepted else ""),
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
        f = check_company(data, names.get(co))
        if f:
            results[co] = {"name": names[co], "findings": f}
            red += sum(1 for x in f if x["severity"] == "RED")

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
            print(f"  {f['severity']} {co} {v['name']}: {f['rule']} — {f['detail']}")
    print(f"[written] {OUT}")
    return 2 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
