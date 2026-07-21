#!/usr/bin/env python3
"""DATA CONTRACT GATE self-test — 게이트를 지키는 게이트 (UH-4, 2026-07-21).

`validate_data_contract.py --selftest` 진입점. 이 모듈이 **부재해서 회귀 suite 자체가 실행 불가**
였던 것을 포스트모템 소급(docs/postmortems, UH-4)이 적발 → 신설.

방식: `Env(inject=...)` 로 **합성 데이터**를 주입하고, 결함을 하나씩 심어 **그 룰이 실제로 RED를
방출하는지** 확인한다(mutation test). 실데이터를 읽지 않으므로 데이터 상태와 무관하게 재현 가능.

커버리지
  A. clean baseline → RED=0 (오탐 없음)
  B. CHECK1 census    : MISSING_FILER_CELL · IMPOSSIBLE_ZERO_AMORT · IMPOSSIBLE_ZERO_LEG
  C. CHECK2 as-of     : STALE_AS_OF · EFFECTIVE_LIST_NOT_FILTERED (donut bug, spec §5.1)
  D. CHECK3 guard     : tier2 Face↔BS는 감점 금지(negative) / 결합 시 WRONG_CONCEPT_PENALTY(positive)
  E. CHECK4 domain    : T2_DENOM_NOT_SCR_HALF · T2_UTIL_OVER_100_NO_EXEMPTION
  F. **1b(iii)/(iv)** : POST_TRANSITION_PARENT_MISSING · POST_TRANSITION_CHILD_MISSING ·
                        DIVERSIFICATION_NEGATIVE · ITEM12_EQUALS_ITEM1 · TRANSITION_AFTER_COPY
                        ← 2026-07-21 lift(UH-1) 회귀 보호. 이게 이 suite의 신설 핵심 이유.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py --selftest
"""
from __future__ import annotations

import sys

QS = ["2025.3Q", "2025.4Q", "2026.1Q"]
LATEST = "2026.1Q"
# 경과조치 적용사(_TRANSITION_APPLIERS)에 실재하는 코드 — 적용후 룰이 대상으로 삼으려면 필요.
APPLIER = "KR0003"
FILERS = [APPLIER, "KR9001", "KR9002", "KR9003"]  # >=3/분기라야 census collapse 오탐 없음


def rec(code, q, item, val, post=None, name=None):
    """K-ICS long-format 레코드 1행. post=None이면 `값_적용후` 키 자체를 넣지 않는다
    (결측과 null을 구분하는 게 census 룰의 핵심이라 키 유무가 의미를 갖는다)."""
    r = {"원보험사코드": code, "원수사명": name or code,
         "항목번호": item, "공시분기": q, "값": val}
    if post is not None:
        r["값_적용후"] = post
    return r


def base_kics():
    """census가 깨끗한 최소 그리드: 4사 × 3분기 item1 + tier2 검사용 item14."""
    rows = []
    for q in QS:
        for c in FILERS:
            rows.append(rec(c, q, 1, "1000"))
            rows.append(rec(c, q, 14, "500"))
    return rows


def base_inject(**over):
    """clean baseline — 이 상태로 run_gate 하면 RED=0 이어야 한다."""
    d = dict(
        kics_records=base_kics(),
        wf={}, pl={},
        delegate_kics=False,          # K-ICS rule 위임은 합성데이터에 무의미 → 끔
        provenance_sidecars={},
        sensitivity_heatmap={"companies": [
            {"company": "KR9001", "period": "FY2026", "as_of": "2026-03-31",
             "scenarios": [{"x": 1}]}]},
        forward_manifest={"baseline_quarter": LATEST},
        forward_rows=[{"insurer_name": "KR9001", "confidence_reasons": ["t1_reconciled"]}],
        tier1_latest={"quarter": LATEST},
        tier2_latest={"quarter": LATEST, "results": [
            {"code": "KR9001", "company": "KR9001", "tier2_limit_eok": 250.0,
             "utilization_pct": 40.0, "data_source": "table"}]},   # 250 == SCR(500)×50%
        bond_effective_evidence={"snapshot_present": True, "has_status_field": True,
                                 "has_effective_call_date": True,
                                 "called_or_matured_in_recognized": False},
    )
    d.update(over)
    return d


# ---------------------------------------------------------------------------
# 결함 주입 fixture (각 케이스는 결함을 '하나만' 심는다)
# ---------------------------------------------------------------------------
def f_missing_filer():
    rows = [r for r in base_kics()
            if not (r["원보험사코드"] == "KR9003" and r["공시분기"] == LATEST)]
    return base_inject(kics_records=rows)


def f_impossible_zero_amort():
    return base_inject(wf={("KR9001", LATEST): {"기초CSM": 1000.0, "기말CSM": 900.0,
                                                "CSM상각": 0.0}})


def f_impossible_zero_leg():
    return base_inject(pl={("KR9001", LATEST): {"생명장기원수손익": 0}})


def f_stale_as_of():
    return base_inject(sensitivity_heatmap={"companies": [
        {"company": "KR9001", "period": "FY2024", "as_of": "2024-12-31",
         "scenarios": [{"x": 1}]}]})


def f_donut_bug():
    ev = dict(base_inject()["bond_effective_evidence"])
    ev["called_or_matured_in_recognized"] = True
    return base_inject(bond_effective_evidence=ev)


def f_concept_penalty():
    """tier2 Face↔BS 개념차이로 confidence를 깎으면 guard 위반(=탐지돼야 함)."""
    return base_inject(forward_rows=[
        {"insurer_name": "KR9001", "confidence_reasons": ["t2_face_vs_bs gap"]}])


