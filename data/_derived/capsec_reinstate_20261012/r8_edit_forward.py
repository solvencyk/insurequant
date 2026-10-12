# -*- coding: utf-8 -*-
from pathlib import Path
P = Path("scripts/forward_capital_simulation.py")
t = P.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global t
    assert t.count(old) == count, (t.count(old), old[:70])
    t = t.replace(old, new)


# --- docstring
sub('''  basic capital: same logic but only tier1_hybrid bonds
''', '''  basic capital: 신종(hybrid)만, **증권별 계층**(data/bonds/capital_tier_registry.json, 2026-10-12)을 따른다:
    · legacy_tfi(2022년 이전 기발행)  = min(잔액, SCR_y x 15%)  [Ⅵ.1.가.(1) 공통적용 경과조치]
    · tier1(기본자본형 신규)          = min(잔액, SCR_y x 10%)  [Ⅲ.2.다.(1)②]
    · tier2(보완자본형, 스텝업 등)    = 기본자본 기여 0 -> 콜이 와도 **총자본에서만** 빠지고 기본자본은 불변
    한도를 매 연말 SCR_y 로 다시 계산하므로 콜로 잔액이 줄면 "한도 초과로 보완자본에 재분류된 부분이 먼저,
    그다음 기본자본" 순서가 자동으로 나온다(owner 2026-06-15). 기준시점 기본자본이 회사 공시값이라 계층은
    발행사 K-ICS 표가 실제로 다룬 형(issuer_type, 없으면 type)을 쓰고, 둘이 다른 회사는 baseline_basis_flag=true
    + 우리 분류 기준 대체 경로(basic_ratio_by_type_pct)를 같이 싣는다. 총자본 경로는 계층과 무관하다.
''')

# --- stdout / argparse guards
sub('sys.stdout.reconfigure(encoding="utf-8")\n', '''try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):   # pytest capture 등 reconfigure 없는 스트림
    pass
''')
sub('from scripts.build_capital_securities_recognition import tier2_recognition_rate  # noqa: E402\n',
    '''from scripts.build_capital_securities_recognition import tier2_recognition_rate  # noqa: E402
from scripts.capital_utilization_rules import classify_hybrid, load_registry  # noqa: E402
''')
sub('_args = _ap.parse_args()\n',
    '_args = _ap.parse_args(sys.argv[1:] if __name__ == "__main__" else [])   # import 시(시험)에는 인자를 읽지 않는다\n')

# --- constants
sub('HYBRID_LIMIT_RATIO = 0.15\n', '''HYBRID_LIMIT_RATIO = 0.15          # legacy_tfi(기발행) 한도 - 종전 이름 유지
TIER1_TYPE_LIMIT_RATIO = 0.10      # tier1(기본자본형 신규) 한도 - [별표22] Ⅲ.2.다.(1)② (조건부자본증권 15% 는 보험사 사례 없음)
''')

# --- load_outstanding_bonds: classification
sub('''    src = REPO / _args.bonds_source
    doc = json.loads(src.read_text(encoding="utf-8"))
    out: dict[str, list[dict]] = {}
    for c in doc["companies"]:
        bonds = []''', '''    src = REPO / _args.bonds_source
    doc = json.loads(src.read_text(encoding="utf-8"))
    registry = load_registry().get("companies") or {}
    out: dict[str, list[dict]] = {}
    for c in doc["companies"]:
        reg_entry = registry.get(c["code"]) or {}
        bonds = []''')
sub('''            bonds.append({
                "isin": b.get("name"),''', '''            cls = (classify_hybrid(reg_entry, b.get("issue_date"))
                   if b.get("tier") == "hybrid" else None)
            bonds.append({
                "isin": b.get("name"),
                "issue_date": b.get("issue_date"),
                "hybrid_class": cls,''')

