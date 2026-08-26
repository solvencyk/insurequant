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
  N. **1b(v)/(vi) 메타룰** : AXIS_NOT_EVALUATED · AXIS_EVAL_RATE_LOW · EXEMPTION_PROVENANCE_MISSING ·
                        EXEMPTION_CITATION_CONTRADICTED · EXEMPTION_CITATION_UNRESOLVED ·
                        EXEMPTION_LEDGER_SCHEMA_INVALID · SOURCE_UNREADABLE_NOT_VERIFIED
                        ← 2026-08-21 owner 적대적 재검증. "룰이 돌았다"와 "룰이 판정했다"를 가른다.
                        **N8~N10 (2026-08-24)**: EXEMPTION_ABSENCE_PIN_PARTIAL_FILL ·
                        EXEMPTION_PIN_LEDGER_DISAGREE · EXEMPTION_PIN_RE_REGISTERED
                        ← 부재형 면제가 축을 통째로 눈감기던 자리(PM-2026-08-24_absence_
                        exemption_blinded_axis). "면제는 축을 빼는 방식이 아니라 잔차·부재를
                        박제하는 방식으로만 걸린다" 를 회귀로 고정한다.

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
        # 2026-08-21 CHECK 2 2a(iv) 신설분. 여기 없으면 baseline 이 MISSING_PROVENANCE_SIDECAR 로
        # 터진다 — 새 축을 배선하면 selftest baseline 도 같이 늘려야 한다는 계약의 실물.
        "kics_rate_sensitivity": {"master": "kics_rate_sensitivity", "cells": [
            {"company_code": "KR9001", "quarter": LATEST, "item_block": "rate_sensitivity",
             "source_id": "DISCLOSURE_MD", "as_of_date": "2026-03-31",
             "source_file": SENS_SOURCE}]},
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
        # 2026-08-21 CHECK 2 2a(iv). 주입하지 않으면 selftest 가 **디스크 실마스터 522행**을
        # 읽어 합성 사이드카(KR9001 1셀)와 대조하게 되고, 87건 MISSING_PROVENANCE 오탐이 난다.
        rate_sensitivity_rows=[{"원보험사코드": "KR9001", "공시분기": LATEST,
                                "measure구분": "비율", "경과조치여부": "적용전"}],
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


# --- F6~F9: 2026-08-21 적용후 배선 확대의 회귀 그물 -------------------------------------
# 넷 다 "적용전은 깨끗하고 적용후만 깨진" 데이터다 — 적용후 검사가 실제로 도는지만 본다.
# 이 넷이 죽으면 곧 '적용사 18사 한정으로 되돌렸다 / 축 15를 뺐다 / 36_irr 후를 껐다 /
# 적용후 허용오차를 다시 느슨하게 했다' 는 뜻이다.

def f_after_mmult_nonapplier():
    """**비-applier**(KR9001)의 적용후 생명장기 mmult 불일치. 적용전은 정확히 닫힌다
    (sqrt([10]*7·R7)=37.4166). 종전 게이트는 `c not in _TRANSITION_APPLIERS: continue` 라
    이 셀을 아예 안 봤다 = 비-applier 21사 적용후 8,914셀 전량 미검사(false-green)."""
    rows = base_kics()
    rows += [rec("KR9001", LATEST, 17, "37.4166", post="500")]     # 후만 붕괴
    rows += [rec("KR9001", LATEST, i, "10", post="10") for i in range(29, 36)]
    return base_inject(kics_records=rows)


def f_after_mmult_axis15():
    """축 C(기본요구자본) 적용후: item15후 ≠ sqrt([17-20]후·R4) + item21후.
    적용전은 176.3519+20=196.3519 로 닫힌다. 종전 `_TRANS_PARENT_SUBS`가 {17,19}뿐이라
    이 축은 **적용후 검사가 통째로 없었다**. (item15후를 정답보다 '작게' 흔들어 분산효과
    음수 룰과 겹치지 않게 한다 — 케이스당 결함 하나 원칙.)"""
    rows = base_kics()
    subs = {17: "100", 18: "50", 19: "80", 20: "40", 21: "20"}
    rows += [rec("KR9002", LATEST, i, v, post=v) for i, v in subs.items()]
    rows += [rec("KR9002", LATEST, 15, "196.3519", post="150")]
    return base_inject(kics_records=rows)