def f_t2_denom():
    return base_inject(tier2_latest={"quarter": LATEST, "results": [
        {"code": "KR9001", "company": "KR9001", "tier2_limit_eok": 1000.0,  # ≠ SCR×50%
         "utilization_pct": 40.0, "data_source": "table"}]})


def f_t2_util_no_exemption():
    return base_inject(tier2_latest={"quarter": LATEST, "results": [
        {"code": "KR9001", "company": "KR9001", "tier2_limit_eok": 250.0,
         "utilization_pct": 130.0, "data_source": "proxy"}]})   # >100% + 면제표 미파싱


def f_parent_missing():
    """적용후 부모 continuity break: 3Q present → 4Q 결측 → 1Q present (SANDWICHED)."""
    rows = base_kics()
    rows += [rec(APPLIER, "2025.3Q", 17, "500", post="450"),
             rec(APPLIER, "2025.4Q", 17, "500"),                  # 값_적용후 결측 = break
             rec(APPLIER, "2026.1Q", 17, "500", post="450")]
    return base_inject(kics_records=rows)


def f_child_missing():
    """부모(item15)후 present인데 적용전이 material한 자식(item17)후 결측."""
    rows = base_kics()
    rows += [rec(APPLIER, "2025.4Q", 15, "1000", post="900"),
             rec(APPLIER, "2025.4Q", 17, "500")]                  # 후 결측
    return base_inject(kics_records=rows)


def f_diversification_negative():
    rows = base_kics()
    rows += [rec("KR9001", LATEST, 16, "-100")]                   # 분산효과 < 0 = 물리적 불가
    return base_inject(kics_records=rows)


def f_item12_equals_item1():
    rows = base_kics()
    rows += [rec("KR9001", LATEST, 12, "1000")]                   # item1(1000)과 동일 = 셀밀림
    return base_inject(kics_records=rows)


def f_transition_copy():
    """적용사 item27 후≈전(margin 내) + 금액후 미이동 = 적용전 복사(V17 패턴)."""
    rows = base_kics()
    rows += [rec(APPLIER, LATEST, 27, "100", post="100.05")]
    return base_inject(kics_records=rows)


CASES = [
    # (이름, fixture, 기대 rule 집합, 그 외 RED 허용 안 함)
    ("A  clean baseline (오탐 0)",              base_inject,               set()),
    ("B1 census MISSING_FILER_CELL",            f_missing_filer,           {"MISSING_FILER_CELL"}),
    ("B2 IMPOSSIBLE_ZERO_AMORT (spec §5.4)",    f_impossible_zero_amort,   {"IMPOSSIBLE_ZERO_AMORT"}),
    ("B3 IMPOSSIBLE_ZERO_LEG",                  f_impossible_zero_leg,     {"IMPOSSIBLE_ZERO_LEG"}),
    ("C1 STALE_AS_OF (sensitivity 기준일)",      f_stale_as_of,             {"STALE_AS_OF"}),
    ("C2 EFFECTIVE_LIST_NOT_FILTERED (donut)",  f_donut_bug,               {"EFFECTIVE_LIST_NOT_FILTERED"}),
    ("D  WRONG_CONCEPT_PENALTY (guard 위반)",    f_concept_penalty,         {"WRONG_CONCEPT_PENALTY"}),
    ("E1 T2_DENOM_NOT_SCR_HALF",                f_t2_denom,                {"T2_DENOM_NOT_SCR_HALF"}),
    ("E2 T2_UTIL_OVER_100_NO_EXEMPTION",        f_t2_util_no_exemption,    {"T2_UTIL_OVER_100_NO_EXEMPTION"}),
    ("F1 POST_TRANSITION_PARENT_MISSING",       f_parent_missing,          {"POST_TRANSITION_PARENT_MISSING"}),
    ("F2 POST_TRANSITION_CHILD_MISSING",        f_child_missing,           {"POST_TRANSITION_CHILD_MISSING"}),
    ("F3 DIVERSIFICATION_NEGATIVE",             f_diversification_negative, {"DIVERSIFICATION_NEGATIVE"}),
    ("F4 ITEM12_EQUALS_ITEM1",                  f_item12_equals_item1,     {"ITEM12_EQUALS_ITEM1"}),
    ("F5 TRANSITION_AFTER_COPY (V17 패턴)",      f_transition_copy,         {"TRANSITION_AFTER_COPY"}),
]


def run_selftest() -> int:
    import validate_data_contract as g

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 78)
    print("DATA CONTRACT GATE — SELF-TEST (mutation regression suite)")
    print("=" * 78)

    passed = failed = 0
    for name, fixture, expect in CASES:
        try:
            res = g.run_gate(g.Env(inject=fixture()))
            rules = {f.rule for f in res.red}
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
            continue
        missing = expect - rules          # 잡아야 하는데 안 잡음 = 룰 사망
        extra = rules - expect            # 안 잡아야 하는데 잡음 = 오탐
        if not missing and not extra:
            print(f"  PASS  {name}")
            passed += 1
        else:
            print(f"  FAIL  {name}")
            if missing:
                print(f"          미검출(룰 사망): {sorted(missing)}")
            if extra:
                print(f"          오탐(예상 밖 RED): {sorted(extra)}")
            failed += 1

    total = passed + failed
    print("-" * 78)
    print(f"SELF-TEST: {passed}/{total} passed" + ("" if failed == 0 else f"  ({failed} FAILED)"))
    print("=" * 78)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    raise SystemExit(run_selftest())
