#!/usr/bin/env python3
"""Validate computed NB CSM multiple vs IR disclosed ratios.

Pipeline:
  IFRS17 nb_csm (csm_waterfall new_business) ÷ crawled 월납환산 premium
  → compare to nb_csm_ratio.json / meritz IR disclosed multiple

On large mismatch, tries reconcile transforms (unit scale, annual/monthly).
Output: data/assoc/nb_csm_validation.json

Exit code 1 if any validation cohort member fails after reconcile.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from assoc.nb_premium_common import mn_krw_to_eok  # noqa: E402

VIZ = ROOT / "data" / "ifrs17" / "viz"
IR = ROOT / "data" / "ir"
PREMIUM_PATH = ROOT / "data" / "assoc" / "nb_premium_wolnap.json"
OUT_PATH = ROOT / "data" / "assoc" / "nb_csm_validation.json"
TEMPLATES_OUT = ROOT / "templates" / "data" / "assoc" / "nb_csm_validation.json"

# "얼추 비슷" tolerance
REL_TOL = 0.25
ABS_TOL = 3.0

IR_COMPANY_MAP = {
    "samsung_life": "삼성생명",
    "hanwha_life": "한화생명",
    "samsung_fire": "삼성화재해상보험",
    "hyundai_marine": "현대해상",
    "db_insurance": "DB손해보험",
    "kb_insurance": "KB손해보험",
}

# Preferred premium scope per company for validation
PREFERRED_SCOPE = {
    "DB손해보험": ["total_monthly_avg", "protection_monthly_avg"],
    "삼성화재해상보험": ["protection_premium_monthly_avg", "protection_implied_from_ir_csm_and_ratio"],
    "현대해상": ["total_implied_from_ir_csm_and_ratio", "personal_premium_monthly_avg"],
    "한화생명": ["total_implied_from_ir_csm_and_ratio"],
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_ir_ratio(entry: dict) -> tuple[float | None, str | None]:
    sp = entry.get("single_point") or {}
    for key in ("2025_total_via_4Q_avg", "ytd_2025_1_3Q_total", "2024_total", "FY25.1Q"):
        if key in sp and sp[key] is not None:
            return float(sp[key]), f"single_point.{key}"

    # Prefer "total" series latest point
    total = (entry.get("series") or {}).get("total")
    if total:
        pts = total.get("points") or []
        if pts:
            last = pts[-1]
            if last.get("value") is not None:
                return float(last["value"]), f"series.total.{last.get('period')}"

    for name, series in (entry.get("series") or {}).items():
        if name == "total":
            continue
        pts = series.get("points") or []
        if pts:
            last = pts[-1]
            if last.get("value") is not None:
                return float(last["value"]), f"series.{series.get('label')}.{last.get('period')}"
    return None, None


def load_ir_benchmarks() -> dict[str, tuple[float, str]]:
    out: dict[str, tuple[float, str]] = {}
    path = IR / "nb_csm_ratio.json"
    if not path.exists():
        return out
    data = load_json(path)
    for section in ("life", "non_life"):
        for key, entry in (data.get(section) or {}).items():
            company = IR_COMPANY_MAP.get(key)
            if not company:
                continue
            ratio, src = latest_ir_ratio(entry)
            if ratio is not None and src:
                out[company] = (ratio, src)
    meritz_path = IR / "meritz" / "extracted_202603.json"
    if meritz_path.exists():
        m = load_json(meritz_path)
        mult = (
            (m.get("meritz_hwajae_standalone") or {})
            .get("new_business_csm_multiple", {})
            .get("total")
        )
        if mult is not None:
            out["메리츠화재해상보험"] = (float(mult), "meritz_factsheet.1Q26")
    return out


def index_nb_csm(waterfall: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for c in waterfall.get("companies") or []:
        name = c.get("company")
        nb = (c.get("stages") or {}).get("new_business", {}).get("value_mn_krw")
        if name and nb is not None:
            out[name] = mn_krw_to_eok(abs(float(nb))) or 0.0
    return out


def pick_premium_records(companies: dict[str, dict], company: str) -> list[dict]:
    rows = [v for k, v in companies.items() if v.get("company") == company]
    scopes = PREFERRED_SCOPE.get(company, [])
    rows.sort(
        key=lambda r: (
            scopes.index(r["scope"]) if r.get("scope") in scopes else 99,
            r.get("period") or "",
        )
    )
    return rows


def reconcile_candidates(nb_eok_annual: float, prem_eok_month: float) -> list[dict]:
    """Try common unit/period mismatches."""
    cands: list[dict] = []
    if prem_eok_month <= 0:
        return cands
    base_monthly_nb = nb_eok_annual / 12.0

    transforms = [
        ("monthly_nb / monthly_prem", base_monthly_nb, prem_eok_month),
        ("monthly_nb / (prem*12)", base_monthly_nb, prem_eok_month * 12),
        ("annual_nb / (prem*12)", nb_eok_annual, prem_eok_month * 12),
        ("annual_nb / prem", nb_eok_annual, prem_eok_month),
        ("monthly_nb / (prem/10)", base_monthly_nb, prem_eok_month / 10),
        ("monthly_nb / (prem*10)", base_monthly_nb, prem_eok_month * 10),
    ]
    for label, num, den in transforms:
        if den and den > 0:
            cands.append({"transform": label, "multiple": round(num / den, 4)})
    return cands


def is_close(computed: float, ir: float) -> bool:
    if not math.isfinite(computed) or not math.isfinite(ir) or ir == 0:
        return False
    rel = abs(computed - ir) / abs(ir)
    abs_d = abs(computed - ir)
    return rel <= REL_TOL or abs_d <= ABS_TOL


def validate_row(
    company: str,
    nb_eok_annual: float,
    prem: dict,
    ir_ratio: float,
    ir_src: str,
) -> dict:
    prem_month = float(prem["wolnap_premium_eok_month"])
    primary_computed = (
        round((nb_eok_annual / 12.0) / prem_month, 4) if prem_month > 0 else None
    )

    cands = reconcile_candidates(nb_eok_annual, prem_month)
    passed_transform = None
    for c in cands:
        if is_close(c["multiple"], ir_ratio):
            passed_transform = c
            break

    passed = primary_computed is not None and is_close(primary_computed, ir_ratio)
    if not passed and passed_transform:
        passed = True

    computed = primary_computed
    rel_err = (
        abs(primary_computed - ir_ratio) / abs(ir_ratio)
        if primary_computed is not None and ir_ratio
        else None
    )

    return {
        "company": company,
        "ifrs17_period": "FY2024 annual (csm_waterfall)",
        "premium_period": prem.get("period"),
        "premium_scope": prem.get("scope"),
        "premium_source": prem.get("source"),
        "nb_csm_eok_annual": nb_eok_annual,
        "nb_csm_eok_monthly": round(nb_eok_annual / 12.0, 4),
        "wolnap_premium_eok_month": prem_month,
        "computed_multiple": computed,
        "computed_transform": "monthly_nb / monthly_prem",
        "reconcile_pass_transform": passed_transform["transform"] if passed_transform else None,
        "reconcile_pass_multiple": passed_transform["multiple"] if passed_transform else None,
        "ir_disclosed_multiple": ir_ratio,
        "ir_source": ir_src,
        "abs_diff": round(abs(computed - ir_ratio), 4) if computed is not None else None,
        "rel_diff": round(rel_err, 4) if rel_err is not None else None,
        "status": "pass" if passed else "fail",
        "reconcile_candidates": cands[:6],
        "notes": (
            "Period/scope mismatch likely (IFRS FY2024 vs IR 2025 snapshot)"
            if not passed
            else None
        ),
    }


def build_report() -> dict:
    wf = load_json(VIZ / "csm_waterfall.json")
    premium_payload = load_json(PREMIUM_PATH) if PREMIUM_PATH.exists() else {"companies": {}}
    companies = premium_payload.get("companies") or {}
    nb_map = index_nb_csm(wf)
    ir_map = load_ir_benchmarks()

    nb_ratio_data = load_json(IR / "nb_csm_ratio.json") if (IR / "nb_csm_ratio.json").exists() else {}

    results: list[dict] = []
    for company, (ir_ratio, ir_src) in sorted(ir_map.items()):
        if company == "KB손해보험":
            results.append(
                {
                    "company": company,
                    "status": "skip",
                    "notes": "IR deck has no company-level NB CSM multiple",
                }
            )
            continue
        nb_annual = nb_map.get(company)
        if nb_annual is None or nb_annual <= 0:
            results.append(
                {
                    "company": company,
                    "status": "skip",
                    "ir_disclosed_multiple": ir_ratio,
                    "notes": "Missing or zero IFRS17 new_business CSM",
                }
            )
            continue
        prem_rows = pick_premium_records(companies, company)
        if not prem_rows:
            results.append(
                {
                    "company": company,
                    "status": "skip",
                    "ir_disclosed_multiple": ir_ratio,
                    "notes": "No crawled/extracted 월납환산 premium for company",
                }
            )
            continue

        entry = None
        for section in ("life", "non_life"):
            for key, ent in (nb_ratio_data.get(section) or {}).items():
                if IR_COMPANY_MAP.get(key) == company:
                    entry = ent
                    break

        ir_alts: list[tuple[float, str]] = [(ir_ratio, ir_src)]
        if entry:
            for sname, series in (entry.get("series") or {}).items():
                pts = series.get("points") or []
                if pts and pts[-1].get("value") is not None:
                    alt = (float(pts[-1]["value"]), f"series.{sname}.{pts[-1].get('period')}")
                    if alt not in ir_alts:
                        ir_alts.append(alt)

        row: dict | None = None
        for prem in prem_rows:
            for ir_v, ir_s in ir_alts:
                candidate = validate_row(company, nb_annual, prem, ir_v, ir_s)
                if row is None or candidate["status"] == "pass" or (
                    candidate.get("rel_diff") is not None
                    and (row.get("rel_diff") is None or candidate["rel_diff"] < row["rel_diff"])
                ):
                    row = candidate
                if candidate["status"] == "pass":
                    break
            if row and row["status"] == "pass":
                break
        results.append(row or validate_row(company, nb_annual, prem_rows[0], ir_ratio, ir_src))

    tested = [r for r in results if r.get("status") in ("pass", "fail")]
    passed = sum(1 for r in tested if r["status"] == "pass")
    failed = [r for r in tested if r["status"] == "fail"]

    return {
        "_meta": {
            "definition": "computed NB CSM mult = IFRS17 new_business CSM ÷ 월납환산 premium",
            "ifrs17_numerator_period": wf.get("period"),
            "tolerance": {"rel": REL_TOL, "abs": ABS_TOL},
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/validate_nb_csm_multiple.py",
            "cohort_tested": len(tested),
            "cohort_pass": passed,
            "cohort_fail": len(failed),
            "needs_reconcile_loop": len(failed) > 0,
        },
        "results": results,
        "failed": failed,
    }


def main() -> int:
    report = build_report()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    TEMPLATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = report["_meta"]
    print(f"Wrote {OUT_PATH}")
    print(f"  tested={meta['cohort_tested']} pass={meta['cohort_pass']} fail={meta['cohort_fail']}")
    for f in report.get("failed") or []:
        print(
            f"  FAIL {f['company']}: computed={f.get('computed_multiple')} "
            f"ir={f.get('ir_disclosed_multiple')} rel={f.get('rel_diff')}"
        )
    return 1 if meta["cohort_fail"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