def f_after_irr():
    """36_irr 적용후: item36후 ≠ 시나리오후(41-46) 도출. 적용전은 닫힌다.
    R상승=100-40=60 · R하락=100-70=30 · R평탄=100-80=20 · R경사=100-90=10 · 평균회귀=100-100=0
    → sqrt(60²+20²)=63.2456. 종전엔 36_irr 적용후 배선이 **아예 없었다**."""
    rows = base_kics()
    sc = {41: "100", 42: "100", 43: "40", 44: "70", 45: "80", 46: "90"}
    rows += [rec("KR9003", LATEST, i, v, post=v) for i, v in sc.items()]
    rows += [rec("KR9003", LATEST, 36, "63.2456", post="200")]
    return base_inject(kics_records=rows)


def f_after_identity_tolerance():
    """적용후 합-항등식 허용오차가 적용전(엔진 flat 2.0)과 같은가.
    item1후 = item2후+item3후 + 3.0 (1000 대비 0.3%). 종전 `max(2.0, 0.5%)`(=5.0)면 통과,
    엔진과 같은 flat 2.0 이면 RED. 한화손해 2024.2Q item1후 복사(4.03억)를 놓친 그 구멍."""
    rows = base_kics()
    rows += [rec("KR9001", LATEST, 1, "1000", post="1003"),
             rec("KR9001", LATEST, 2, "500", post="500"),
             rec("KR9001", LATEST, 3, "500", post="500")]
    return base_inject(kics_records=rows)


# --- O1~O3: 2026-08-21 item23 = item24+25+26 (기타 요구자본 분해) 의 회귀 그물 -----------
# 24/25/26 은 이 날까지 **어떤 항등식도 참조하지 않던 항목**이었다 — 셀은 존재하니 census 는
# 통과하고 값은 아무도 안 봤다. 이 셋이 죽으면 곧 그 세 항목이 다시 무검증으로 돌아갔다는 뜻이다.
# O3 은 **오탐 금지**를 고정한다(결측을 결함으로 세면 라이브에서 97칸이 거짓 RED 가 된다).

def f_other_capital_pre():
    """적용전 분해 붕괴 — 흥국생명 KR0071 2023.3Q 실사례의 축소판.
    raw p11 은 1번 행이 `-` 인데 마스터가 부모값 8,313 을 넣어 합이 정확히 2배가 됐다
    (같은 `-` 인 2번 행은 0 으로 들어감 = 같은 기호를 두 가지로 읽은 파서 dash 버그)."""
    rows = base_kics()
    rows += [rec("KR9001", LATEST, 23, "8313"),
             rec("KR9001", LATEST, 24, "8313"),          # raw 는 '-' → 날조값
             rec("KR9001", LATEST, 25, "0"),
             rec("KR9001", LATEST, 26, "8313")]
    return base_inject(kics_records=rows)


def f_other_capital_post():
    """**적용후만** 붕괴 — 적용전은 300=100+100+100 으로 정확히 닫힌다.
    적용후 컬럼 배선이 살아 있는지만 본다(적용후가 검증사각이었던 전례 PM-2026-07-07)."""
    rows = base_kics()
    rows += [rec("KR9002", LATEST, 23, "300", post="300"),
             rec("KR9002", LATEST, 24, "100", post="100"),
             rec("KR9002", LATEST, 25, "100", post="100"),
             rec("KR9002", LATEST, 26, "100", post="250")]   # 후만 어긋남
    return base_inject(kics_records=rows)


def f_other_capital_partial_is_clean():
    """오탐 금지: 자식이 일부만 공시된 셀(24 만 있고 25/26 없음)은 **결측이지 결함이 아니다**.
    결측을 RED 로 세면 라이브 적용전 59칸 · 적용후 38칸이 통째로 거짓 RED 가 된다."""
    rows = base_kics()
    rows += [rec("KR9003", LATEST, 23, "500"), rec("KR9003", LATEST, 24, "500")]
    return base_inject(kics_records=rows)


# --- N1~N7: 2026-08-21 메타룰(평가율 · 자기미러 · 면제근거 · 판독불가)의 회귀 그물 ----------
# 이 일곱이 죽으면 곧 "판정하지 않은 축이 다시 통과처럼 읽힌다 / 근거 없는 면제를 조용히 추가할 수
# 있다 / 스캔본이 다시 '정당' 으로 세어진다" 는 뜻이다.
# 평가율 룰은 `_AXIS_MIN_GRID`(=20) 이상의 그리드에서만 판정하므로, 아래 두 픽스처는 일부러
# 12사 × 3분기 = 36버킷으로 넓힌다(기존 4사 픽스처로는 룰이 아예 안 깨어난다).
_WIDE = [f"KR9{i:03d}" for i in range(1, 13)]        # KR9001 은 tier2 픽스처가 참조하므로 유지


def wide_kics(codes=None):
    """item14 만 깐다 — item1/2/3 은 축 픽스처가 전·후를 직접 지정하므로 중복행을 만들지 않는다."""
    return [rec(c, q, 14, "500") for q in QS for c in (codes or _WIDE)]


