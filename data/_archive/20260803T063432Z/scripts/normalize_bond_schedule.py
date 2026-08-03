# -*- coding: utf-8 -*-
"""Normalize FSC bond schedule data into per-ISIN calendar for KICS-FORWARD-CAPITAL.

Input:  data/bonds/<stamp>/schedule_by_insurer.json
Output: data/bonds/normalized/<stamp>/
          bonds_calendar.json    -- flat list of per-ISIN dicts
          bonds_by_insurer.json  -- grouped by insurer_code with totals
          manifest.json

For each ISIN, we collect:
  - issue_date / issue_amount_won  (from "발행" row)
  - maturity_date                  (bondExprDt of "발행" row)
  - fsc_call_dates_raw[]           (from "조기상환일" rows — kept for audit only; unreliable)
  - effective_call_date            (issue_date + 5 years — Korean market convention, ALL bonds)
  - next_deduction_date            (effective_call_date)
  - tier                           ("tier1_hybrid" if name contains 신종자본; else "tier2_subordinated")
  - status                         ("outstanding" / "called" / "matured")
                                     * outstanding: effective_call_date > today  (live in capital)
                                     * called:      effective_call_date <= today < maturity  (assumed Called at 5y)
                                     * matured:     maturity < today (or no Call and past maturity)

Why issue+5y rule for ALL bonds (not just those with "콜" in name):
- Korean insurance capital instruments (신종자본증권, 후순위채) are universally structured
  with 5-year Call. Confirmed cases:
  * 2024-12 Hanwha Life 후순위채 4000억 prospectus: 10년 만기 5년 콜옵션
  * 2022-04 Hanwha Life 신종자본증권 1 (2017 발행) → 5년 콜 행사 (thebell 2022-04-18)
  * 2022 흥국생명 신종자본증권 콜 미행사 시도 → 시장 패닉 → 결국 행사. 즉 미행사는 예외 사례
- isinCdNm의 "(콜/후)" 표기 누락 흔함. name keyword로 gate하면 false negative 다수.
- Step-up coupon + reputational risk make Call de facto mandatory.

Why FSC raw Call data not used:
- Partial coverage (45/171 ISINs) and often equal contractual maturity (= dirty data).
- FSC and Seibro UI both fed by KSD backend but "조기상환권" field commonly omitted for
  unstructured 자본성증권. Korean market convention (5y) is more reliable.

Why `called` status (not "past_call_window"):
- FSC 발행 row is a historical record ("was issued") not a live-status flag.
- Assuming 5y Call exercised eliminates ambiguity. Rare non-exercised cases are known
  exceptions; treat as known overrides in Phase 3 cross-ref with K-ICS disclosure.

Notes:
- 원리금지급일 rows (coupon payments) are NOT retained — irrelevant for K-ICS capital recognition.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = REPO / "data" / "bonds"
OUT_DIR = DATA_DIR / "normalized"

# ISINs confirmed NOT to have exercised Call at 5y (documented exceptions to the 5y convention).
# "treat as known overrides in Phase 3 cross-ref with K-ICS disclosure" (see module docstring).
_CALL_NOT_EXERCISED: frozenset[str] = frozenset({
    "KR60005416C3",  # 흥국화재 신종자본증권1 (2016-12-29, 920억) — 콜 미행사, 2026.1Q FS appendix 기재
})


def _stamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _parse_yyyymmdd(s: str | None) -> str | None:
    """Convert 'YYYYMMDD' to 'YYYY-MM-DD'. Returns None for '9999...' (perpetual) or invalid."""
    if not s or len(s) < 8:
        return None
    yyyy, mm, dd = s[:4], s[4:6], s[6:8]
    if yyyy == "9999":
        return None  # perpetual
    try:
        datetime(int(yyyy), int(mm), int(dd))
    except (ValueError, TypeError):
        return None
    return f"{yyyy}-{mm}-{dd}"


def _classify_tier(name: str | None) -> str:
    """Map FSC isinCdNm to tier1_hybrid vs tier2_subordinated.

    FSC often labels hybrid capital as ``(신종)`` rather than full ``신종자본``.
    Examples: ``농협손해보험3(신종)(사모/콜/후)``, ``농협생명보험4(신종)(사모/콜/후)``.
    Trailing ``/후`` in call notation is not a subordinated-product marker.
    """
    if not name:
        return "tier2_subordinated"
    n = name.replace(" ", "")
    if any(k in n for k in ("신종자본증권", "신종자본", "하이브리드증권", "하이브리드")):
        return "tier1_hybrid"
    if "(신종)" in n:
        return "tier1_hybrid"
    if "(후)" in n or "후순위" in n:
        return "tier2_subordinated"
    if "신종" in n:
        return "tier1_hybrid"
    return "tier2_subordinated"


def _add_years(date_iso: str | None, years: int) -> str | None:
    """Add N years to YYYY-MM-DD. Handles Feb 29 by clamping to Feb 28."""
    if not date_iso:
        return None
    try:
        y, m, d = date_iso.split("-")
        new_y = int(y) + years
        if m == "02" and d == "29":
            d = "28"  # non-leap-year clamp
        # Validate
        datetime(new_y, int(m), int(d))
        return f"{new_y:04d}-{m}-{d}"
    except (ValueError, TypeError):
        return None


def _to_int(s: str | None) -> int | None:
    if s in (None, ""):
        return None
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def _find_latest_schedule_dir() -> Path:
    candidates = sorted(
        [p for p in DATA_DIR.iterdir() if p.is_dir() and (p / "schedule_by_insurer.json").exists()]
    )
    if not candidates:
        raise FileNotFoundError(f"No schedule_by_insurer.json found under {DATA_DIR}")
    return candidates[-1]


def normalize(schedule_rows: list[dict], as_of: date) -> list[dict]:
    by_isin: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in schedule_rows:
        isin = row.get("isinCd")
        evt = row.get("scrsScedDcdNm")
        if not isin or not evt:
            continue
        by_isin[isin][evt].append(row)

    out: list[dict] = []
    for isin, events in sorted(by_isin.items()):
        issue_rows = events.get("발행", [])
        if not issue_rows:
            # Skip ISINs with no 발행 row (cannot determine issue/maturity)
            continue
        head = issue_rows[0]  # 발행 row is unique per ISIN
        name = head.get("isinCdNm")
        issue_date = _parse_yyyymmdd(head.get("bondIssuDt"))
        maturity_date = _parse_yyyymmdd(head.get("bondExprDt"))
        fsc_call_dates_raw = sorted(
            d for d in (_parse_yyyymmdd(r.get("bondExprDt")) for r in events.get("조기상환일", []))
            if d is not None
        )

        # Korean market convention: 5-year Call for ALL capital instruments
        # (regardless of "콜" keyword in name — keyword omission is common).
        # FSC raw 조기상환일 data unreliable (often == maturity); ignore for deduction logic.
        effective_call = _add_years(issue_date, 5)
        next_deduction = effective_call or maturity_date

        # 3-status taxonomy: outstanding / called / matured.
        # Assume Call IS exercised at 5y (Korean market norm — see module docstring).
        # Exception: ISINs in _CALL_NOT_EXERCISED (confirmed by FS notes cross-ref).
        today = as_of.isoformat()
        if maturity_date and maturity_date < today:
            status = "matured"
        elif effective_call and effective_call <= today and isin not in _CALL_NOT_EXERCISED:
            status = "called"            # assumed Called at 5y (de facto mandatory)
        else:
            status = "outstanding"

        out.append({
            "isin": isin,
            "name": name,
            "insurer_code": head.get("_insurer_code"),
            "insurer_name": head.get("bondIsurNm"),
            "tier": _classify_tier(name),
            "issue_date": issue_date,
            "issue_amount_won": _to_int(head.get("bondIssuAmt")),
            "maturity_date": maturity_date,
            "is_perpetual": head.get("bondExprDt", "").startswith("9999"),
            "effective_call_date": effective_call,        # = issue + 5y (Korean convention)
            "next_deduction_date": next_deduction,         # = effective_call (or maturity if no issue date)
            "fsc_call_dates_raw": fsc_call_dates_raw,      # audit only — unreliable
            "irt_chng": head.get("irtChngDcdNm"),
            "status": status,                              # outstanding / called / matured
        })
    return out


def group_by_insurer(calendar: list[dict]) -> dict[str, dict]:
    """Group by insurer. 'outstanding' = effective_call_date > today (assumed live in capital).
    'called' and 'matured' are excluded from outstanding aggregates."""
    grouped: dict[str, dict] = defaultdict(lambda: {
        "insurer_code": None,
        "insurer_name": None,
        "bonds_total": 0,
        "bonds_outstanding": 0,
        "bonds_called": 0,
        "bonds_matured": 0,
        "amount_outstanding_won": 0,
        "tier1_hybrid_outstanding_won": 0,
        "tier2_subordinated_outstanding_won": 0,
        "bonds": [],
    })
    for b in calendar:
        code = b["insurer_code"]
        g = grouped[code]
        g["insurer_code"] = code
        g["insurer_name"] = b["insurer_name"]
        g["bonds_total"] += 1
        g["bonds"].append(b)
        status = b["status"]
        if status == "outstanding":
            g["bonds_outstanding"] += 1
            amt = b["issue_amount_won"] or 0
            g["amount_outstanding_won"] += amt
            if b["tier"] == "tier1_hybrid":
                g["tier1_hybrid_outstanding_won"] += amt
            else:
                g["tier2_subordinated_outstanding_won"] += amt
        elif status == "called":
            g["bonds_called"] += 1
        elif status == "matured":
            g["bonds_matured"] += 1
    return dict(sorted(grouped.items()))


def main() -> int:
    src_dir = _find_latest_schedule_dir()
    src_path = src_dir / "schedule_by_insurer.json"
    rows = json.loads(src_path.read_text(encoding="utf-8"))
    print(f"Source: {src_path} ({len(rows)} rows)")

    as_of = date.today()
    calendar = normalize(rows, as_of=as_of)
    grouped = group_by_insurer(calendar)

    stamp = _stamp_utc()
    out_dir = OUT_DIR / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    cal_path = out_dir / "bonds_calendar.json"
    cal_path.write_text(json.dumps(calendar, ensure_ascii=False, indent=2), encoding="utf-8")

    grp_path = out_dir / "bonds_by_insurer.json"
    grp_path.write_text(json.dumps(grouped, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "generated_at": stamp,
        "as_of": as_of.isoformat(),
        "source_dir": src_dir.name,
        "isins_total": len(calendar),
        "isins_outstanding": sum(1 for b in calendar if b["status"] == "outstanding"),
        "isins_called": sum(1 for b in calendar if b["status"] == "called"),
        "isins_matured": sum(1 for b in calendar if b["status"] == "matured"),
        "insurers_covered": len(grouped),
        "tier_breakdown": {
            "tier1_hybrid": sum(1 for b in calendar if b["tier"] == "tier1_hybrid"),
            "tier2_subordinated": sum(1 for b in calendar if b["tier"] == "tier2_subordinated"),
        },
        "call_date_rule": "issue_date + 5 years for ALL bonds (Korean market convention). FSC raw kept in fsc_call_dates_raw for audit only. Assumed Called at 5y if past today.",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n=== normalize summary ===")
    for k, v in manifest.items():
        print(f"  {k}: {v}")
    print(f"\nOutput dir: {out_dir}")
    for name in ("bonds_calendar.json", "bonds_by_insurer.json", "manifest.json"):
        p = out_dir / name
        print(f"  {name}: {p.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
