#!/usr/bin/env python3
"""Build IFRS17 CSM bubble chart JSON for templates/index.html.

Bubble encoding:
  - symbolSize ∝ closing CSM (억원)
  - color ∝ NB CSM multiple = IFRS17 new_business CSM ÷ crawled 월납환산 premium

Denominator: data/_derived/nb_premium_wolnap.json (KIDI + IR extract + overrides).
NO IR ratio back-solve. See data/_derived/nb_csm_validation.json for IR cross-check.

Output: data/dart/viz/csm_bubble.json (+ templates copy + embed.js)
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "dart" / "viz"
ASSOC = ROOT / "data" / "_derived"
OUT_PATH = VIZ / "csm_bubble.json"
OUT_EMBED = VIZ / "csm_bubble.embed.js"
TEMPLATES_OUT = ROOT / "templates" / "data" / "dart" / "viz" / "csm_bubble.json"
TEMPLATES_EMBED = ROOT / "templates" / "data" / "dart" / "viz" / "csm_bubble.embed.js"
PREMIUM_PATH = ASSOC / "nb_premium_wolnap.json"
VALIDATION_PATH = ASSOC / "nb_csm_validation.json"

LIFE_HINTS = ("생명", "라이프", "Life")


def mn_to_eok(mn_krw: float | None) -> float | None:
    if mn_krw is None:
        return None
    return round(float(mn_krw) / 100.0, 2)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sector_of(company: str) -> str:
    if any(h in company for h in LIFE_HINTS):
        return "Life"
    return "Non-Life"


def best_premium_by_company(companies: dict[str, dict]) -> dict[str, dict]:
    """Pick one premium row per company (prefer latest / non-implied scope)."""
    by_co: dict[str, list[dict]] = {}
    for row in companies.values():
        co = row.get("company")
        if not co:
            continue
        by_co.setdefault(co, []).append(row)

    implied_markers = ("implied_from_ir", "ratio_only")
    out: dict[str, dict] = {}
    for co, rows in by_co.items():
        rows.sort(
            key=lambda r: (
                1 if any(m in (r.get("scope") or "") for m in implied_markers) else 0,
                r.get("period") or "",
            ),
            reverse=True,
        )
        out[co] = rows[0]
    return out


def color_ratio(r: float | None) -> str:
    if r is None or not math.isfinite(r):
        return "#adb5bd"
    if r >= 12:
        t = min((r - 12) / 8, 1.0)
        return f"hsl(120, {40 + 40 * t}%, {28 + 8 * (1 - t)}%)"
    if r >= 8:
        return "hsl(90, 45%, 35%)"
    if r >= 5:
        return "hsl(45, 55%, 42%)"
    t = min((5 - r) / 5, 1.0)
    return f"hsl(0, {35 + 45 * t}%, {32 + 6 * (1 - t)}%)"


def build_payload() -> dict:
    wf = load_json(VIZ / "csm_waterfall.json")
    kpis = load_json(VIZ / "downstream_kpis.json")
    premium_payload = load_json(PREMIUM_PATH)
    validation = load_json(VALIDATION_PATH)
    prem_by_co = best_premium_by_company(premium_payload.get("companies") or {})

    wf_idx = {c["company"]: c for c in wf.get("companies", []) if c.get("company")}
    kpi_idx = {c["company"]: c for c in kpis.get("companies", []) if c.get("company")}

    val_idx = {r["company"]: r for r in validation.get("results") or [] if r.get("company")}

    companies: list[dict] = []
    stats = {
        "total": 0,
        "with_csm": 0,
        "with_nb_csm": 0,
        "with_premium": 0,
        "with_computed_multiple": 0,
        "validation_pass": 0,
        "validation_fail": 0,
    }

    for name in sorted(wf_idx.keys()):
        wf_row = wf_idx[name]
        kpi_row = kpi_idx.get(name, {})
        stats["total"] += 1

        stages = wf_row.get("stages") or {}
        nb_mn = (stages.get("new_business") or {}).get("value_mn_krw")
        nb_eok_annual = mn_to_eok(abs(nb_mn)) if nb_mn is not None else None
        nb_eok_month = round(nb_eok_annual / 12.0, 4) if nb_eok_annual else None
        if nb_eok_annual is not None:
            stats["with_nb_csm"] += 1

        closing_mn = (kpi_row.get("inputs") or {}).get("closing_csm_mn_krw")
        if closing_mn is None:
            closing_mn = (stages.get("closing") or {}).get("value_mn_krw")
        csm_eok = mn_to_eok(closing_mn)
        if csm_eok is not None and csm_eok > 0:
            stats["with_csm"] += 1

        prem_row = prem_by_co.get(name)
        premium_eok_month = None
        premium_source = None
        premium_period = None
        if prem_row and prem_row.get("wolnap_premium_eok_month") is not None:
            premium_eok_month = float(prem_row["wolnap_premium_eok_month"])
            premium_source = prem_row.get("source")
            premium_period = prem_row.get("period")
            stats["with_premium"] += 1

        computed_multiple = None
        if premium_eok_month and premium_eok_month > 0 and nb_eok_month is not None:
            computed_multiple = round(nb_eok_month / premium_eok_month, 2)
            stats["with_computed_multiple"] += 1

        v = val_idx.get(name) or {}
        if v.get("status") == "pass":
            stats["validation_pass"] += 1
        elif v.get("status") == "fail":
            stats["validation_fail"] += 1

        companies.append(
            {
                "company": name,
                "sector": sector_of(name),
                "csm_closing_eok": csm_eok,
                "nb_csm_eok_annual": nb_eok_annual,
                "nb_csm_eok_monthly": nb_eok_month,
                "wolnap_premium_eok_month": premium_eok_month,
                "wolnap_premium_period": premium_period,
                "nb_csm_multiple": computed_multiple,
                "multiple_source": premium_source,
                "validation_status": v.get("status"),
                "ir_disclosed_multiple": v.get("ir_disclosed_multiple"),
                "validation_rel_diff": v.get("rel_diff"),
                "color": color_ratio(computed_multiple),
                "status": wf_row.get("status"),
            }
        )

    companies.sort(key=lambda c: (-(c.get("csm_closing_eok") or 0), c["company"]))

    return {
        "_meta": {
            "chart": "IFRS17 CSM bubble (index.html lower panel)",
            "definition": "NB CSM multiple = IFRS17 new_business CSM (monthly) ÷ 월납환산 premium (monthly)",
            "numerator_period": wf.get("period"),
            "size_field": "csm_closing_eok (억원)",
            "color_field": "nb_csm_multiple (×)",
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/viz_build_csm_bubble.py",
            "premium_source": str(PREMIUM_PATH.relative_to(ROOT)).replace("\\", "/"),
            "validation_source": str(VALIDATION_PATH.relative_to(ROOT)).replace("\\", "/"),
            "coverage": stats,
            "validation_summary": validation.get("_meta"),
        },
        "companies": companies,
    }


def write_embed(payload: dict, path: Path) -> None:
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    path.write_text(
        f"// Auto-built by scripts/viz_build_csm_bubble.py\nwindow.CSM_BUBBLE_DATA = {blob};\n",
        encoding="utf-8",
    )


def main() -> int:
    payload = build_payload()
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_embed(payload, OUT_EMBED)
    TEMPLATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_embed(payload, TEMPLATES_EMBED)

    cov = payload["_meta"]["coverage"]
    vs = payload["_meta"].get("validation_summary") or {}
    print(f"Wrote {OUT_PATH}")
    print(
        f"  bubble: csm={cov['with_csm']} premium={cov['with_premium']} "
        f"computed_mult={cov['with_computed_multiple']}"
    )
    print(f"  validation: pass={cov['validation_pass']} fail={cov['validation_fail']} (cohort {vs.get('cohort_tested')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