# 'AC'(가용자본 시가평가 자본감소분)를 실제로 신청한 적용사 — R1 축을 움직여야 하는 회사.
# 정본은 `_TRANSITION_KIND`(FSS 붙임-1). 여기서 코드를 재타이핑하지 않고 그 registry 에서 뽑는다.
def _ac_applier():
    from validate_kics_disclosure import _TRANSITION_KIND
    return sorted(c for c, k in _TRANSITION_KIND.items() if "AC" in k)[0]


def f_axis_mirror_applier():
    """**AC 경과조치를 신청한 적용사**의 R1 적용후가 적용전과 한 자리도 다르지 않다 = 적용후 컬럼
    복사 지문(AXIS_SELF_MIRRORED_APPLIER). 항등식은 전·후 모두 깨끗하게 닫힌다 — 즉 **산술이
    틀려서가 아니라 적용후가 적용전의 사본이라서** RED 다."""
    rows = wide_kics()
    c = _ac_applier()
    for q in QS:
        rows += [rec(c, q, 14, "500"),
                 rec(c, q, 1, "1000", post="1000"),
                 rec(c, q, 2, "500", post="500"),
                 rec(c, q, 3, "500", post="500")]
    return base_inject(kics_records=rows)


def f_axis_mirror_nonapplier_is_clean():
    """**경과조치 미적용사**의 R1 적용후가 적용전과 동일 — 이건 정의상 참이라 finding 이 **없어야**
    한다. 2026-08-21 첫 배선이 정확히 여기서 뒤집혔다(정의를 동어반복으로 읽어 축을 RED 로 올림).
    이 케이스는 '무엇을 잡는가'가 아니라 **'무엇을 잡으면 안 되는가'**를 고정한다."""
    rows = wide_kics()
    for q in QS:
        for c in _WIDE:                      # KR9xxx 는 전부 비적용사
            rows += [rec(c, q, 1, "1000", post="1000"),
                     rec(c, q, 2, "500", post="500"),
                     rec(c, q, 3, "500", post="500")]
    return base_inject(kics_records=rows)


def f_axis_eval_rate_low():
    """R1 적용후를 12사 중 4사만 판정 가능하게 만든다(평가 12/36 = 33%). 판정된 칸은 미러가 아니고
    항등식도 닫힌다 → 결함은 0인데 **그리드의 3분의 1만 본 'FAIL 0'** 이다. 비차단 YELLOW."""
    rows = wide_kics()
    for q in QS:
        for c in _WIDE:
            p = c in _WIDE[:4]          # 분기가 아니라 '회사' 로 갈라야 continuity break 가 안 생김
            rows += [rec(c, q, 1, "1000", post="1200" if p else None),
                     rec(c, q, 2, "500", post="600" if p else None),
                     rec(c, q, 3, "500", post="600" if p else None)]
    return base_inject(kics_records=rows)


def f_exemption_provenance_missing():
    """레지스트리엔 면제가 등재돼 있는데 근거 원장에 기록이 아예 없다 = 근거 없이 검사에서 빠진 칸.
    **새 면제를 조용히 추가하는 경로**가 바로 여기다."""
    return base_inject(
        exemption_registries={"_AFTER_SUBRISK_NOT_DISCLOSED": {("KR9001", LATEST)}},
        exemption_ledger=None)


# 인용 원천으로는 저장소에 반드시 존재하는 게이트 소스 자체를 쓴다 — 마커도 그 안의 상수명이라
# 룰이 살아 있는 한 반드시 발견된다(픽스처가 외부 문서의 문구 변경에 흔들리지 않는다).
_CITE_FILE = "scripts/validate_kics_disclosure.py"


def _ledger(entry_over):
    e = {"registry": "_AFTER_SUBRISK_NOT_DISCLOSED", "company": "KR9001", "quarter": LATEST,
         "claim": "적용후 세부표 부재", "claim_kind": "TABLE_ABSENT",
         "status": "VERIFIED", "citation": {"file": _CITE_FILE, "pages": None}, "verify": None}
    e.update(entry_over)
    return {"entries": [e]}


def f_exemption_citation_contradicted():
    """'그 표는 원천에 없다' 는 주장을 게이트가 **인용 원천을 직접 열어** 반증한다. 라이브에서
    KR0003 2026.1Q(p24·p25) · KR0073 2026.1Q(p15) 두 건이 정확히 이렇게 잡힌다 — 둘 다 근거를
    docling MD 에서 읽고 'raw 확인' 이라 적었다."""
    led = _ledger({"verify": {"file": _CITE_FILE,
                              "absent_markers": ["_AFTER_SUBRISK_NOT_DISCLOSED"]}})
    return base_inject(
        exemption_registries={"_AFTER_SUBRISK_NOT_DISCLOSED": {("KR9001", LATEST)}},
        exemption_ledger=led)


