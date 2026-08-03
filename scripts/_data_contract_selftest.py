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


CAPSEC_SOURCE = "data/bonds/capital_securities_fy2025.json"   # DART 계보 (실재 경로여야 함:
SENS_SOURCE = "data/dart/viz/sensitivity_heatmap.json"        # verify가 디스크 존재를 확인한다)


def base_sidecars(sens_quarter=LATEST, sens_as_of="2026-03-31"):
    """CHECK 2가 보는 4개 마스터의 **유효한** provenance 사이드카.

    2026-08-03 UH-3 end-state 전환으로 **사이드카 부재 = RED**가 됐다 → baseline이 사이드카를
    갖고 있어야 clean이 성립한다(종전 `provenance_sidecars={}`는 이제 4 RED)."""
    def capsec(master):
        return {"master": master, "cells": [
            {"quarter": LATEST, "item_block": master, "source_id": "DART",
             "as_of_date": "2026-03-31", "source_file": CAPSEC_SOURCE,
             "effective_filtered": True}]}

    return {
        "sensitivity_heatmap": {"master": "sensitivity_heatmap", "cells": [
            {"company_code": "KR9001", "quarter": sens_quarter, "item_block": "sensitivity",
             "as_of_date": sens_as_of, "source_file": SENS_SOURCE}]},
        "forward_capital": capsec("forward_capital"),
        "tier1_utilization": capsec("tier1_utilization"),
        "tier2_utilization": capsec("tier2_utilization"),
    }


