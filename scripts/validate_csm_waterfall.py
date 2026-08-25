#!/usr/bin/env python3
"""Validate IFRS17 CSM waterfall completeness and rollforward identity.

Rules (all companies with IFRS17 disclosure must pass):
  1. new_business CSM present and non-zero
  2. opening + new_business + interest + assumption + amortization ≈ closing
  3. minimum stage coverage (opening, closing, new_business)

Output: data/dart/viz/csm_waterfall_validation.json
Exit code 1 when any company fails.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATERFALL_PATH = ROOT / "data" / "dart" / "viz" / "csm_waterfall.json"
OUT_PATH = ROOT / "data" / "dart" / "viz" / "csm_waterfall_validation.json"

STAGE_KEYS = ("opening", "new_business", "interest", "assumption", "amortization", "closing")
REQUIRED_STAGES = ("opening", "new_business", "closing")

# IFRS17 disclosure rule: every entity × reporting period with CSM rollforward
# must publish new-business CSM (신계약 CSM). Missing/zero → block viz + reparse.
NB_ISSUE_CODES = frozenset({"new_business_missing", "new_business_zero"})

# Rollforward 항등식의 허용오차. **등식이므로 반올림 폭만** (2026-08-25).
# 종전 0.5% / 500백만 은 `scripts/validate_master_tables.py` 의 CLOSING_IDENTITY
# (max(0.1%, 2억=200백만)) 와 **같은 등식을 다른 폭으로** 재구현한 것이었다 — 같은 축을
# 두 파일이 서로 다르게 구현해 둔 것이 2026-08-25 CSM 상각 사고의 절반이라, 폭을 맞췄다.
# 전 버킷 시뮬레이션(41사): 0.5%/500mn·0.1%/200mn·0.05%/100mn 어디서도 위반 0 —
# 조이는 비용이 0 이고, 이제 이 게이트가 잡을 수 있는 결함의 폭이 5배 좁아졌다.
REL_TOL = 0.001
ABS_TOL_MN = 200.0

# IFRS17 (K-IFRS 제1117호) is mandatorily effective for annual periods
# beginning on or after 2023-01-01. Every entry in csm_waterfall.json is an
# ANNUAL 사업보고서 filed in Q1 (Jan-Apr) of the year AFTER the fiscal year it
# covers (rcept_no's first 4 digits = filing year; verified across all 47
# entries currently in this file — every rcept_no month is 03 or 04, none
# fall in the 05/08/11 windows that would mark a quarterly/half-year filing).
# So a filing whose fiscal year is 2022 or earlier (rcept_no filed in 2023)
# reports BEFORE the standard existed: its measurement-note extract carries,
# at most, a single point-in-time "적용할 경우"(if-applied) pro-forma preview —
# never a rollforward with opening/new_business/.../closing stages, because
# that concept did not apply to the FY2022 financial statements themselves.
# Confirmed by direct inspection: all 6 affected filings' extracted
# measurement blocks contain ZERO occurrences of "보험계약마진" anywhere
# (not just in the picked block — searched every block in the file).
# These are therefore a STRUCTURAL exclusion (never had the data to report),
# not a parsing gap — reparsing them can never produce a waterfall. Excluding
# them keeps the gate meaningful for the 41 in-scope filings instead of
# permanently pinned at fail=6 for filings that can never pass.
IFRS17_EFFECTIVE_FISCAL_YEAR = 2023


def _annual_fiscal_year(rcept_no: str) -> int | None:
    """Fiscal year covered by an ANNUAL (사업보고서) filing, from its rcept_no.

    First 4 digits of rcept_no are the filing year; annual reports file in
    Q1 of the year after the fiscal year they cover (same convention as
    ``scripts/_dart_path_helpers.py:annual_period_dir_for_rcept`` and
    ``scripts/viz_build_ifrs17_panels.py:_period_asof_from_rcept``'s months
    1-4 branch). Returns None when rcept_no doesn't look like a 14-digit
    DART receipt number, so a malformed value is never silently excluded.
    """
    if not (isinstance(rcept_no, str) and len(rcept_no) >= 4 and rcept_no[:4].isdigit()):
        return None
    return int(rcept_no[:4]) - 1


def _stage_val(stages: dict, key: str) -> float | None:
    node = stages.get(key) or {}
    v = node.get("value_mn_krw")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def check_balance(stages: dict) -> dict:
    parts: dict[str, float | None] = {k: _stage_val(stages, k) for k in STAGE_KEYS}
    missing = [k for k in STAGE_KEYS if parts[k] is None]
    if missing:
        return {
            "ok": False,
            "missing_stages": missing,
            "residual_mn_krw": None,
            "tolerance_mn_krw": None,
        }

    opening = parts["opening"] or 0.0
    computed_closing = sum(parts[k] or 0.0 for k in STAGE_KEYS if k != "closing")
    closing = parts["closing"] or 0.0
    residual = computed_closing - closing
    tol = max(ABS_TOL_MN, abs(closing) * REL_TOL)
    return {
        "ok": abs(residual) <= tol,
        "opening_mn_krw": opening,
        "computed_closing_mn_krw": round(computed_closing, 2),
        "reported_closing_mn_krw": closing,
        "residual_mn_krw": round(residual, 2),
        "tolerance_mn_krw": round(tol, 2),
        "missing_stages": [],
    }


def validate_company(entry: dict) -> dict:
    company = entry.get("company") or "?"
    status = entry.get("status") or "unknown"
    stages = entry.get("stages") or {}
    nb = _stage_val(stages, "new_business")

    issues: list[str] = []
    if status in ("no_csm_columns", "no_stage_match", "error"):
        issues.append(f"waterfall_status={status}")

    for req in REQUIRED_STAGES:
        if _stage_val(stages, req) is None:
            issues.append(f"missing_stage:{req}")

    if nb is None:
        issues.append("new_business_missing")
    elif abs(nb) < 1e-6:
        issues.append("new_business_zero")

    balance = check_balance(stages)
    if not balance.get("ok"):
        if balance.get("missing_stages"):
            issues.append(f"balance_incomplete:{','.join(balance['missing_stages'])}")
        else:
            issues.append(
                f"balance_fail:residual={balance.get('residual_mn_krw')} "
                f"tol={balance.get('tolerance_mn_krw')}"
            )

    period_score = None
    cap = entry.get("caption") or ""
    if "(전)기" in cap or "제74(전)" in cap or "<전기>" in cap:
        issues.append("prior_period_block_selected")
        period_score = "prior"

    nb_issues = [i for i in issues if i in NB_ISSUE_CODES or i.startswith("missing_stage:new_business")]
    passed = len(issues) == 0
    return {
        "company": company,
        "rcept_no": entry.get("rcept_no"),
        "waterfall_status": status,
        "caption": cap,
        "period_hint": period_score,
        "new_business_mn_krw": nb,
        "new_business_ok": len(nb_issues) == 0,
        "must_reparse": len(nb_issues) > 0 or status in ("no_csm_columns", "no_stage_match", "error"),
        "balance": balance,
        "issues": issues,
        "status": "pass" if passed else "fail",
    }


def build_report() -> dict:
    payload = json.loads(WATERFALL_PATH.read_text(encoding="utf-8"))
    companies = payload.get("companies") or []

    in_scope: list[dict] = []
    excluded: list[dict] = []
    for c in companies:
        fy = _annual_fiscal_year(c.get("rcept_no") or "")
        if fy is not None and fy < IFRS17_EFFECTIVE_FISCAL_YEAR:
            excluded.append(
                {
                    "company": c.get("company") or "?",
                    "rcept_no": c.get("rcept_no"),
                    "fiscal_year": fy,
                    "reason": (
                        f"annual filing covers FY{fy}, before IFRS17's "
                        f"{IFRS17_EFFECTIVE_FISCAL_YEAR}-01-01 effective date — "
                        "no rollforward existed to disclose"
                    ),
                }
            )
        else:
            in_scope.append(c)

    results = [validate_company(c) for c in in_scope]
    failed = [r for r in results if r["status"] == "fail"]
    passed = [r for r in results if r["status"] == "pass"]
    nb_failed = [r for r in results if not r.get("new_business_ok")]
    must_reparse = [r for r in results if r.get("must_reparse")]

    return {
        "_meta": {
            "definition": "opening + new_business + interest + assumption + amortization ≈ closing",
            "required_stages": list(REQUIRED_STAGES),
            "new_business_rule": (
                "IFRS17 CSM rollforward: new_business CSM mandatory non-null/non-zero "
                "for every disclosed entity at every reporting period in scope"
            ),
            "new_business_required_nonzero": True,
            "balance_tolerance": {"rel": REL_TOL, "abs_mn_krw": ABS_TOL_MN},
            "source": str(WATERFALL_PATH),
            "period": payload.get("period"),
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/validate_csm_waterfall.py",
            "ifrs17_effective_fiscal_year": IFRS17_EFFECTIVE_FISCAL_YEAR,
            "companies_total": len(companies),
            "companies_excluded_pre_ifrs17": len(excluded),
            "companies_in_scope": len(results),
            "companies_pass": len(passed),
            "companies_fail": len(failed),
            "new_business_fail": len(nb_failed),
            "must_reparse_count": len(must_reparse),
            "needs_reparse_loop": len(failed) > 0,
            "needs_reparse_for_new_business": len(nb_failed) > 0,
        },
        "excluded_pre_ifrs17": excluded,
        "new_business_failed": nb_failed,
        "must_reparse": must_reparse,
        "failed": failed,
        "results": results,
    }


def main() -> int:
    if not WATERFALL_PATH.is_file():
        print(f"missing {WATERFALL_PATH}", file=sys.stderr)
        return 2

    report = build_report()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = report["_meta"]
    print(f"Wrote {OUT_PATH}")
    print(
        f"  pass={meta['companies_pass']} fail={meta['companies_fail']} "
        f"nb_fail={meta['new_business_fail']} in_scope={meta['companies_in_scope']} "
        f"excluded_pre_ifrs17={meta['companies_excluded_pre_ifrs17']} "
        f"total={meta['companies_total']}"
    )
    for x in report.get("excluded_pre_ifrs17") or []:
        print(f"  EXCLUDED (pre-IFRS17, FY{x['fiscal_year']}): {x['company']} {x['rcept_no']}")
    for f in report.get("new_business_failed") or []:
        print(f"  NB BLOCK {f['company']}: {', '.join(f.get('issues') or [])}")
    for f in report.get("failed") or []:
        if f.get("new_business_ok"):
            print(f"  FAIL {f['company']}: {', '.join(f.get('issues') or [])}")
    if meta["needs_reparse_for_new_business"]:
        print("  → needs_reparse_for_new_business: run run_ifrs17_csm_reconcile_loop.py")
    return 1 if meta["companies_fail"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