def f_exemption_citation_unresolved():
    """인용한 파일이 디스크에 없다 = 확인 불가능한 인용(= 사실상 근거 없음)."""
    led = _ledger({"citation": {"file": "data/disclosure/FY1999_Q9/raw/nope.pdf"}})
    return base_inject(
        exemption_registries={"_AFTER_SUBRISK_NOT_DISCLOSED": {("KR9001", LATEST)}},
        exemption_ledger=led)


def f_exemption_ledger_schema_invalid():
    """원장이 '근거 기록' 에서 '면제 억제기' 로 변질되는 경로를 기계로 막는다.

    2026-08-24 수정: 종전 픽스처는 `verify: None` 이라 `EXEMPTION_VERIFIED_WITHOUT_MARKERS`
    가 **같이** 터져 케이스가 계속 FAIL 이었다(이 라운드 이전부터 50/51). 이 케이스가 고정할
    명제는 '금지 키가 들어오면 RED' 하나이므로 다른 축은 통과시켜 놓는다 — 마커가 도는 verify
    블록을 주고(원천에 없는 문자열이라 반증도 안 난다) 금지 키만 남긴다."""
    led = _ledger({"suppress": True,
                   "verify": {"file": _CITE_FILE,
                              "absent_markers": ["ZZZ_THIS_STRING_IS_NOT_IN_THE_FILE_ZZZ"]}})
    return base_inject(
        exemption_registries={"_AFTER_SUBRISK_NOT_DISCLOSED": {("KR9001", LATEST)}},
        exemption_ledger=led)


def f_exemption_absence_pin_partial_fill():
    """**부재형 면제가 축을 눈감기던 자리** (2026-08-24 사고).

    원장이 '이 셀들은 원천에 없다' 고 박제한 그룹인데 **일부만** 값이 채워진 상태.
    섞인 상태는 항등식을 입력결측 SKIP 으로 만들어 채워진 값이 아무 검사도 안 받게 한다 —
    하나생명 2024.4Q 에서 item33후·item34후가 직전분기 값 복사인 채로 살아남은 경로가
    정확히 이것이다. 전부 결측(= 명제 그대로)이거나 전부 present(= 파생값, 항등식이 검산)
    둘 중 하나여야 한다."""
    # 적용전을 0 으로 둔다 — `_parent_present_child_incomplete_after`(자식 census)는 적용전이
    # material 한 자식만 기대하므로 이 픽스처가 **그 축과 겹치지 않는다**. 케이스는 결함을
    # 하나만 심어야 한다.
    rows = base_kics()
    rows.append(rec("KR9001", LATEST, 17, "100", post="100"))
    rows.append(rec("KR9001", LATEST, 29, "0", post="0"))       # 박제된 셀인데 적용후 값이 있다
    rows.append(rec("KR9001", LATEST, 30, "0"))                 # 같은 그룹인데 적용후 결측
    return base_inject(
        kics_records=rows,
        absence_pins={"_AFTER_SUBRISK_NOT_DISCLOSED": {("KR9001", LATEST): frozenset({29, 30})}})


def f_exemption_absence_pin_all_missing_is_clean():
    """**오탐 금지 고정** — 박제 그룹이 통째로 비어 있는 것은 면제가 지키는 바로 그 상태다."""
    rows = base_kics()
    rows.append(rec("KR9001", LATEST, 17, "100", post="100"))
    rows.append(rec("KR9001", LATEST, 29, "0"))
    rows.append(rec("KR9001", LATEST, 30, "0"))
    return base_inject(
        kics_records=rows,
        absence_pins={"_AFTER_SUBRISK_NOT_DISCLOSED": {("KR9001", LATEST): frozenset({29, 30})}})


def f_exemption_pin_ledger_disagree():
    """**원장 숫자를 아무도 안 읽던 자리** (2026-08-24). 진짜 박제는 코드 상수에 있고 원장은
    사본인데, 둘이 어긋나도 아무 일이 없었다 — 실제로 KR0075 3분기의 축 목록이 어긋나 있었다.
    이제 축 목록·잔차값·부재셀집합 중 하나라도 다르면 RED."""
    led = _ledger({"registry": "_TIER2_ISSUER_INCONSISTENT",
                   "expected_residual": {"3_tier2_composition|적용전": 1.0},
                   "verify": {"file": _CITE_FILE,
                              "absent_markers": ["ZZZ_THIS_STRING_IS_NOT_IN_THE_FILE_ZZZ"]}})
    return base_inject(
        exemption_ledger=led,
        code_pins={("_TIER2_ISSUER_INCONSISTENT", "KR9001", LATEST): {
            "expected_residual": {"3_tier2_composition|적용전": 999.0}}})