def base_inject(**over):
    """clean baseline — 이 상태로 run_gate 하면 RED=0 이어야 한다."""
    d = dict(
        kics_records=base_kics(),
        wf={}, pl={},
        delegate_kics=False,          # K-ICS rule 위임은 합성데이터에 무의미 → 끔
        provenance_sidecars=base_sidecars(),
        sensitivity_heatmap={"companies": [
            {"company": "KR9001", "period": "FY2026", "as_of": "2026-03-31",
             "scenarios": [{"x": 1}]}]},
        forward_manifest={"baseline_quarter": LATEST},
        forward_rows=[{"insurer_code": "KR9001", "insurer_name": "KR9001",
                       "outstanding_bonds_total_eok": 100.0,        # == 소스 total 10,000백만
                       "confidence_reasons": ["t1_reconciled"]}],
        tier1_latest={"quarter": LATEST, "results": [
            {"code": "KR9001", "company": "KR9001",
             "tier1_hybrid_issued_eok": 40.0,                       # == 소스 hybrid 4,000백만
             "tier1_grandfathered_hybrid_eok": 0.0}]},
        tier2_latest={"quarter": LATEST, "results": [
            {"code": "KR9001", "company": "KR9001", "tier2_limit_eok": 250.0,
             "utilization_pct": 40.0, "data_source": "table",
             "new_subordinated_gross_eok": 60.0,                    # == 소스 sub 6,000백만
             "grandfathered_subordinated_eok": 0.0}]},              # 250 == SCR(500)×50%
        # capital-securities 커버리지 census(owner 20260803T0310Z)의 입력.
        # 세 마스터가 per-bond 소스를 **선언**했고 그 소스에 발행 회사 레코드가 있는 상태 = clean.
        capsec_source_files={m: ["data/bonds/capital_securities_fy2025.json"]
                             for m in ("forward_capital", "tier1_utilization", "tier2_utilization")},
        capsec_bond_source={"KR9001": {"n_bonds": 2, "hybrid_mn": 4000.0,
                                       "sub_mn": 6000.0, "total_mn": 10000.0}},
        forward_prior_rows=None,
        # 2026-08-03: 계보별(per-lineage) 구조로 변경 — 2c가 "쓰이는 계보마다" 증거를 요구한다
        # (owner 20260803T0056Z §3). 종전 flat dict을 그대로 두면 키가 계보로 오해된다.
        # 계보 키는 사이드카가 선언한 소스(CAPSEC_SOURCE = DART)와 일치시킨다.
        bond_effective_evidence={"DART": {"snapshot_present": True, "has_status_field": True,
                                         "has_effective_call_date": True,
                                         "called_or_matured_in_recognized": False,
                                         "leak_detail": None}},
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
    """heatmap이 FY2024 기준으로 얼어붙음. 사이드카도 그 낡은 기준일을 **정직하게** 선언한다
    (거짓 라벨이 아니라 stale basis 자체를 잡는 케이스) → 요구 기준분기보다 오래됨 = RED."""
    return base_inject(
        sensitivity_heatmap={"companies": [
            {"company": "KR9001", "period": "FY2024", "as_of": "2024-12-31",
             "scenarios": [{"x": 1}]}]},
        provenance_sidecars=base_sidecars(sens_quarter="2024.4Q", sens_as_of="2024-12-31"))


def f_donut_bug():
    ev = {k: dict(v) for k, v in base_inject()["bond_effective_evidence"].items()}
    ev["DART"]["called_or_matured_in_recognized"] = True
    return base_inject(bond_effective_evidence=ev)


def f_missing_sidecar():
    """UH-3 end-state(2026-08-03): 사이드카 **부재 = RED**. 2026-07-21~08-03 사이엔 YELLOW라
    발행 경로가 씻겨나가도 push를 못 막았다 — 4종 전부 발행된 뒤에는 부재가 정상 상태가 아니다."""
    sc = base_sidecars()
    del sc["tier1_utilization"]
    return base_inject(provenance_sidecars=sc)


def f_source_id_lineage_mismatch():
    """capital-securities 사이드카가 **DART 파일**을 가리키면서 `source_id: FSC_BONDS`로 선언.
    2026-08-03까지 게이트는 FSC_BONDS를 하드코딩 요구했기 때문에 이 거짓 라벨이 **통과**했다
    (owner 20260803T0056Z, PM-2026-08-03). 이제 계보 불일치 = RED."""
    sc = base_sidecars()                     # 결함은 하나만 — 나머지 3종은 유효하게 둔다
    sc["tier2_utilization"] = {
        "master": "tier2_utilization",
        "cells": [{"quarter": LATEST, "item_block": "tier2_utilization",
                   "source_id": "FSC_BONDS",                       # ← 거짓 라벨
                   "as_of_date": "2026-03-31",
                   "source_file": CAPSEC_SOURCE,                   # ← 실제는 DART
                   "effective_filtered": True}]}
    return base_inject(provenance_sidecars=sc)


def f_capsec_absent_in_source():
    """마스터는 회사 행을 발행하는데 **선언된 per-bond 소스에 그 회사 레코드가 없다**.
    2026-08-03까지 이 상태가 `bond_coverage=no_bonds_in_dart`(=무발행)와 한 값으로 뭉개져
    RED=0으로 통과했다 — KR0050/KR0076의 발행잔액 3,700억이 사라지고 2030 지급여력비율이
    낙관 방향으로 뒤집혔는데도(owner 20260803T0310Z). 소스에 없음 = 미검증 = RED."""
    return base_inject(capsec_bond_source={})


def f_capsec_adapter_drop():
    """소스엔 후순위 잔액이 있는데 tier2 마스터가 0 — 어댑터/필터가 조용히 떨어뜨린 경우.
    분자가 0이 되면 소진율이 **낮게** 보이는 같은 방향의 낙관 오류."""
    return base_inject(tier2_latest={"quarter": LATEST, "results": [
        {"code": "KR9001", "company": "KR9001", "tier2_limit_eok": 250.0,
         "utilization_pct": 40.0, "data_source": "table",
         "new_subordinated_gross_eok": 0.0,                 # ← 소스 60억이 사라짐
         "grandfathered_subordinated_eok": 0.0}]})


def f_capsec_source_unresolved():
    """사이드카가 per-bond 소스를 선언하지 않으면 커버리지 census가 **빈 껍데기**가 된다
    (2c가 FSC 스냅샷 하나만 보다 겪은 실패 유형). 검사축 소실 = 통과 아님."""
    files = dict(base_inject()["capsec_source_files"])
    files["tier2_utilization"] = []
    return base_inject(capsec_source_files=files)


def f_capsec_prior_drop():
    """보조축(그물): 직전 배포 스냅샷 대비 전사 발행잔액 급감 → YELLOW(비차단)."""
    return base_inject(forward_prior_rows=[
        {"insurer_code": "KR9001", "outstanding_bonds_total_eok": 500.0}])   # 500 → 100 = -80%


def f_capsec_amount_mismatch():
    """소스와 마스터 금액이 어긋남(0은 아님) — 부분 유실/이중계상. 관찰기 YELLOW."""
    rows = [dict(base_inject()["forward_rows"][0])]
    rows[0]["outstanding_bonds_total_eok"] = 50.0                # 소스 100억의 절반
    return base_inject(forward_rows=rows)


def f_csm_magnitude_implausible():
    """KR0075류: **항등식은 닫히나 규모가 100배 비정상**. closure 검사는 스케일과 무관하게 통과하고
    절대값 가드(CSM_ABS_CAP)도 밑이라 수개월 라이브 노출됐다(PM-2026-07-30 UH-6).
    코호트 13사는 기말CSM/지급여력금액 = 0.5, 1사만 50 (median의 100배) → 임계 median×10 초과."""
    codes = FILERS + [f"KR90{i:02d}" for i in range(10, 20)]        # 14사 (>= 최소표본 10)
    rows = []
    for q in QS:
        for c in codes:
            rows.append(rec(c, q, 1, "1000"))
            rows.append(rec(c, q, 14, "500"))
    wfc = {(c, LATEST): {"기말CSM": 500.0} for c in codes}
    wfc[(codes[-1], LATEST)] = {"기말CSM": 50000.0}                 # r=50 vs median 0.5
    return base_inject(kics_records=rows, wf_by_code=wfc)


def f_concept_penalty():
    """tier2 Face↔BS 개념차이로 confidence를 깎으면 guard 위반(=탐지돼야 함)."""
    return base_inject(forward_rows=[
        {"insurer_name": "KR9001", "confidence_reasons": ["t2_face_vs_bs gap"]}])


# 결함은 '하나만' 심는다 — 아래 두 fixture는 분모/소진율만 손대고 발행잔액 필드는 baseline 값을
# 유지한다(빠뜨리면 CAPSEC_COVERAGE_REGRESSION이 같이 터져 케이스가 둘을 섞는다).
_T2_SUB = {"new_subordinated_gross_eok": 60.0, "grandfathered_subordinated_eok": 0.0}


def f_t2_denom():
    return base_inject(tier2_latest={"quarter": LATEST, "results": [
        {"code": "KR9001", "company": "KR9001", "tier2_limit_eok": 1000.0,  # ≠ SCR×50%
         "utilization_pct": 40.0, "data_source": "table", **_T2_SUB}]})


def f_t2_util_no_exemption():
    return base_inject(tier2_latest={"quarter": LATEST, "results": [
        {"code": "KR9001", "company": "KR9001", "tier2_limit_eok": 250.0,
         "utilization_pct": 130.0, "data_source": "proxy", **_T2_SUB}]})   # >100% + 면제표 미파싱


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
    ("C3 MISSING_PROVENANCE_SIDECAR (UH-3 RED)", f_missing_sidecar,        {"MISSING_PROVENANCE_SIDECAR"}),
    ("D  WRONG_CONCEPT_PENALTY (guard 위반)",    f_concept_penalty,         {"WRONG_CONCEPT_PENALTY"}),
    ("E1 T2_DENOM_NOT_SCR_HALF",                f_t2_denom,                {"T2_DENOM_NOT_SCR_HALF"}),
    ("E2 T2_UTIL_OVER_100_NO_EXEMPTION",        f_t2_util_no_exemption,    {"T2_UTIL_OVER_100_NO_EXEMPTION"}),
    ("F1 POST_TRANSITION_PARENT_MISSING",       f_parent_missing,          {"POST_TRANSITION_PARENT_MISSING"}),
    ("F2 POST_TRANSITION_CHILD_MISSING",        f_child_missing,           {"POST_TRANSITION_CHILD_MISSING"}),
    ("F3 DIVERSIFICATION_NEGATIVE",             f_diversification_negative, {"DIVERSIFICATION_NEGATIVE"}),
    ("F4 ITEM12_EQUALS_ITEM1",                  f_item12_equals_item1,     {"ITEM12_EQUALS_ITEM1"}),
    ("F5 TRANSITION_AFTER_COPY (V17 패턴)",      f_transition_copy,         {"TRANSITION_AFTER_COPY"}),
    ("G1 SOURCE_ID_LINEAGE_MISMATCH",           f_source_id_lineage_mismatch,
     {"SOURCE_ID_LINEAGE_MISMATCH"}),
    # CSM plausibility는 신설 시점 severity=YELLOW(관찰 1~2 릴리스) → 4번째 원소로 기대 YELLOW 지정.
    ("G2 CSM_WATERFALL_PLAUSIBILITY (YELLOW)",  f_csm_magnitude_implausible,
     set(), {"CSM_WATERFALL_PLAUSIBILITY"}),
    ("H1 CAPSEC_COVERAGE_REGRESSION (소스에 회사 없음)", f_capsec_absent_in_source,
     {"CAPSEC_COVERAGE_REGRESSION"}),
    ("H2 CAPSEC_COVERAGE_REGRESSION (어댑터 drop)", f_capsec_adapter_drop,
     {"CAPSEC_COVERAGE_REGRESSION"}),
    ("H3 CAPSEC_SOURCE_UNRESOLVED (검사축 소실)", f_capsec_source_unresolved,
     {"CAPSEC_SOURCE_UNRESOLVED"}),
    ("H4 CAPSEC_COVERAGE_DROP_VS_PRIOR (YELLOW 그물)", f_capsec_prior_drop,
     set(), {"CAPSEC_COVERAGE_DROP_VS_PRIOR"}),
    ("H5 CAPSEC_AMOUNT_MISMATCH (YELLOW 관찰기)", f_capsec_amount_mismatch,
     set(), {"CAPSEC_AMOUNT_MISMATCH"}),
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
    for case in CASES:
        name, fixture, expect = case[0], case[1], case[2]
        expect_yellow = case[3] if len(case) > 3 else None   # None = YELLOW 검사 안 함
        try:
            res = g.run_gate(g.Env(inject=fixture()))
            rules = {f.rule for f in res.red}
            yrules = {f.rule for f in res.yellow}
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
            continue
        missing = expect - rules          # 잡아야 하는데 안 잡음 = 룰 사망
        extra = rules - expect            # 안 잡아야 하는데 잡음 = 오탐
        if expect_yellow:
            missing |= expect_yellow - yrules
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