# --- simulate_one: carry classification into events
sub('''            "tier": b.get("tier"),
            "name": b.get("name"),
        })
    bond_events.sort(key=lambda x: x["call_date"])
    total_hybrid = sum(e["amount_eok"] for e in bond_events if e["tier"] == "tier1_hybrid")
    hybrid_events = [e for e in bond_events if e["tier"] == "tier1_hybrid"]
    as_of = _baseline_as_of()
''', '''            "tier": b.get("tier"),
            "name": b.get("name"),
            "issue_date": b.get("issue_date"),
            "hybrid_class": b.get("hybrid_class"),
        })
    bond_events.sort(key=lambda x: x["call_date"])
    hybrid_events = [e for e in bond_events if e["tier"] == "tier1_hybrid"]
    as_of = _baseline_as_of()
    flagged = [e for e in hybrid_events if _cls(e, "basis_type") != _cls(e, "type")]
    unconfirmed = any(_cls(e, "type_unconfirmed") for e in hybrid_events)
''')

# --- loop body
old_loop = t[t.index("        # Tier-priority deduction (owner 2026-06-15)"):t.index("        ratio = (capital_y / scr_y * 100.0) if scr_y else None")]
new_loop = '''        # 증권별 계층 반영(2026-10-12 재공개 라운드). 순서 규칙(owner 2026-06-15)은 그대로다: 매 시점 잔액과
        # 한도(legacy 15% · tier1형 10%)를 다시 계산하면 한도 초과로 보완자본에 재분류된 부분이 먼저 빠지고
        # 그다음 기본자본이 깎인다. 보완자본형(tier2)은 기본자본 기여 0 이라 기본자본이 안 변한다.
        hy = _hybrid_basic(hybrid_events, "basis_type", year_end, as_of, scr_y)
        hy0 = _hybrid_basic(hybrid_events, "basis_type", as_of, as_of, scr_post)
        capital_y = cap_baseline - cumulative_dedu
        basic_y = (basic_baseline or 0) + (hy["basic"] - hy0["basic"])
        hybrid_remaining = hy["remaining"]
        hybrid_t1_y = hy["basic"]
        hybrid_t2_overflow = hy["overflow"]
        limit_y = scr_y * HYBRID_LIMIT_RATIO

        basic_by_type_y = None
        if flagged:
            by = _hybrid_basic(hybrid_events, "type", year_end, as_of, scr_y)
            by0 = _hybrid_basic(hybrid_events, "type", as_of, as_of, scr_post)
            basic_by_type_y = (basic_baseline or 0) + (by["basic"] - by0["basic"])
        basic_if_t2_y = None
        if unconfirmed:
            iy = _hybrid_basic(hybrid_events, "basis_type", year_end, as_of, scr_y, unconfirmed_as_tier2=True)
            iy0 = _hybrid_basic(hybrid_events, "basis_type", as_of, as_of, scr_post, unconfirmed_as_tier2=True)
            basic_if_t2_y = (basic_baseline or 0) + (iy["basic"] - iy0["basic"])

'''
t = t.replace(old_loop, new_loop)

# --- projection payload: additive fields
sub('''            "capacity_exhausted": capacity_exhausted,
            "basic_capacity_exhausted": basic_capacity_exhausted,
        })
''', '''            "capacity_exhausted": capacity_exhausted,
            "basic_capacity_exhausted": basic_capacity_exhausted,
            # --- 2026-10-12 새 필드(additive; 위 기존 필드의 이름·뜻은 그대로) ---
            "hybrid_legacy_remaining_eok": round(hy["by_type"]["legacy_tfi"], 1),
            "hybrid_tier1type_remaining_eok": round(hy["by_type"]["tier1"], 1),
            "hybrid_tier2type_remaining_eok": round(hy["by_type"]["tier2"], 1),   # 보완자본형: 기본자본 기여 0
            "hybrid_limit_tier1type_eok": round(scr_y * TIER1_TYPE_LIMIT_RATIO, 1),   # SCR_y x 10%
            "basic_capital_by_type_eok": None if basic_by_type_y is None else round(basic_by_type_y, 1),
            "basic_ratio_by_type_pct": (None if basic_by_type_y is None or not scr_y
                                        else round(max(basic_by_type_y, 0.0) / scr_y * 100.0, 2)),
            "basic_ratio_if_tier2_type_pct": (None if basic_if_t2_y is None or not scr_y
                                              else round(max(basic_if_t2_y, 0.0) / scr_y * 100.0, 2)),
        })
''')