def f_exemption_pin_re_registered():
    """**해제된 박제가 조용히 되살아나는 경로.** 원장 `contradicted_pins` 에 적힌 축이 코드에
    다시 등재되면 RED — KR0087 2025.2Q `2_tier1_bridge`(우리 룰 결함으로 해제) 의 tripwire."""
    led = _ledger({"registry": "_TIER2_ISSUER_INCONSISTENT",
                   "expected_residual": {"2_tier1_bridge|적용전": 5.0},
                   "contradicted_pins": {"2_tier1_bridge|적용전": "반증돼 해제된 축"},
                   "verify": {"file": _CITE_FILE,
                              "absent_markers": ["ZZZ_THIS_STRING_IS_NOT_IN_THE_FILE_ZZZ"]}})
    return base_inject(
        exemption_ledger=led,
        code_pins={("_TIER2_ISSUER_INCONSISTENT", "KR9001", LATEST): {
            "expected_residual": {"2_tier1_bridge|적용전": 5.0}}})


def f_source_unreadable_not_verified():
    """'적용후 세부결측(후=전)' 인데 원천이 스캔본 — 종전엔 '구조적으로 정당' 버킷에 섞여 정당
    카운트를 부풀렸다. 확인한 게 아니라 못 읽은 것이므로 별도 카테고리(YELLOW)."""
    rows = base_kics()
    rows.append(rec("KR9001", LATEST, 17, "100", post="100"))    # 부모후 present · 후=전 · 세부후 없음
    return base_inject(kics_records=rows,
                       source_readability={("KR9001", LATEST): "UNREADABLE"})


def bs_rows(assets=1000.0, items=(1, 2, 3, 4)):
    """17BS 마스터 1행 세트 — 자산 1000 = 부채 700 + 자본 300, AOCI 20."""
    vals = {1: assets, 2: 700.0, 3: 300.0, 4: 20.0}
    return [{"원보험사코드": "KR9001", "원수사명": "KR9001", "항목번호": i,
             "공시분기": LATEST, "값": vals[i]} for i in items]


def f_bs_identity():
    """자산총계 != 부채총계 + 자본총계 (연결/별도 오선택·단위 오적용 지문)."""
    return base_inject(ifrs17_bs=bs_rows(assets=1200.0), ifrs17_bs_published=True)


def f_bs_census_missing():
    """코어 항목 4(AOCI) 결측 — 행은 있는데 셀이 비었다."""
    return base_inject(ifrs17_bs=bs_rows(items=(1, 2, 3)), ifrs17_bs_published=True)


def f_bs_unpublished():
    """같은 결함이라도 **아무 페이지도 fetch 하지 않는 마스터**면 push를 막지 않는다(YELLOW).
    배포 keep-list에 오르는 순간 코드 수정 없이 RED로 승격되는 쪽이 위 두 케이스."""
    return base_inject(ifrs17_bs=bs_rows(assets=1200.0))


def wf_continuity(opening=500.0):
    """CSM 워터폴 2개 분기 — 2025.4Q 기말 500, 2026.1Q 기초는 인자대로.
    같으면 clean, 다르면 FY 경계 연속성 위반."""
    return {
        ("KR9001", "2025.4Q"): {"기초CSM": 400.0, "기말CSM": 500.0},
        ("KR9001", "2026.1Q"): {"기초CSM": opening, "기말CSM": 560.0},
    }


def f_csm_continuity_break():
    """2026.1Q 기초가 2025.4Q 기말과 어긋남 — 기시 misparse / 미확정 소급재작성."""
    return base_inject(wf=wf_continuity(opening=560.0))


def div_rows(total=1000.0, payout=50.0, dps=None, stock_total=0.0):
    """배당 마스터 1분기 세트 — 순이익 2000, 현금배당총액 1000 → 배당성향 50%."""
    rows = [{"원보험사코드": "KR9001", "원수사명": "KR9001", "공시분기": LATEST,
             "종류주": "-", "항목번호": i, "값": v}
            for i, v in ((2, 2000.0), (5, total), (6, stock_total), (7, payout))]
    if dps is not None:
        rows.append({"원보험사코드": "KR9001", "원수사명": "KR9001", "공시분기": LATEST,
                     "종류주": "보통주", "항목번호": 8, "값": dps})
    return rows


