# -*- coding: utf-8 -*-
"""KICS-FORWARD-CAPITAL Phase 3: yearly forward simulation for 5 years out.

Per-insurer projection of 지급여력비율 + 기본자본비율 across 2026~2030 year-ends.

Numerator (가용자본):
  baseline = item1 (값_적용후 if present, else 값) as of FY2025_Q4
  Year-Y: subtract outstanding bonds whose effective_call_date <= year-end
  basic capital: same logic but subtract only tier1_hybrid bonds

Denominator (지급여력기준금액):
  baseline (post-transition, current) = item14 값_적용후 (else 값)
  endpoint (pre-transition, 2032-12-31) = item14 값
  Year-Y: linear interp between baseline and endpoint over (year - 2025) / 7

Phase 3 v2 additions:
- Per-insurer **confidence**: face amount (outstanding bond DB) vs K-ICS BS Tier1/Tier2;
  wired into JSON as `confidence` on each insurer row (see thresholds T*_GAP_*).
- **capacity_exhausted**: when interpolated capital falls to zero or below, reported
  ratio is capped at 0% so negative outliers do not distort charts.

Residual limitations:
- Projection still uses outstanding bonds only + bond calendar effective_call (issue+5y).
  'Called' securities are excluded from the deduction list — may over-state decline until
  fully reconciled to K-ICS 자본성증권 표.
- Insurer count = bond-data cohort size in latest normalized bonds snapshot (not fixed at 19).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

KICS_JSON = REPO / "kics_disclosure.json"
BONDS_DIR = REPO / "data" / "bonds" / "normalized"
OUT_DIR = REPO / "output" / "kics_forward_capital"
TIER1_JSON = REPO / "output" / "tier1_utilization" / "tier1_utilization_20254Q.json"
TIER2_JSON = REPO / "output" / "tier2_utilization" / "tier2_utilization_20254Q.json"

BASELINE_QUARTER = "2025.4Q"
SIM_YEARS = [2026, 2027, 2028, 2029, 2030]
TRANSITION_END_YEAR = 2032
BASELINE_YEAR = 2025  # baseline taken as 2025-12-31

# v3: compare FSC outstanding face to BS table rows (subordinated_eok / tier1 issued),
# NOT tier2 numerator_eok (limit residual after lapse — caused false +15,000% gaps).
T1_GAP_HIGH_PCT = 10.0
T1_GAP_MED_PCT = 30.0
T2_GAP_HIGH_PCT = 30.0
T2_GAP_MED_PCT = 75.0


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _latest_bonds_dir() -> Path:
    candidates = sorted(p for p in BONDS_DIR.iterdir() if p.is_dir())
    if not candidates:
        raise FileNotFoundError(f"No normalized bonds under {BONDS_DIR}")
    return candidates[-1]


def _to_float(v) -> float | None:
    if v in (None, "", "None"):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _value_effective(row: dict, prefer_post: bool = True) -> float | None:
    """Return float value preferring 값_적용후 if present (post-transition baseline)."""
    if prefer_post and row.get("값_적용후") not in (None, "", "None"):
        return _to_float(row["값_적용후"])
    return _to_float(row.get("값"))


def load_kics_baselines() -> dict[str, dict]:
    """For each insurer at BASELINE_QUARTER, extract items 1, 2, 14 in pre/post."""
    data = json.loads(KICS_JSON.read_text(encoding="utf-8"))
    rows = [r for r in data if r.get("공시분기") == BASELINE_QUARTER]
    by_insurer: dict[str, dict] = {}
    for r in rows:
        code = r.get("원보험사코드")
        if not code:
            continue
        try:
            item = int(r.get("항목번호", 0))
        except (ValueError, TypeError):
            continue
        if item not in (1, 2, 14):
            continue
        b = by_insurer.setdefault(code, {"insurer_name": r.get("원수사명"), "items": {}})
        b["items"][item] = {
            "pre": _to_float(r.get("값")),
            "post": _value_effective(r, prefer_post=True),
        }
    return by_insurer


def load_outstanding_bonds() -> tuple[dict[str, list[dict]], str]:
    """Per-insurer outstanding bonds (status='outstanding' only)."""
    bdir = _latest_bonds_dir()
    by_insurer_full = json.loads((bdir / "bonds_by_insurer.json").read_text(encoding="utf-8"))
    out: dict[str, list[dict]] = {}
    for code, g in by_insurer_full.items():
        out[code] = [b for b in g["bonds"] if b.get("status") == "outstanding"]
    return out, bdir.name


def load_utilization() -> tuple[dict, dict]:
    """Return (tier1_by_code, tier2_by_code) from utilization JSONs (v2 confidence input)."""
    t1: dict[str, dict] = {}
    t2: dict[str, dict] = {}
    if TIER1_JSON.exists():
        d = json.loads(TIER1_JSON.read_text(encoding="utf-8"))
        for r in d.get("results", []):
            t1[r["code"]] = r
    if TIER2_JSON.exists():
        d = json.loads(TIER2_JSON.read_text(encoding="utf-8"))
        for r in d.get("results", []):
            t2[r["code"]] = r
    return t1, t2


def _gap_bucket(diff_pct: float | None, high_pct: float, med_pct: float) -> str:
    if diff_pct is None:
        return "no_data"
    a = abs(diff_pct)
    if a <= high_pct:
        return "high"
    if a <= med_pct:
        return "medium"
    return "low"


def _pick_kics_t1_baseline(t1_row: dict | None) -> tuple[float, str]:
    """Return (eok, field_name) for T1 hybrid face reconciliation."""
    if not t1_row:
        return 0.0, "missing"
    for key in ("tier1_hybrid_issued_eok", "tier1_hybrid_recognized_eok"):
        v = _to_float(t1_row.get(key))
        if v and v > 0:
            return v, key
    return 0.0, "missing"


def _pick_kics_t2_baseline(t2_row: dict | None) -> tuple[float, str]:
    """Return (eok, field_name) for T2 subordinated face reconciliation.

    v2 bug used ``numerator_eok`` (limit residual) — e.g. Meritz showed 99.8 vs
    bond face 15,910. Correct peer is ``subordinated_eok`` (기발행 후순위채).
    """
    if not t2_row:
        return 0.0, "missing"
    sub = _to_float(t2_row.get("subordinated_eok"))
    if sub and sub > 0:
        return sub, "subordinated_eok"
    tier2 = _to_float(t2_row.get("tier2_eok"))
    if tier2 and tier2 > 0 and t2_row.get("data_source") == "proxy":
        return tier2, "tier2_eok_proxy"
    num = _to_float(t2_row.get("numerator_eok"))
    if num and num > 0:
        return num, "numerator_eok_fallback"
    return 0.0, "missing"


def _pct_gap(bond: float, kics: float) -> float | None:
    if kics > 0:
        return (bond - kics) / kics * 100.0
    return None


def _overall_bucket(t1_bucket: str, t2_bucket: str) -> str:
    rank = {"high": 3, "medium": 2, "low": 1, "no_data": 0}
    inv = {3: "high", 2: "medium", 1: "low", 0: "no_data"}
    r1, r2 = rank.get(t1_bucket, 0), rank.get(t2_bucket, 0)
    if r1 == 0 and r2 == 0:
        return "no_data"
    if r1 == 0:
        return inv[r2]
    if r2 == 0:
        return inv[r1]
    return inv[min(r1, r2)]


def compute_confidence(code: str, bonds: list[dict], t1: dict, t2: dict) -> dict:
    """Score bond-schedule vs K-ICS BS reconciliation for forward sim trust."""
    bond_t1_out = sum((b.get("issue_amount_won") or 0) / 1e8
                      for b in bonds
                      if b.get("status") == "outstanding" and b.get("tier") == "tier1_hybrid")
    bond_t2_out = sum((b.get("issue_amount_won") or 0) / 1e8
                      for b in bonds
                      if b.get("status") == "outstanding" and b.get("tier") == "tier2_subordinated")

    t1_row = t1.get(code) or {}
    t2_row = t2.get(code) or {}
    kics_t1, kics_t1_field = _pick_kics_t1_baseline(t1_row)
    kics_t2, kics_t2_field = _pick_kics_t2_baseline(t2_row)

    d_t1 = _pct_gap(bond_t1_out, kics_t1)
    d_t2 = _pct_gap(bond_t2_out, kics_t2)
    t1_bucket = _gap_bucket(d_t1, T1_GAP_HIGH_PCT, T1_GAP_MED_PCT)
    t2_bucket = _gap_bucket(d_t2, T2_GAP_HIGH_PCT, T2_GAP_MED_PCT)
    overall = _overall_bucket(t1_bucket, t2_bucket)

    issue_flags: list[str] = []
    reasons: list[str] = []

    if bond_t1_out == 0 and kics_t1 > 0:
        issue_flags.append("fsc_missing_t1")
        reasons.append(f"T1 FSC gap: BS {kics_t1:.0f}억 but bond DB=0")
    if bond_t2_out == 0 and kics_t2 > 0:
        issue_flags.append("fsc_missing_t2")
        reasons.append(f"T2 FSC gap: BS {kics_t2:.0f}억 but bond DB=0")
    if bond_t1_out > 0 and kics_t1 == 0:
        issue_flags.append("kics_missing_t1")
    if bond_t2_out > 0 and kics_t2 == 0:
        issue_flags.append("kics_missing_t2")

    if d_t1 is not None and abs(d_t1) > T1_GAP_MED_PCT:
        reasons.append(f"T1 face/BS gap {d_t1:+.0f}% ({kics_t1_field})")
    if d_t2 is not None and abs(d_t2) > T2_GAP_MED_PCT:
        reasons.append(f"T2 face/BS gap {d_t2:+.0f}% ({kics_t2_field})")

    # Forward sim direction when bond schedule diverges from BS
    sim_bias = "neutral"
    if issue_flags:
        if any(f.startswith("fsc_missing") for f in issue_flags):
            sim_bias = "under_deduct"  # sim misses future calls → ratio too optimistic
        elif bond_t2_out > kics_t2 * 1.5 and kics_t2 > 0:
            sim_bias = "over_deduct"  # FSC face >> BS → sim may cut capital too much
    elif bond_t2_out > kics_t2 * 1.5 and kics_t2 > 0:
        sim_bias = "over_deduct"
    elif bond_t2_out < kics_t2 * 0.5 and kics_t2 > 0 and bond_t2_out > 0:
        sim_bias = "under_deduct"

    if not reasons and overall == "high":
        reasons.append("FSC outstanding face aligns with K-ICS BS table rows")
    if not reasons and overall == "no_data":
        reasons.append("no capital-instruments in either source")

    return {
        "level": overall,
        "tier1_bucket": t1_bucket,
        "tier2_bucket": t2_bucket,
        "t1_gap_pct": round(d_t1, 1) if d_t1 is not None else None,
        "t2_gap_pct": round(d_t2, 1) if d_t2 is not None else None,
        "bond_t1_out_eok": round(bond_t1_out, 1),
        "bond_t2_out_eok": round(bond_t2_out, 1),
        "kics_t1_issued_eok": round(kics_t1, 1),
        "kics_t1_field": kics_t1_field,
        "kics_t2_baseline_eok": round(kics_t2, 1),
        "kics_t2_field": kics_t2_field,
        "kics_t2_numerator_eok": round(_to_float(t2_row.get("numerator_eok")) or 0, 1),
        "tier2_data_source": t2_row.get("data_source"),
        "tier2_quality_flag": t2_row.get("quality_flag"),
        "issue_flags": issue_flags,
        "sim_bias": sim_bias,
        "reasons": reasons,
    }


def simulate_one(insurer_code: str, baseline: dict, bonds: list[dict]) -> dict:
    """Build 5-year projection for one insurer."""
    items = baseline["items"]
    item1 = items.get(1, {})
    item2 = items.get(2, {})
    item14 = items.get(14, {})

    cap_baseline = item1.get("post") or item1.get("pre")
    basic_baseline = item2.get("post") or item2.get("pre")
    scr_post = item14.get("post") or item14.get("pre")
    scr_pre = item14.get("pre") or item14.get("post")

    if cap_baseline is None or scr_post is None or scr_pre is None:
        return {
            "insurer_code": insurer_code,
            "insurer_name": baseline.get("insurer_name"),
            "status": "missing_baseline",
            "missing": {
                "item1_baseline": cap_baseline is None,
                "item14_post": scr_post is None,
                "item14_pre": scr_pre is None,
            },
        }

    # Sort bonds by effective_call_date; convert won → 억원 for unit match
    bond_events: list[dict] = []
    for b in bonds:
        call_date = b.get("effective_call_date")
        amt_won = b.get("issue_amount_won")
        if not call_date or not amt_won:
            continue
        bond_events.append({
            "isin": b["isin"],
            "call_date": call_date,
            "amount_eok": amt_won / 1e8,
            "tier": b.get("tier"),
            "name": b.get("name"),
        })
    bond_events.sort(key=lambda x: x["call_date"])

    projections = []
    transition_span = float(TRANSITION_END_YEAR - BASELINE_YEAR)  # 7
    for year in SIM_YEARS:
        year_end = f"{year}-12-31"
        cumulative_dedu = sum(e["amount_eok"] for e in bond_events if e["call_date"] <= year_end)
        cumulative_dedu_t1 = sum(
            e["amount_eok"] for e in bond_events
            if e["call_date"] <= year_end and e["tier"] == "tier1_hybrid"
        )
        capital_y = cap_baseline - cumulative_dedu
        basic_y = (basic_baseline or 0) - cumulative_dedu_t1

        # SCR linear interp 2025→2032 (post→pre)
        progress = (year - BASELINE_YEAR) / transition_span
        progress = min(max(progress, 0.0), 1.0)
        scr_y = scr_post + (scr_pre - scr_post) * progress

        ratio = (capital_y / scr_y * 100.0) if scr_y else None
        basic_ratio = (basic_y / scr_y * 100.0) if scr_y else None

        # v2: cap at 0% when capital goes negative (capacity exhausted).
        # Avoids misleading -700% etc. for small-baseline insurers (e.g. KR1098 카카오페이).
        capacity_exhausted = capital_y <= 0
        basic_capacity_exhausted = basic_y <= 0
        if capacity_exhausted:
            ratio = 0.0
        if basic_capacity_exhausted:
            basic_ratio = 0.0

        projections.append({
            "year": year,
            "capital_eok": round(capital_y, 1),
            "basic_capital_eok": round(basic_y, 1),
            "scr_eok": round(scr_y, 1),
            "ratio_pct": round(ratio, 2) if ratio is not None else None,
            "basic_ratio_pct": round(basic_ratio, 2) if basic_ratio is not None else None,
            "cumulative_bond_dedu_eok": round(cumulative_dedu, 1),
            "cumulative_tier1_dedu_eok": round(cumulative_dedu_t1, 1),
            "scr_interp_progress": round(progress, 4),
            "capacity_exhausted": capacity_exhausted,
            "basic_capacity_exhausted": basic_capacity_exhausted,
        })

    return {
        "insurer_code": insurer_code,
        "insurer_name": baseline.get("insurer_name"),
        "status": "ok",
        "baseline_2025_4Q": {
            "capital_eok": cap_baseline,
            "basic_capital_eok": basic_baseline,
            "scr_post_eok": scr_post,
            "scr_pre_eok": scr_pre,
            "ratio_post_pct": round(cap_baseline / scr_post * 100, 2),
            "basic_ratio_post_pct": round((basic_baseline or 0) / scr_post * 100, 2) if basic_baseline else None,
        },
        "outstanding_bonds_total_eok": round(sum(e["amount_eok"] for e in bond_events), 1),
        "outstanding_tier1_eok": round(sum(e["amount_eok"] for e in bond_events if e["tier"] == "tier1_hybrid"), 1),
        "projections": projections,
    }


def _sync_forward_data_into_kics_html(results: list[dict]) -> None:
    """Replace ``window.FORWARD_DATA`` line in templates/K-ICS.html (avoids file:// fetch)."""
    html_path = REPO / "templates" / "K-ICS.html"
    html = html_path.read_text(encoding="utf-8")
    blob = json.dumps(results, ensure_ascii=False, separators=(",", ":"))
    replacement = "window.FORWARD_DATA = " + blob + ";"
    new_html, count = re.subn(
        r"^window\.FORWARD_DATA = .+;$",
        replacement,
        html,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        print(f"WARN: templates/K-ICS.html FORWARD_DATA sync skipped (replace count={count})", file=sys.stderr)
        return
    html_path.write_text(new_html, encoding="utf-8")
    print(f"  K-ICS inline: window.FORWARD_DATA updated ({len(blob)} chars)")


def _confidence_histogram(results: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0, "no_data": 0}
    for r in results:
        c = (r.get("confidence") or {}).get("level")
        if c in counts:
            counts[c] += 1
    return counts


def main() -> int:
    baselines = load_kics_baselines()
    bonds_per_insurer, bonds_src = load_outstanding_bonds()
    insurer_codes = sorted(bonds_per_insurer.keys())  # 19 with bond data
    tier1_by_code, tier2_by_code = load_utilization()

    results = []
    for code in insurer_codes:
        bonds = bonds_per_insurer.get(code, [])
        if not baselines.get(code):
            stub = {"insurer_code": code, "status": "missing_kics_baseline"}
            stub["confidence"] = compute_confidence(code, bonds, tier1_by_code, tier2_by_code)
            results.append(stub)
            continue
        row = simulate_one(code, baselines[code], bonds)
        row["confidence"] = compute_confidence(code, bonds, tier1_by_code, tier2_by_code)
        results.append(row)

    stamp = _stamp()
    out_dir = OUT_DIR / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "forward_simulation_v3.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    hist = _confidence_histogram(results)
    manifest = {
        "generated_at": stamp,
        "simulation_version": "v3",
        "baseline_quarter": BASELINE_QUARTER,
        "simulation_years": SIM_YEARS,
        "transition_end_year": TRANSITION_END_YEAR,
        "bonds_source": bonds_src,
        "tier1_utilization_json": str(TIER1_JSON.relative_to(REPO)) if TIER1_JSON.exists() else None,
        "tier2_utilization_json": str(TIER2_JSON.relative_to(REPO)) if TIER2_JSON.exists() else None,
        "kics_source": KICS_JSON.name,
        "insurers_total": len(insurer_codes),
        "ok": sum(1 for r in results if r.get("status") == "ok"),
        "missing_kics_baseline": sum(1 for r in results if r.get("status") == "missing_kics_baseline"),
        "missing_baseline": sum(1 for r in results if r.get("status") == "missing_baseline"),
        "confidence_distribution": hist,
        "notes": [
            "v3: confidence compares FSC outstanding face to BS subordinated_eok / tier1_hybrid_issued (not tier2 numerator residual).",
            "v3: issue_flags (fsc_missing_*) + sim_bias (under_deduct/over_deduct) flag forward sim direction risk.",
            "v2: negative interpolated capital ⇒ ratio_pct/basic_ratio_pct shown as 0% (capacity_exhausted) to avoid distorted charts.",
            "Projection still excludes 'called' bonds from deductions (bond calendar issue+5y); reconcile with 공시표 if needed.",
            "SCR baseline = item14 값_적용후; endpoint by 2032 = item14 값 (linear interp).",
        ],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    templates_latest = REPO / "templates" / "forward_capital_latest.json"
    templates_latest.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    _sync_forward_data_into_kics_html(results)

    print("=== Forward simulation v3 summary ===")
    for k, v in manifest.items():
        if k != "notes":
            print(f"  {k}: {v}")
    print("  confidence (all cohort rows): " + ", ".join(f"{k}={v}" for k, v in hist.items()))

    kr1098 = next((r for r in results if r.get("insurer_code") == "KR1098"), None)
    if kr1098 and kr1098.get("status") == "ok":
        p2030 = next((p for p in kr1098["projections"] if p["year"] == 2030), None)
        if p2030:
            print(
                "  KR1098 2030: ratio_pct={} capacity_exhausted={}".format(
                    p2030.get("ratio_pct"), p2030.get("capacity_exhausted")
                )
            )

    print(f"Output: {out_path}")
    print(f"Templates copy: {templates_latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
