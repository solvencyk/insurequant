"""Build downstream IFRS17 KPI cards JSON for the dashboard."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "ifrs17" / "viz"
OUT = VIZ / "downstream_kpis.json"

SERVICE_MARGIN_PATTERNS = (
    "\uc81c\uacf5\ub41c \uc11c\ube44\uc2a4\uc758 \ubcf4\ud5d8\uacc4\uc57d\ub9c8\uc9c4",
    "\ubcf4\ud5d8\uacc4\uc57d\ub9c8\uc9c4\uc0c1\uac01",
    "\uc11c\ube44\uc2a4\uc758 \uc774\uc804\uc744 \ubc18\uc601",
    "\ub2f9\uae30\uc190\uc775\uc73c\ub85c \uc778\uc2dd\ud55c \ubcf4\ud5d8\uacc4\uc57d\ub9c8\uc9c4",
    "\ubcf4\ud5d8\uc11c\ube44\uc2a4\uc218\uc775",
    "\ubcf4\ud5d8\uc218\uc775",
)


def load_json(name: str) -> dict:
    path = VIZ / name
    if not path.exists():
        return {"companies": []}
    return json.loads(path.read_text(encoding="utf-8"))


def index_by_company(payload: dict) -> dict[str, dict]:
    return {c["company"]: c for c in payload.get("companies", [])}


def find_service_margin(pl: dict | None) -> float | None:
    if not pl:
        return None
    for row in pl.get("rows") or []:
        label = row.get("label") or ""
        if any(p in label for p in SERVICE_MARGIN_PATTERNS):
            v = row.get("current")
            if v is not None and v != 0:
                return abs(float(v))
    for row in pl.get("rows") or []:
        v = row.get("current")
        if v is not None and v != 0:
            return abs(float(v))
    return None


def safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return num / den


def build_kpi(company: str, wf: dict | None, amort: dict | None, pl: dict | None) -> dict:
    stages = (wf or {}).get("stages") or {}
    closing = (stages.get("closing") or stages.get("opening") or {}).get("value_mn_krw")
    amort_val = (stages.get("amortization") or {}).get("value_mn_krw")
    nb_val = (stages.get("new_business") or {}).get("value_mn_krw")

    abs_amort = abs(amort_val) if amort_val is not None else None
    abs_nb = abs(nb_val) if nb_val is not None else None
    service_margin = find_service_margin(pl)

    csm_dependency = None
    if abs_amort is not None:
        denom = abs_amort + (service_margin or 0)
        if denom > 0:
            csm_dependency = round(abs_amort / denom, 3)

    csm_runway = safe_div(closing, abs_amort)
    if csm_runway is not None:
        csm_runway = round(csm_runway, 2)

    nb_replacement = safe_div(abs_nb, abs_amort)
    if nb_replacement is not None:
        nb_replacement = round(nb_replacement, 2)

    buckets = (amort or {}).get("buckets") or {}
    near_term = sum(v for k, v in buckets.items() if k in ("y1", "y1_y3") and v is not None)
    schedule_run_rate = None
    if near_term and closing and closing != 0:
        scale = 1.0
        if near_term > abs(closing) * 100:
            scale = 1_000_000.0
        elif near_term > abs(closing) * 10:
            scale = 1_000.0
        schedule_run_rate = round((near_term / scale) / abs(closing), 3)

    status = "ok" if any(x is not None for x in (csm_dependency, csm_runway, schedule_run_rate, nb_replacement)) else "partial"

    return {
        "company": company,
        "status": status,
        "csm_dependency": csm_dependency,
        "csm_runway_years": csm_runway,
        "schedule_run_rate": schedule_run_rate,
        "nb_replacement": nb_replacement,
        "inputs": {
            "closing_csm_mn_krw": closing,
            "csm_amort_mn_krw": amort_val,
            "new_business_mn_krw": nb_val,
            "service_margin_proxy_mn_krw": service_margin,
            "amort_buckets": buckets,
        },
    }


def main() -> None:
    waterfall = load_json("csm_waterfall.json")
    amort = index_by_company(load_json("csm_amort_schedule.json"))
    pl = index_by_company(load_json("insurance_pl_breakdown.json"))

    companies = [
        build_kpi(wf["company"], wf, amort.get(wf["company"]), pl.get(wf["company"]))
        for wf in waterfall.get("companies", [])
    ]

    payload = {
        "definitions": {
            "csm_dependency": "|CSM amort| / (|CSM amort| + insurance service margin proxy)",
            "csm_runway_years": "closing CSM / |annual CSM amort|",
            "schedule_run_rate": "sum(A2 y1 + y1_y3 buckets) / closing CSM",
            "nb_replacement": "|new business CSM| / |CSM amort|",
        },
        "period": waterfall.get("period", "annual FY2024"),
        "companies": companies,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for c in companies if c.get("status") == "ok")
    print(f"Wrote {OUT} ({ok}/{len(companies)} ok)")


if __name__ == "__main__":
    main()