def div_census(status="000"):
    """수집 census — 기대 그리드의 원천(회사 목록이 아니라 fetch status 가 정한다).
    reprt 는 LATEST 의 분기와 반드시 같아야 한다 — 어긋나면 다른 분기를 기대하게 되어
    모든 배당 케이스에 DIV_CENSUS_MISSING 오탐이 섞인다(실제로 겪음)."""
    reprt = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}[LATEST[5:]]
    return {"cells": [{"kr": "KR9001", "corp_code": "00000001",
                       "year": LATEST[:4], "reprt": reprt, "status": status}]}


def f_div_payout():
    """배당성향 공시값이 배당총액/당기순이익과 안 맞음 (연결/별도 오선택 지문)."""
    return base_inject(dividend=div_rows(payout=35.0), dividend_published=True,
                       dividend_fetch_census=div_census())


def f_div_census_missing():
    """수집 census 는 필링 존재(000)라는데 그 (회사,분기) 행이 마스터에 없음."""
    other = [dict(r, 원보험사코드="KR9002", 원수사명="KR9002") for r in div_rows()]
    return base_inject(dividend=other, dividend_published=True,
                       dividend_fetch_census=div_census())


def f_div_zero_contradiction():
    """현금배당금총액=0 인데 주당현금배당금은 양수 — '-'를 0으로 뭉갠 0값 맹점."""
    return base_inject(dividend=div_rows(total=0.0, payout=0.0, dps=700.0),
                       dividend_published=True, dividend_fetch_census=div_census())


def f_div_census_source_missing():
    """수집 census 파일이 사라지면 결측 검사축이 통째로 없어진다 — 조용히 통과 금지."""
    return base_inject(dividend=div_rows(), dividend_published=True,
                       dividend_fetch_census=None)


def f_div_unpublished():
    """같은 결함이라도 아직 아무 페이지도 fetch 하지 않으면 push 를 막지 않는다(YELLOW)."""
    return base_inject(dividend=div_rows(payout=35.0), dividend_fetch_census=div_census())


def f_csm_sign_convention():
    """신계약 CSM 음수 = 부호역전 지문(예별 2023.4Q 실사례).

    PL 버킷을 같이 준다 — 안 그러면 2026-08-26 신설 `PL_BUCKET_ABSENT_VS_WATERFALL` 이
    (정당하게) 같이 터져 이 케이스가 부호룰을 단독으로 못 재게 된다. 원수CSM상각 47,180백만원
    = 471.8억 이라 상각 항등식은 잔차 0 으로 닫힌다."""
    return base_inject(pl={("KR9001", LATEST): {"원수CSM상각": 47180.0}},
                       wf={("KR9001", LATEST): {"기초CSM": 6055.5, "신계약CSM": -509.7,
                                                "CSM상각": -471.8, "기말CSM": 6774.0}})


def f_pl_bucket_absent_vs_waterfall():
    """워터폴 상각은 큰데 PL 에 그 (회사,분기) 버킷이 **통째로 없다** = 룰 3z 가 방문조차
    못 하던 사각(2026-08-26). 종전에는 완전 침묵이라 게이트 출력이 정상과 바이트 동일했다."""
    return base_inject(wf={("KR9001", LATEST): {"기초CSM": 10000.0, "기말CSM": 9000.0,
                                                "CSM상각": -3760.4}})


def f_pl_bucket_absent_below_threshold_is_clean():
    """상각이 임계(10억) 아래면 대조 의미가 없다 — 부재를 결함으로 보지 않는다."""
    return base_inject(wf={("KR9001", LATEST): {"기초CSM": 100.0, "기말CSM": 95.0,
                                                "CSM상각": -4.2}})


def f_pl_csm_amort_vs_waterfall():
    """워터폴엔 상각이 있는데 PL 원수CSM상각이 결측 = 생명장기 분해 결측(라이브 사고 재현)."""
    return base_inject(
        pl={("KR9001", LATEST): {"원수CSM상각": None}},
        wf={("KR9001", LATEST): {"기초CSM": 10000.0, "기말CSM": 9000.0, "CSM상각": -8029.5}})


def f_pl_ytd_collapse():
    """같은 FY 안에서 누계가 non-zero -> 정확히 0.0 (재빌드 결손 지문)."""
    return base_inject(pl={
        ("KR9001", "2025.3Q"): {"기타사업비용": 35264.2},
        ("KR9001", "2025.4Q"): {"기타사업비용": 0.0},
    })


def f_rs_provenance_missing():
    """CHECK 2 2a(iv): 마스터가 발행한 (회사,분기)가 사이드카에 없으면 MISSING_PROVENANCE.
    이 축이 없던 동안 kics_rate_sensitivity 는 mtime 감시만 받고 as-of·계보는 아무도 안 봤다
    (inbox/parser/20260803T0520Z, UH-8)."""
    return base_inject(rate_sensitivity_rows=[
        {"원보험사코드": "KR9001", "공시분기": LATEST},
        {"원보험사코드": "KR9002", "공시분기": LATEST},   # 사이드카에 없는 회사
    ])