# --- row-level fields
sub('''        "outstanding_tier1_eok": round(sum(e["amount_eok"] for e in bond_events if e["tier"] == "tier1_hybrid"), 1),
        "projections": projections,
    }''', '''        "outstanding_tier1_eok": round(sum(e["amount_eok"] for e in bond_events if e["tier"] == "tier1_hybrid"), 1),
        "projections": projections,
        # --- 2026-10-12 새 필드(additive) ---
        "baseline_basis_flag": bool(flagged),
        "baseline_basis_note": _basis_note(flagged),
        "type_unconfirmed": bool(unconfirmed),
        "outstanding_hybrid_by_type_eok": {
            ty: round(sum(e["amount_eok"] for e in hybrid_events if _cls(e, "type") == ty), 1)
            for ty in ("legacy_tfi", "tier1", "tier2")},
        "hybrid_classification": [
            {"name": e["name"], "issue_date": e.get("issue_date"), "call_date": e["call_date"],
             "amount_eok": round(e["amount_eok"], 1), "type": _cls(e, "type"),
             "issuer_type": _cls(e, "basis_type") if _cls(e, "basis_type") != _cls(e, "type") else None,
             "type_unconfirmed": bool(_cls(e, "type_unconfirmed")), "type_source": _cls(e, "source")}
            for e in hybrid_events],
    }''')

# --- helper functions before simulate_one
sub('''def simulate_one(insurer_code: str, baseline: dict, bonds: list[dict]) -> dict:''', '''def _cls(e: dict, key: str):
    """채권 이벤트의 계층 필드. 신종이 아니면(후순위) 값이 없다."""
    return (e.get("hybrid_class") or {}).get(key)


def _hybrid_basic(events: list[dict], attr: str, at: date, as_of: date, scr: float,
                  unconfirmed_as_tier2: bool = False) -> dict:
    """시점 `at` 의 신종 기본자본 기여.

    attr = "basis_type"(발행사 처리 기준, 기본자본 경로의 정본) | "type"(우리 분류 기준).
    legacy_tfi -> min(잔액, SCR x 15%) · tier1 -> min(잔액, SCR x 10%) · tier2 -> 0.
    unconfirmed_as_tier2: 미확정 증권을 보완자본형으로 보는 대체 경로(type_unconfirmed 회사용).
    """
    by = {"legacy_tfi": 0.0, "tier1": 0.0, "tier2": 0.0}
    for e in events:
        ty = _cls(e, attr)
        if unconfirmed_as_tier2 and _cls(e, "type_unconfirmed"):
            ty = "tier2"
        by[ty] += _contribution(e, at, as_of)
    b_leg = min(by["legacy_tfi"], scr * HYBRID_LIMIT_RATIO)
    b_t1 = min(by["tier1"], scr * TIER1_TYPE_LIMIT_RATIO)
    return {"basic": b_leg + b_t1,
            "overflow": (by["legacy_tfi"] - b_leg) + (by["tier1"] - b_t1),   # 한도 초과 -> 보완자본 재분류
            "remaining": sum(by.values()), "by_type": by}


def _basis_note(flagged: list[dict]) -> str | None:
    """baseline_basis_flag 회사의 한 줄 근거: 기본자본 경로를 어느 기준으로 계산했는지."""
    if not flagged:
        return None
    names = ", ".join(f"{e.get('issue_date')} {e['amount_eok']:,.0f}억" for e in flagged)
    return (f"우리 분류({'/'.join(sorted({_cls(e, 'type') for e in flagged}))})와 발행사 K-ICS 표 처리"
            f"({'/'.join(sorted({_cls(e, 'basis_type') for e in flagged}))})가 다른 신종 [{names}]. "
            "기준시점 기본자본이 회사 공시값이라 기본자본 경로(basic_ratio_pct)는 발행사 실제 처리 기준으로 계산했고, "
            "우리 분류 기준 경로는 basic_ratio_by_type_pct. 총자본(지급여력비율) 경로는 분류와 무관.")


def simulate_one(insurer_code: str, baseline: dict, bonds: list[dict]) -> dict:''')

P.write_text(t, encoding="utf-8", newline="\n")
print("ok")
