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
- Projection still uses outstanding bonds only + bond calendar effective_call (disclosed call
  date, else legal maturity). 'Called'/fully-redeemed securities are excluded from the
  deduction list — may over-state decline until fully reconciled to K-ICS 자본성증권 표.
- Insurer count = bond-data cohort size in the DART per-bond source (not fixed at 19).

2026-08-03 rebase (inbox/parser/20260803T0055Z): bonds source moved from FSC data.go.kr
(data/bonds/normalized/**) to DART per-bond disclosure (data/bonds/capital_securities_fy2025.json,
FY2025 사업보고서, as_of 2025-12-31). KR0050(하나손해보험)/KR0076(아이엠라이프생명보험) have FSC
bond data but no DART annual raw on disk (git-purge) — routed to downloader for refetch; until
backfilled they show bond_coverage=no_bonds_in_dart (flat SCR-interp projection, no bond
deductions), same as any genuinely bond-free insurer.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

KICS_JSON = REPO / "kics_disclosure.json"
BONDS_FY2025_JSON = REPO / "data" / "bonds" / "capital_securities_fy2025.json"  # 기본값(하위호환)
OUT_DIR = REPO / "output" / "kics_forward_capital"

# DART per-bond tier labels -> internal tier labels the simulation/confidence
# logic below already keys off of (kept unchanged from the FSC-era schema).
_TIER_MAP = {"hybrid": "tier1_hybrid", "subordinated": "tier2_subordinated"}
# 분기는 인자로 받는다 (2026-08-31). 그 전에는 20261Q 와 "2026.1Q" 가 리터럴로 박혀 있어
# 새 분기를 돌리려면 파일을 고쳐야 했다. 기본값은 종전 동작 그대로다.
_ap = argparse.ArgumentParser(description="K-ICS forward capital simulation")
_ap.add_argument("--baseline-quarter", default="2026.1Q", help="예: 2026.2Q")
_ap.add_argument("--tier-quarter", default=None,
                 help="confidence 대조용 tier{1,2}_utilization 분기 (기본: --baseline-quarter)")
# 2026-09-01 (owner): 채권 소스가 FY2025 로 **박혀** 있었다. 그 사이 반기 중 상환된 채권이
# 그대로 남아 있어, 이미 사라진 채권을 미래 시점에 또 한 번 가용자본에서 차감하고 있었다
# (docstring "Residual limitations" 가 예고했던 그 결함). 실측 상환 4건 = KB손해 제1회
# 3,790억 · 미래에셋 제2회 2,995억 · 현대해상 후순위3 3,500억 · DB손해 제2회 4,990억.
_ap.add_argument("--bonds-source", default="data/bonds/capital_securities_fy2025.json",
                 help="per-bond 잔액 소스 (repo-relative). 기본은 종전 동작(FY2025 연간). "
                      "반기 갱신본(data/bonds/capital_securities_fy2026h1.json)을 넘기면 "
                      "상환·신규발행이 반영된 잔액으로 전망한다.")
_args = _ap.parse_args()

BASELINE_QUARTER = _args.baseline_quarter
_ty, _tq = (_args.tier_quarter or BASELINE_QUARTER).split(".")
_TIER_TAG = f"{_ty}{_tq}"
TIER1_JSON = REPO / "output" / "tier1_utilization" / f"tier1_utilization_{_TIER_TAG}.json"
TIER2_JSON = REPO / "output" / "tier2_utilization" / f"tier2_utilization_{_TIER_TAG}.json"

SIM_YEARS = [2026, 2027, 2028, 2029, 2030]
TRANSITION_END_YEAR = 2032
BASELINE_YEAR = int(_ty)  # baseline as-of year. Anchors the 경과조치
# phase-out ramp (post→pre over BASELINE_YEAR→2032) at the as-of date, so the ~1yr of
# transitional run-off already baked into the 2026.1Q post values is not double-counted.
# 신종자본증권(hybrid) 기본자본 인정한도 비율 = SCR × 15% (「보험업법」 조건부자본증권;
# 규정 [별표22] Ⅲ.2.다.(1)). compute_tier1_utilization.py LIMIT_RATIO_PRIMARY와 동일.
HYBRID_LIMIT_RATIO = 0.15

# v3: compare FSC outstanding face to BS table rows (subordinated_eok / tier1 issued),
# NOT tier2 numerator_eok (limit residual after lapse — caused false +15,000% gaps).
T1_GAP_HIGH_PCT = 10.0
T1_GAP_MED_PCT = 30.0
T2_GAP_HIGH_PCT = 30.0
T2_GAP_MED_PCT = 75.0


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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
    """Per-insurer outstanding bonds, adapted from the DART per-bond disclosure
    (2026-08-03 rebase off FSC data.go.kr, inbox/parser/20260803T0055Z).

    The adapter maps DART fields onto the schema simulate_one()/compute_confidence()
    already expect (isin/tier/issue_amount_won/status) so the call-roll-off, limit,
    and transition math is untouched. `outstanding_mn` (not `face_amount_mn`) is used
    as the deduction amount: it already reflects any partial paydown (e.g. the small
    FX-translation drift on foreign-currency subordinated bonds), matching the
    2026-05-26 owner directive to deduct the amount actually still owed to investors.
    A bond fully redeemed in-period (outstanding_mn == 0, e.g. "당기 중 전액 상환") is
    dropped, mirroring the old FSC status=='outstanding' filter.

    past_call_outstanding==true bonds (call date passed without redemption, 6 of 119
    in the FY2025 cohort) keep their disclosed call_date as-is rather than rolling
    forward to legal_maturity — this matches how the one FSC-era precedent for the
    same real bond (흥국화재 KR0005 신종자본증권1, effective_call_date=2021-12-29 kept
    outstanding past its own call rule) was handled: the simulation's existing
    call-date-based deduction logic already accounts for this, unchanged.
    """
    src = REPO / _args.bonds_source
    doc = json.loads(src.read_text(encoding="utf-8"))
    out: dict[str, list[dict]] = {}
    for c in doc["companies"]:
        bonds = []
        for b in c.get("bonds", []):
            out_mn = b.get("outstanding_mn")
            if not out_mn:
                continue
            bonds.append({
                "isin": b.get("name"),
                "name": b.get("name"),
                "tier": _TIER_MAP.get(b.get("tier"), b.get("tier")),
                "issue_amount_won": out_mn * 1_000_000,
                "effective_call_date": b.get("call_date") or b.get("legal_maturity"),
                "status": "outstanding",
            })
        out[c["code"]] = bonds
    return out, src.relative_to(REPO).as_posix()


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


def _overall_bucket(t1_bucket: str, t1_real_error: bool, t2_hard_error: bool) -> str:
    """(a) T2-decoupled overall confidence (owner 2026-06-16).

    Overall trust tracks the **T1 reconciliation** (FSC outstanding face ≈ BS issued —
    the two sources nearly agree for 신종, so this is a valid comparison). The T2
    Face-vs-BS gap is a **structural concept difference** (FSC outstanding vs BS K-ICS
    grandfathered-issued 보완자본), NOT a data-quality signal, so it is advisory only and
    never drags overall down. A **genuine** error still forces low: a T1 source mismatch
    (``t1_real_error`` — fsc_missing_t1 / kics_missing_t1) or a real T2 error
    (``t2_hard_error`` — one source missing, or T2 util>100%). This distinguishes real
    data gaps from concept-gap noise (parser dx `inbox/publishing/20260616T0600Z`).
    """
    if t1_real_error or t2_hard_error:
        return "low"
    if t1_bucket == "no_data":
        return "high"          # genuinely no T1 instruments to reconcile → nothing to distrust
    return t1_bucket


def compute_confidence(code: str, bonds: list[dict], t1: dict, t2: dict,
                       bond_coverage: str = "dart_listed") -> dict:
    """Score bond-schedule vs K-ICS BS reconciliation for forward sim trust.

    bond_coverage='no_bonds_in_dart' → the source WAS scanned and the insurer has no
    DART capital instruments. If BS also shows no T1/T2 capital, confidence is 'high'
    (nothing to deduct, nothing to reconcile). bond_coverage='absent_in_source' → the
    insurer is missing from the source entirely (annual raw gap): never shortcut to
    'high', the normal fsc_missing_* flags fire. If BS shows capital but DART is empty,
    those flags fire as usual either way.
    """
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
    t2_bucket = _gap_bucket(d_t2, T2_GAP_HIGH_PCT, T2_GAP_MED_PCT)  # advisory only (a, 2026-06-16)
    # overall computed below after issue_flags — T2 concept-gap decoupled (see _overall_bucket)

    # No-bond insurer with effectively no BS capital → nothing to project against.
    # Forward sim is just SCR-interpolation on flat capital, fully deterministic.
    # Threshold <1.0 (was ==0) tolerates sub-1억 BS rounding residual (e.g. KR1010
    # 교보라이프플래닛 has T2 = 0.1억 — moc 자본성증권 미발행 actual case).
    # 2026-08-03: the literal was still "no_bonds_in_fsc" after the DART rebase renamed the
    # value, so this branch was dead. Restored — but ONLY for the *verified* zero. An insurer
    # that is absent from the source has not been scanned, so "nothing to reconcile → high"
    # would be the optimistic claim this whole ticket is about.
    if (bond_coverage == "no_bonds_in_dart"
            and bond_t1_out < 1.0 and bond_t2_out < 1.0
            and kics_t1 < 1.0 and kics_t2 < 1.0):
        return {
            "level": "high",
            "tier1_bucket": "no_data",
            "tier2_bucket": "no_data",
            "t1_gap_pct": None,
            "t2_gap_pct": None,
            "bond_t1_out_eok": 0.0,
            "bond_t2_out_eok": 0.0,
            "kics_t1_issued_eok": 0.0,
            "kics_t1_field": kics_t1_field,
            "kics_t2_baseline_eok": 0.0,
            "kics_t2_field": kics_t2_field,
            "kics_t2_numerator_eok": round(_to_float(t2_row.get("numerator_eok")) or 0, 1),
            "tier2_data_source": t2_row.get("data_source"),
            "tier2_quality_flag": t2_row.get("quality_flag"),
            "issue_flags": [],
            "sim_bias": "neutral",
            "reasons": ["no capital instruments in FSC or BS — flat capital, SCR-interp only"],
        }

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
        reasons.append(f"T2 face/BS gap {d_t2:+.0f}% ({kics_t2_field}) — advisory, not in overall")

    # (a) T2 decoupling (owner 2026-06-16): overall = T1 reconciliation. A genuine T2
    # error (one source missing, or T2 util>100%) still forces low; the T2 face/BS
    # concept gap (FSC outstanding vs BS grandfathered-issued) does not.
    # NOTE (2026-08-25): this >100 test is **tier2 only** and stays as-is. Tier2's
    # utilization_pct was never capped, so removing the tier1 100% data-cap
    # (wire_capital_securities_to_utilization.py) does not change this rule. T1 is read
    # through _pick_kics_t1_baseline, which uses issued/recognized 금액 — not a 소진율 —
    # so no ≤100 assumption exists on the tier1 side of this script.
    t2_util_over = (t2_row.get("quality_flag") == "util_over_100"
                    or (_to_float(t2_row.get("utilization_pct")) or 0.0) > 100.0)
    if t2_util_over:
        issue_flags.append("t2_util_over_100")
        reasons.append(f"T2 util {_to_float(t2_row.get('utilization_pct')) or 0:.0f}% > 100 (limit breach)")
    t1_real_error = ("fsc_missing_t1" in issue_flags
                     or "kics_missing_t1" in issue_flags)
    t2_hard_error = ("fsc_missing_t2" in issue_flags
                     or "kics_missing_t2" in issue_flags
                     or t2_util_over)
    overall = _overall_bucket(t1_bucket, t1_real_error, t2_hard_error)

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
    """Build 5-year projection for one insurer.

    Per user directive (2026-05-26, Gemini consult): 상환 시 실질 가용자본
    deduction은 **액면가 (face value)** — 실제 투자자 지급액 기준. BS 장부가
    (carrying value) 와의 차이는 발행비용 분할상각 등 회계 artifact 이며 실제
    가용자본 흡수력과 무관. Therefore face-value deduction is correct.
    """
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
    total_hybrid = sum(e["amount_eok"] for e in bond_events if e["tier"] == "tier1_hybrid")

    projections = []
    transition_span = float(TRANSITION_END_YEAR - BASELINE_YEAR)  # 7
    for year in SIM_YEARS:
        year_end = f"{year}-12-31"
        cumulative_dedu = sum(e["amount_eok"] for e in bond_events if e["call_date"] <= year_end)
        cumulative_hybrid_called = sum(
            e["amount_eok"] for e in bond_events
            if e["call_date"] <= year_end and e["tier"] == "tier1_hybrid"
        )

        # SCR linear interp 2025→2032 (post→pre)
        progress = (year - BASELINE_YEAR) / transition_span
        progress = min(max(progress, 0.0), 1.0)
        scr_y = scr_post + (scr_pre - scr_post) * progress

        # Tier-priority deduction (owner 2026-06-15): 신종자본증권 call 차감은 보완자본(Tier-2
        # overflow) → 기본자본(Tier-1) 순서. 별도 분기 없이 매 시점 신종 잔액 H_y와 한도
        # L_y=SCR_y×15%로 min/max 재계산 → 그 순서가 자동으로 나옴 (규정 [별표22] Ⅲ.2.다.(1):
        # 신종 한도초과분=보완자본 재분류). 기본자본 hybrid 기여 = min(H,L)이므로, call로 H가
        # 줄어도 H≥L인 동안은 기본자본 불변(초과분=Tier-2에서만 빠짐), H<L로 떨어지면 기본자본 감소.
        # 후순위채(tier2_subordinated)는 순수 Tier-2 → 총자본에서만 빠지고 기본자본 불변(아래 미반영).
        limit_y = scr_y * HYBRID_LIMIT_RATIO
        hybrid_remaining = total_hybrid - cumulative_hybrid_called
        hybrid_t1_y = min(hybrid_remaining, limit_y)
        hybrid_t1_baseline = min(total_hybrid, scr_post * HYBRID_LIMIT_RATIO)
        hybrid_t2_overflow = max(hybrid_remaining - limit_y, 0.0)

        capital_y = cap_baseline - cumulative_dedu
        basic_y = (basic_baseline or 0) + (hybrid_t1_y - hybrid_t1_baseline)

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
            "cumulative_tier1_dedu_eok": round(cumulative_hybrid_called, 1),  # gross 신종 call 누계
            "hybrid_remaining_eok": round(hybrid_remaining, 1),
            "hybrid_tier1_eok": round(hybrid_t1_y, 1),          # 기본자본 인정분 min(H,L)
            "hybrid_tier2_overflow_eok": round(hybrid_t2_overflow, 1),  # 보완자본 재분류분 max(H-L,0)
            "hybrid_limit_eok": round(limit_y, 1),              # L = SCR_y×15%
            "scr_interp_progress": round(progress, 4),
            "capacity_exhausted": capacity_exhausted,
            "basic_capacity_exhausted": basic_capacity_exhausted,
        })

    baseline_payload = {
        "capital_eok": cap_baseline,
        "basic_capital_eok": basic_baseline,
        "scr_post_eok": scr_post,
        "scr_pre_eok": scr_pre,
        "ratio_post_pct": round(cap_baseline / scr_post * 100, 2),
        "basic_ratio_post_pct": round((basic_baseline or 0) / scr_post * 100, 2) if basic_baseline else None,
    }
    return {
        "insurer_code": insurer_code,
        "insurer_name": baseline.get("insurer_name"),
        "status": "ok",
        # Quarter-agnostic key (UH-7 fix, inbox/publishing/20260803T0210Z): the old
        # key name hardcoded a quarter that drifted out of sync with BASELINE_QUARTER
        # after the 2026-06-16 rebaseline. Consumers read baseline_quarter to know
        # which quarter this is, not the key name.
        "baseline": baseline_payload,
        "baseline_quarter": BASELINE_QUARTER,
        # TEMP alias, drop after designer swaps K-ICS.html off this key (same inbox).
        "baseline_2025_4Q": baseline_payload,
        "outstanding_bonds_total_eok": round(sum(e["amount_eok"] for e in bond_events), 1),
        "outstanding_tier1_eok": round(sum(e["amount_eok"] for e in bond_events if e["tier"] == "tier1_hybrid"), 1),
        "projections": projections,
    }


BOND_COVERAGE_VALUES = ("dart_listed", "no_bonds_in_dart", "absent_in_source")


def _bond_coverage(code: str, bonds: list[dict], bonds_per_insurer: dict) -> str:
    """3-way coverage state (validation inbox 20260803T0310Z — additive, no field removed).

    ``no_bonds_in_dart`` used to mean two very different things at once:
    "the source was scanned and this insurer has no capital securities" and
    "this insurer is not in the source at all". The second is a *coverage gap*
    (annual raw missing) whose 0 removes real bond redemptions from the
    projection — KR0050/KR0076 lost 3,700억 that way and their 2030 지급여력비율
    jumped 124%→146% / 94%→152%, i.e. the error runs in the optimistic direction.
    Splitting the value is what lets the data-contract gate (and a reader of the
    JSON) tell a verified zero from an unverified one.
    """
    if code not in bonds_per_insurer:
        return "absent_in_source"        # 소스에 레코드 자체가 없음 = 미검증 (RED at the gate)
    return "dart_listed" if bonds else "no_bonds_in_dart"   # 스캔 후 무발행 = 정당한 0


def _write_forward_deploy_asset(results: list[dict]) -> None:
    """Write the root deploy asset K-ICS.html fetches for the forward panel.

    Until 2026-07-21 this rewrote the ``window.FORWARD_DATA`` line inside
    K-ICS.html, which is why publishing needed ``--no-html`` (HTML is
    designer-owned). The panel data now lives in its own JSON, so this is a
    plain data artefact and the stage boundary is no longer in the way.

    Keep-list: this file must ship with K-ICS.html or the forward panel
    renders its placeholder.
    """
    out = REPO / "kics_forward_capital.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  deploy asset: {out.name} ({out.stat().st_size:,} bytes, {len(results)} rows)")


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
    # Universe = DART bond cohort ∪ K-ICS baseline cohort. No-bond insurers
    # (e.g. KR0008 삼성화재) still get a flat-capital + SCR-interp projection.
    # Exclude PAA-only insurers (no CSM-driven capital projection makes sense):
    #   KR0150 서울보증보험 (PAA 적용, per F4 v2 report recommendation)
    EXCLUDE_PAA = {"KR0150"}
    insurer_codes = sorted(
        (set(bonds_per_insurer.keys()) | set(baselines.keys())) - EXCLUDE_PAA
    )
    tier1_by_code, tier2_by_code = load_utilization()

    results = []
    for code in insurer_codes:
        bonds = bonds_per_insurer.get(code, [])
        bond_coverage = _bond_coverage(code, bonds, bonds_per_insurer)
        if not baselines.get(code):
            stub = {
                "insurer_code": code,
                "status": "missing_kics_baseline",
                "bond_coverage": bond_coverage,
            }
            stub["confidence"] = compute_confidence(
                code, bonds, tier1_by_code, tier2_by_code, bond_coverage=bond_coverage)
            results.append(stub)
            continue
        row = simulate_one(code, baselines[code], bonds)
        row["bond_coverage"] = bond_coverage
        row["confidence"] = compute_confidence(
            code, bonds, tier1_by_code, tier2_by_code, bond_coverage=bond_coverage)
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
        "bond_coverage_distribution": {
            v: sum(1 for r in results if r.get("bond_coverage") == v)
            for v in BOND_COVERAGE_VALUES
        },
        "confidence_distribution": hist,
        "notes": [
            "Universe = FSC bond cohort ∪ K-ICS baseline cohort. No-bond insurers (bond_coverage='no_bonds_in_fsc') get flat-capital projection: SCR-interp only, no bond deductions.",
            "v3: confidence compares FSC outstanding face to BS subordinated_eok / tier1_hybrid_issued (not tier2 numerator residual).",
            "v3: issue_flags (fsc_missing_*) + sim_bias (under_deduct/over_deduct) flag forward sim direction risk.",
            "v2: negative interpolated capital ⇒ ratio_pct/basic_ratio_pct shown as 0% (capacity_exhausted) to avoid distorted charts.",
            "Projection still excludes 'called' bonds from deductions (bond calendar issue+5y); reconcile with 공시표 if needed.",
            "SCR baseline = item14 값_적용후; endpoint by 2032 = item14 값 (linear interp).",
            "2026-06-16 rebaseline: BASELINE_QUARTER=2026.1Q, tier{1,2}_utilization_20261Q; BASELINE_YEAR=2026 anchors 경과조치 phase-out ramp at the as-of date (avoids double-counting ~1yr run-off already in 2026.1Q post values).",
            "2026-06-16 (a) T2-decoupled confidence: overall = T1 reconciliation only (FSC face≈BS valid). T2 Face(FSC outstanding)-vs-BS(grandfathered issued) gap is a structural concept difference → advisory, NOT in overall. Genuine T2 errors (fsc_missing_t2 / kics_missing_t2 / t2_util_over_100) still force low.",
            "2026-08-03 (b) coverage 3-way (inbox/validation/20260803T0310Z): bond_coverage adds "
            "'absent_in_source' — 소스에 레코드 자체가 없는 회사(annual raw 부재)를 '스캔 후 무발행'"
            "(no_bonds_in_dart)과 구분한다. 전자의 0은 상환차감을 지워 비율을 낙관 방향으로 틀리게 "
            "만든다(KR0050 124→146%, KR0076 94→152%). validate_data_contract.py의 "
            "CAPSEC_COVERAGE_REGRESSION이 같은 축을 소스에서 직접 도출해 RED로 막는다(라벨을 믿지 "
            "않는다). 같은 커밋에서 compute_confidence의 no-bond shortcut 리터럴이 rename 이후 "
            "죽어 있던 것(no_bonds_in_fsc)을 복구하되 absent_in_source에는 적용하지 않는다.",
            "2026-08-03 rebase (inbox/parser/20260803T0055Z): bonds_source is now DART per-bond "
            "(data/bonds/capital_securities_fy2025.json, FY2025 사업보고서, as_of 2025-12-31) — "
            "FSC data.go.kr (data/bonds/normalized/**) no longer read here. bond_coverage renamed "
            "fsc_listed/no_bonds_in_fsc -> dart_listed/no_bonds_in_dart (values only, field name "
            "unchanged). Deduction amount = outstanding_mn (not face_amount_mn), already reflects "
            "partial paydown. KR0050(하나손해보험)/KR0076(아이엠라이프생명보험) had FSC bond data but "
            "have no DART annual raw on disk yet (git-purge) — bond_coverage=no_bonds_in_dart for "
            "these two until downloader backfills FY2025 사업보고서 raw (inbox/downloader routed).",
        ],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    templates_latest = REPO / "templates" / "forward_capital_latest.json"
    templates_latest.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    # No HTML is touched any more (2026-07-21): the panel reads its own JSON, so
    # publishing can produce it without crossing into designer's territory.
    _write_forward_deploy_asset(results)
    # Root provenance sidecar (kics_forward_capital_provenance.json) is derived —
    # not written here — by scripts/emit_capsec_provenance.py, which reads
    # bonds_source back out of this run's manifest.json and looks up source_id
    # from validate_data_contract.source_id_for_lineage (single source of truth,
    # avoids a second hardcoded label drifting out of sync). Run it after this.

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