def f_rs_stale_as_of():
    """같은 축의 as-of 어긋남: 사이드카 as_of 분기 ≠ 셀 분기 → STALE_AS_OF."""
    sc = base_sidecars()
    sc["kics_rate_sensitivity"] = {
        "master": "kics_rate_sensitivity",
        "cells": [dict(sc["kics_rate_sensitivity"]["cells"][0], as_of_date="2024-12-31")],
    }
    return base_inject(provenance_sidecars=sc)


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
    ("F6 적용후 mmult — 비-applier 도 검사",       f_after_mmult_nonapplier,
     {"TRANSITION_AFTER_MMULT_MISMATCH"}),
    ("F7 적용후 mmult — 축15(기본요구자본 R4)",     f_after_mmult_axis15,
     {"TRANSITION_AFTER_MMULT_MISMATCH"}),
    ("F8 TRANSITION_AFTER_IRR_MISMATCH",         f_after_irr,
     {"TRANSITION_AFTER_IRR_MISMATCH"}),
    ("F9 적용후 항등식 허용오차 = 적용전과 동일",     f_after_identity_tolerance,
     {"TRANSITION_AFTER_IDENTITY"}),
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
    # 17BS(IFRS17_BS.json) — 이 마스터에 남은 룰은 이 둘뿐이라 죽으면 검사축이 통째로 사라진다.
    ("I1 BS_IDENTITY (자산 != 부채+자본)",        f_bs_identity,             {"BS_IDENTITY"}),
    ("I2 BS_CENSUS_MISSING_ITEM (코어 결측)",     f_bs_census_missing,       {"BS_CENSUS_MISSING_ITEM"}),
    ("I3 미배포 마스터는 push 차단 안 함(YELLOW)", f_bs_unpublished,
     set(), {"BS_IDENTITY"}),
    # 배당(dividend.json) — 신규 마스터 3룰 + 검사축 소실 + 미배포 강등(owner 20260814T1625Z).
    ("J1 DIV_PAYOUT_IDENTITY (배당성향 불일치)",   f_div_payout,              {"DIV_PAYOUT_IDENTITY"}),
    ("J2 DIV_CENSUS_MISSING (000인데 행 없음)",   f_div_census_missing,      {"DIV_CENSUS_MISSING"}),
    ("J3 DIV_ZERO_CONTRADICTION (0값 맹점)",      f_div_zero_contradiction,  {"DIV_ZERO_CONTRADICTION"}),
    ("J4 DIV_CENSUS_SOURCE_MISSING (검사축 소실)", f_div_census_source_missing,
     {"DIV_CENSUS_SOURCE_MISSING"}),
    ("J5 미배포 배당 마스터는 YELLOW",              f_div_unpublished,
     set(), {"DIV_PAYOUT_IDENTITY"}),
    # CSM 연속성 — owner 2026-08-15 지시로 validate_master_tables 에서 push 차단 게이트로 승격.
    # clean baseline(wf={})은 위 A 케이스가 이미 오탐 0으로 지킨다.
    ("K1 CSM_CONTINUITY_FY_BOUNDARY",           f_csm_continuity_break,
     {"CSM_CONTINUITY_FY_BOUNDARY"}),
    # PL 누계 붕괴 — 0 은 등식을 깨지 않아 폐쇄식·브리지가 조용히 통과시킨다. 신설 관찰기 YELLOW.
    ("L1 PL_YTD_COLLAPSE_TO_ZERO",                f_pl_ytd_collapse,
     {"PL_YTD_COLLAPSE_TO_ZERO"}),
    # 마스터 2개가 같은 사건을 각자 들고 있으면서 서로를 안 보던 자리 — 라이브 사고(2026-08-15)의 탐지기.
    ("L2 PL_CSM_AMORT_VS_WATERFALL",              f_pl_csm_amort_vs_waterfall,
     {"PL_CSM_AMORT_VS_WATERFALL"}),
    # L2 는 PL 버킷이 **있는데** 셀만 빈 자리를 잡는다. 버킷이 통째로 없으면 그 루프는
    # 방문조차 못 했다 — 실측 12버킷이 그 사각에 있었고 그중 삼성화재 2023.1Q 는 워터폴
    # 상각 3,760.4억이었다(이 룰이 태어난 사고와 같은 회사·같은 모양).
    ("L3 PL_BUCKET_ABSENT_VS_WATERFALL (미순회 사각)", f_pl_bucket_absent_vs_waterfall,
     {"PL_BUCKET_ABSENT_VS_WATERFALL"}),
    ("L4 임계 아래 상각의 버킷 부재는 결함 아님 — finding 0",
     f_pl_bucket_absent_below_threshold_is_clean, set()),
    # 폐쇄식이 잔차(조정)로 닫혀 부호역전을 통과시키는 자리 — 예별 2023.4Q 가 그 실사례였다.
    ("M1 CSM_SIGN_CONVENTION",                    f_csm_sign_convention,
     {"CSM_SIGN_CONVENTION"}),
    # N: 메타룰 — "룰이 돌았다" 와 "룰이 판정했다" 를 가르는 그물 (owner 2026-08-21 적대적 재검증).
    ("N1 AXIS_SELF_MIRRORED_APPLIER (적용사 적용후 복사)", f_axis_mirror_applier,
     {"AXIS_SELF_MIRRORED_APPLIER"}),
    # N1b 는 **오탐 금지**를 고정한다 — 미적용사의 후=전은 정의라 아무 finding 도 나오면 안 된다.
    ("N1b 미적용사 후=전은 정의 — finding 0",          f_axis_mirror_nonapplier_is_clean, set()),
    ("N2 AXIS_EVAL_RATE_LOW (그리드 1/3만 판정, YELLOW)", f_axis_eval_rate_low,
     set(), {"AXIS_EVAL_RATE_LOW"}),
    ("N3 EXEMPTION_PROVENANCE_MISSING (근거 없는 면제)", f_exemption_provenance_missing,
     {"EXEMPTION_PROVENANCE_MISSING"}),
    ("N4 EXEMPTION_CITATION_CONTRADICTED (원천이 반증)", f_exemption_citation_contradicted,
     {"EXEMPTION_CITATION_CONTRADICTED"}),
    ("N5 EXEMPTION_CITATION_UNRESOLVED (인용 파일 부재)", f_exemption_citation_unresolved,
     {"EXEMPTION_CITATION_UNRESOLVED"}),
    ("N6 EXEMPTION_LEDGER_SCHEMA_INVALID (억제기 변질)", f_exemption_ledger_schema_invalid,
     {"EXEMPTION_LEDGER_SCHEMA_INVALID"}),
    ("N7 SOURCE_UNREADABLE_NOT_VERIFIED (스캔본, YELLOW)", f_source_unreadable_not_verified,
     set(), {"SOURCE_UNREADABLE_NOT_VERIFIED"}),
    # N8~N11: 부재형 면제를 **셀 단위 박제**로 바꾼 라운드 (2026-08-24). 종전엔 (회사,분기)
    # 통째로 축을 순회에서 빼서, 그 안의 값이 stale 이어도 게이트 출력이 바이트 동일했다.
    ("N8 EXEMPTION_ABSENCE_PIN_PARTIAL_FILL (부재 박제 부분충전)",
     f_exemption_absence_pin_partial_fill, {"EXEMPTION_ABSENCE_PIN_PARTIAL_FILL"}),
    ("N8b 부재 박제 전부결측은 정상 — finding 0",
     f_exemption_absence_pin_all_missing_is_clean, set()),
    ("N9 EXEMPTION_PIN_LEDGER_DISAGREE (원장≠코드 박제)",
     f_exemption_pin_ledger_disagree, {"EXEMPTION_PIN_LEDGER_DISAGREE"}),
    ("N10 EXEMPTION_PIN_RE_REGISTERED (해제된 박제 재등재)",
     f_exemption_pin_re_registered, {"EXEMPTION_PIN_RE_REGISTERED"}),
    # O: item23 = item24+25+26 — 종전 무참조 항목 3개(24/25/26)를 처음으로 묶는 다리.
    ("O1 OTHER_CAPITAL_CHILDREN_SUM (적용전)",      f_other_capital_pre,
     {"OTHER_CAPITAL_CHILDREN_SUM"}),
    ("O2 OTHER_CAPITAL_CHILDREN_SUM (적용후)",      f_other_capital_post,
     {"OTHER_CAPITAL_CHILDREN_SUM"}),
    ("O3 자식 일부결측은 결함 아님 — finding 0",       f_other_capital_partial_is_clean, set()),
    # P: kics_rate_sensitivity provenance (CHECK 2 2a(iv), UH-8 — 18일 방치 스레드 종결분).
    ("P1 RS MISSING_PROVENANCE (사이드카 미커버 셀)", f_rs_provenance_missing,
     {"MISSING_PROVENANCE"}),
    ("P2 RS STALE_AS_OF (as_of 분기 ≠ 셀 분기)",     f_rs_stale_as_of, {"STALE_AS_OF"}),
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
