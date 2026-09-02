# -*- coding: utf-8 -*-
"""push 게이트 배선 매니페스트 — "mandatory 라고 문서에 썼다" 를 기계가 강제한다.

**왜 있나.** 2026-08-21 에 push 훅(`.githooks/pre-push`)을 만들면서
`scripts/validate_data_contract.py` 하나만 걸었다. 그런데 `CLAUDE.md` 의
"K-ICS validation gate (mandatory)" 절은 push 전에 `validate_kics_disclosure.py` 를 돌리라고
**명시**하고 있었고, 그건 훅에도 CI 에도 없었다. 증거가 코드에 남아 있었다 —
`validate_data_contract.py` 의 주석 *"(prepush_check.py 는 validate_kics_disclosure.py 를
호출하지 않는다) 여기서 같이 건다"*. 빠진 게이트를 눈치챌 때마다 **룰을 한 개씩 베껴 심는**
방식으로 버텨 온 것이다. 전수확인해 보니 8개 중 5개가 호출처 0 이었고, 그중 3개는 **통과하고
있는데도** 아무도 안 부르고 있었다.

그래서 이 테스트는 `scripts/validate_*.py` 를 **전수 열거**하고 각각을 둘 중 하나로 강제한다:
  · `WIRED` — `prepush_check.py` 가 실제로 호출한다(소스에서 확인).
  · `NOT_A_PUSH_GATE` — 왜 push 를 막지 않는지 **사유가 적혀 있다**.
새 `validate_*.py` 를 추가하면 어느 쪽에도 없어서 **여기서 막힌다.** 그때 "이건 push 를
막아야 하나?" 를 한 번은 생각하게 된다 — 그 질문을 아무도 안 해서 생긴 구멍이다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREPUSH = ROOT / "scripts" / "prepush_check.py"

# `prepush_check.py` 가 호출해야 하는 게이트. 값 = 무엇을 막는지(사람이 읽는 용도).
WIRED = {
    "validate_data_contract": "데이터계약 하드게이트 — census/provenance/as-of. RED=push 차단",
    "validate_kics_disclosure": "K-ICS 룰게이트 — CLAUDE.md 'mandatory'. 2026-08-21 2차에 배선",
    "validate_csm_continuity": "CSM 기초≠직전기말 boundary break (2026-08-21 배선, 2초)",
    "validate_kics_rate_sensitivity": "금리민감도 표 정합 (2026-08-21 배선, 3초)",
    "validate_nb_csm_multiple": "신계약 CSM 배수 (2026-08-21 배선, 3초)",
    "validate_disclosure_freshness":
        "새 분기 경영공시 PDF 가 직전 분기와 바이트 동일한지 (2026-08-31 신설, 배선). "
        "2026.2Q 에 KR0011·KR0029·KR0150 세 회사가 1분기 파일을 재탕했고 룰 게이트는 "
        "전부 GREEN 이었다 — 마스터 30항목 중 27개가 1Q 와 같은 값이었는데도. 산수가 맞는 "
        "틀린 소스를 원천에서 막는다. 과거 분기 전수 감사 결과 RED=0 이라 이 사고는 이번 "
        "라운드가 처음이다.",
    "validate_live_artifacts":
        "라이브 HTML 이 fetch 하는 아티팩트를 마스터와 대조 (2026-08-25 신설, 3초). 불변식 1번"
        "('게이트가 검사하는 파일 = 사용자가 보는 파일')의 집행자다. 런타임 추적으로 대조했더니 "
        "배포 HTML 이 fetch 하는 .json 16개 중 6개를 어떤 검사기도 읽지 않고 있었다 — "
        "NB_CSM_multiple · csm_amort_schedule · csm_waterfall_history · insurance_pl_breakdown · "
        "kics_tier{1,2}_utilization(값 축). 기지 결함은 data/_gold/live_artifact_baseline.json 에 "
        "건별 등재되어 매 실행 인쇄되고, 등재에 없는 신규 발견은 RED 로 push 를 막는다.",
    "validate_golden_input_fingerprints":
        "골든 입력지문 — 빌더를 재실행하는 골든 6개는 훅 예산 안에 못 들어간다"
        "(ifrs17_bs 실측 492·514초 · pl_breakdown 95초 opt-in · dividend/viz 2종은 산출을 "
        "인플레이스로 덮어써서 제외). 그 사각으로 2026-08-26 삼성생명 OFS 캐시 정정이 BS "
        "마스터에 반영 안 된 채 이틀간 미검출됐다. 이 게이트는 빌더를 **안 돌리고** "
        "입력·코드·산출 3축 지문만 대조해 '마스터가 자기 입력보다 낡았는가'를 수초에 "
        "판정한다(2026-08-29 신설, owner 승인). 무거운 골든의 대체가 아니라 층이다.",
    "validate_stale_quarter_tables":
        "공시표가 **직전 분기 것**인지 (2026-09-01 신설, 배선, <1초). 롯데손해 2026.1Q 의 TFI "
        "표가 통째로 직전 분기 기준값으로 인쇄돼 있었는데 그것을 잡는 룰이 없었다 — "
        "`48_tier2_limit` 이 잔차를 냈고 사람이 손으로 파고들어서야 원인을 알았다. "
        "`TIER2_LIMIT_STALE` 은 그 뒤에 예외 등재부에 붙인 라벨이지 탐지기가 아니다. 같은 "
        "잔차가 발행사 총괄표/세부표 불일치로도 나므로, 탐지기가 없으면 다음 스테일 표는 "
        "'발행사 불일치' 로 등재되고 원인이 묻힌다 — 스테일 표는 발행사 불일치와 달리 "
        "고칠 수 있는 결함(원천 선택·파싱)이다. 전수 census 오탐 0, 기지 1건은 스크립트 "
        "`_KNOWN` 에 owner 결정과 함께 등재.",
    "validate_csm_waterfall":
        "CSM 워터폴 항등식 + 단계 커버리지. 2026-08-21 에 18건 실패 상태로 발견됐고(호출처 0 이라 "
        "아무도 몰랐다) 같은 날 exit 0 까지 닫혀 WIRED 로 옮겼다. 구조적 제외 6건(IFRS17 시행 전 "
        "FY2022 필링)은 조용한 skip 이 아니라 매 실행 이름과 함께 인쇄된다.",
}

# push 를 막지 않는 것들. **사유 없이 여기 넣지 말 것** — 그게 이 테스트를 무력화하는 방법이다.
NOT_A_PUSH_GATE = {
    "validate_asset_quality":
        "경영공시 3-1/3-2(자산건전성·유가증권 평가손익) 신규 마스터의 검증기 "
        "(2026-08-31 신설). 초회 적재 단계라 아직 닫히지 않았고, 지금 push 게이트에 걸면 "
        "다른 모든 작업이 막힌다. **마스터가 닫히면 WIRED 로 승격할 것.**",
    "validate_management_indicators":
        "경영공시 1-1/1-2/5-1(주요경영지표·경영효율·수익성) 신규 마스터의 검증기 "
        "(2026-08-31 신설, 7,665행·14개 분기). 초회 적재 단계라 아직 닫히지 않았다. "
        "**마스터가 닫히면 WIRED 로 승격할 것.**",
    "validate_insurance_liability_portfolio":
        "경영공시 2-4/2-5(회계모형별 보험부채·무저해지 해지율) 신규 마스터의 검증기 "
        "(2026-08-31 신설). owner 가 '경영공시 PDF 에서 파생되는 테이블을 다 뽑아라' 고 "
        "지시해 만든 마스터이고, 아직 초회 적재 단계라 RED=468 이다. 지금 push 게이트에 "
        "걸면 다른 모든 작업이 막힌다. **마스터가 닫히면 WIRED 로 승격할 것** — 그 전까지는 "
        "손으로 돌려 진척을 재는 용도다.",
    "validate_statutory_reserves":
        "직접 호출은 아니지만 `validate_data_contract.py` 가 법정준비금 절에서 이 모듈을 "
        "import 해 실제로 돌린다(구현이 한 곳에만 있고 게이트는 호출만 한다는 설계). "
        "따라서 RED 는 data-contract 를 통해 push 를 막는다 — 이중 호출하면 같은 검사를 두 번 "
        "돌리게 된다.",
    "validate_master_tables":
        "게이트 본체는 `tests/test_master_tables_golden.py` 가 SUMMARY+exit code 를 박제해 "
        "훅의 오프라인 묶음에서 돌고 있다. 직접 호출하면 기본값이 build_root_masters 를 부르는 "
        "숨은 진입점이라 **마스터가 파괴적으로 재생성된다**(`--no-build` 필수). 골든 경유가 안전.",
}


def _prepush_src() -> str:
    return PREPUSH.read_text(encoding="utf-8")


def _all_validators() -> set[str]:
    return {p.stem for p in (ROOT / "scripts").glob("validate_*.py")}


def test_every_validator_is_declared():
    """`scripts/validate_*.py` 전부가 WIRED 나 NOT_A_PUSH_GATE 중 한 곳에 있어야 한다."""
    declared = set(WIRED) | set(NOT_A_PUSH_GATE)
    found = _all_validators()
    undeclared = sorted(found - declared)
    assert not undeclared, (
        f"미선언 게이트 {undeclared} — push 를 막아야 하는지 정하고 "
        f"tests/test_push_gate_wiring.py 의 WIRED 나 NOT_A_PUSH_GATE 에 사유와 함께 넣어라. "
        f"이 판단을 아무도 안 해서 2026-08-21 에 5개가 호출처 0 이었다."
    )
    ghost = sorted(declared - found)
    assert not ghost, f"매니페스트에만 있고 파일이 없는 게이트 {ghost} — 개명/삭제됐다면 매니페스트도 고쳐라"


@pytest.mark.parametrize("name", sorted(WIRED))
def test_wired_gate_is_actually_called(name):
    """선언만 하고 안 부르는 것을 막는다 — 이 저장소의 반복 사고 그 자체."""
    src = _prepush_src()
    called = (
        re.search(rf"^import {re.escape(name)}\b", src, re.M)
        or re.search(rf'"{re.escape(name)}"', src)
        or re.search(rf'"{re.escape(name)}\.py"', src)
    )
    assert called, (
        f"{name} 이 WIRED 인데 scripts/prepush_check.py 에서 호출을 못 찾았다. "
        f"import 하거나 subprocess 목록에 이름을 넣어라."
    )


def test_wired_gates_are_in_the_blocking_verdict():
    """호출만 하고 exit code 를 안 보면 배선이 아니다 — 출력만 늘어난다."""
    src = _prepush_src()
    m = re.search(r"^\s*blocked = (.+)$", src, re.M)
    assert m, "prepush_check.py 에서 `blocked = ...` 줄을 못 찾았다"
    expr = m.group(1)
    # 게이트들은 n_red / n_kics / n_dom / n_hyg / n_test 로 합류한다. 최소 5개 항이 있어야 한다.
    terms = [t.strip() for t in expr.split(" or ")]
    assert len(terms) >= 5, (
        f"`blocked` 가 {terms} — 배선한 게이트 수보다 적다. 호출해 놓고 판정에 안 넣으면 "
        f"게이트가 아니라 로그다."
    )


@pytest.mark.parametrize("name", sorted(NOT_A_PUSH_GATE))
def test_unwired_gate_has_a_reason(name):
    reason = NOT_A_PUSH_GATE[name]
    assert len(reason) >= 60, (
        f"{name} 의 미배선 사유가 너무 짧다({len(reason)}자). "
        f"'나중에' 같은 말로 게이트를 빼는 것을 막기 위한 최소 길이다."
    )


def test_unwired_gates_still_fail():
    """"지금 깨져 있어서 뺐다" 는 사유가 **아직도 참인지** 매번 확인한다.

    데이터가 고쳐져서 게이트가 통과하기 시작하면 그 사유는 거짓이 된다. 그때 조용히 안 걸린
    채로 남으면 또 honor-system 이다 — 여기서 막고 WIRED 로 옮기게 한다."""
    import subprocess

    name = "validate_csm_waterfall"
    if name not in NOT_A_PUSH_GATE:
        pytest.skip(f"{name} 은 이미 WIRED 로 옮겨졌다")
    script = ROOT / "scripts" / (name + ".py")
    if not script.exists():
        pytest.skip("slim 워크트리")
    # 이 게이트는 자기 산출 JSON 을 덮어쓴다. 테스트가 워킹트리를 더럽히면 안 되므로
    # 바이트를 떠 두고 되돌린다(`prepush_check.py` 의 도메인 게이트 절과 같은 계약).
    out = ROOT / "data" / "dart" / "viz" / "csm_waterfall_validation.json"
    before = out.read_bytes() if out.exists() else None
    try:
        rc = subprocess.run([sys.executable, str(script)], cwd=str(ROOT),
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace").returncode
    finally:
        if before is not None and out.exists() and out.read_bytes() != before:
            out.write_bytes(before)
    assert rc != 0, (
        f"{name} 이 이제 통과한다(exit 0). 미배선 사유('지금 깨져 있다')가 더는 참이 아니다 — "
        f"WIRED 로 옮기고 prepush_check.py 1c 목록에 이름을 넣어라."
    )


def test_claude_md_mandatory_gate_is_wired():
    """`CLAUDE.md` 가 'mandatory' 라고 부르는 게이트가 훅에 실제로 있는지 대조한다.

    이 두 문서가 어긋난 채로 두 달을 갔다 — 문서는 '필수'라고 하고 훅은 안 불렀다."""
    md = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    if "validation gate (mandatory)" not in md:
        pytest.skip("CLAUDE.md 에 mandatory 게이트 절이 없다")
    assert "validate_kics_disclosure.py" in md
    assert "validate_kics_disclosure" in WIRED, (
        "CLAUDE.md 가 mandatory 라고 쓴 게이트가 WIRED 에 없다"
    )


# ---------------------------------------------------------------------------
# data-contract 게이트 **내부** 검사(check_*)의 배선 선언 (2026-08-25 신설)
# ---------------------------------------------------------------------------
# 위 매니페스트는 `scripts/validate_*.py` **파일** 단위만 강제한다. 그런데 한 파일 안의
# `check_*` 하나를 `run_gate()` 에서 빼는 것도 똑같이 게이트를 좁히는 행위인데 아무도 안 봤다.
# 2026-08-25 에 CHECK 5(일반 이상치)를 실제로 뺐고, 그 결정이 **선언 없이** 코드 주석으로만
# 남으면 다음 세션이 회귀로 오인하거나(되살려 놓고 이유를 모름) 반대로 다른 검사가 조용히
# 빠져도 못 잡는다. 그래서 같은 방식으로 못 박는다.
DATA_CONTRACT_CHECKS = {
    "check_artifact_readable": "WIRED — 깨진 아티팩트 ≠ 없는 아티팩트",
    "check_ifrs17_bs": "WIRED — BS 항등식 + 코어 census",
    "check_statutory_reserves": "WIRED — 법정준비금 R-RSV",
    "check_dividend": "WIRED — 배당 census/항등식",
    "check_csm_continuity": "WIRED — CSM 기초≠직전기말 boundary break",
    "check_census": "WIRED — 결측 census·부모자식 완전성·메타룰. 산술의 전제라 절대 빼지 말 것",
    "check_as_of": "WIRED — as-of/stale/effective-list",
    "check_cross_source": "WIRED — 동일개념 tolerance + 다른개념 guard",
    "check_domain_identity": "WIRED — 보완자본 한도 분모=SCR×50% / 소진율",
    "check_gold_overlay":
        "WIRED 2026-08-30 — gold 오버레이가 빌더 소스를 덮은 칸의 census + 마스크 드리프트 RED. "
        "이 검사 이전에는 gold(`data/_gold/user_{csm,pl}_cells.json`)를 빌더 소스와 대조하는 "
        "게이트·테스트가 저장소에 **0건**이었다 — `_apply_*_overrides()` 가 비교 없이 UPSERT 만 "
        "하므로 gold 밑에서 빌더가 회귀해도 화면은 옳고 모든 게이트가 clean 을 찍었다. "
        "빼면 그 false-green 이 그대로 돌아온다. inbox/validation/20260830T0710Z",
    "check_kics_restatement":
        "WIRED 2026-09-01 — K-ICS 소급재작성 축. 공시본의 3열 표(해당/직전/전전분기) 때문에 같은 "
        "(회사,분기) 값이 두 번 인쇄되는데, 발행사가 그걸 다르게 인쇄하면 소급재작성이다. "
        "이 검사 이전에 그 축을 재는 검사기는 저장소에 **0건**이었고 교보생명 2026.1Q 재작성 "
        "10칸이 손으로 발견됐다. 재작성 자체는 YELLOW(발행사의 정당한 행위)이고, RED 은 "
        "**마스터가 원공시본 기준을 벗어날 때**만 낸다 — 한 마스터만 재작성값으로 갈아끼우면 "
        "축이 갈라진다(csm_amort_identity_ledger 의 RESTATEMENT_BASIS 3건이 그 사고다). "
        "탐지기는 scripts/detect_kics_restatement.py, 등재부는 "
        "data/_gold/kics_restatement_ledger.json.",
    "check_master_xlsx":
        "WIRED 2026-09-02 — 루트 마스터 JSON ↔ insurequant_master_tables.xlsx 13개 시트 전수 "
        "셀 단위 대조. 이 검사 이전에는 **마스터와 xlsx 를 대조하는 룰이 저장소에 0건**이었다 "
        "(`PUBLIC_EXPORT_DRIFT` 는 마스터 ↔ public_exports/ 스냅샷만 본다) — xlsx 만 조용히 "
        "뒤처져도 RED 이 안 떴다. 2026-09-02 owner 라이브 QA 로 발견: `자본비율전망` 시트가 "
        "2026.1Q 베이스라인에 멈춰 38개사 2090칸 중 1219칸 stale, 그 조사에서 `K-ICS공시` 도 "
        "stale(33셀 변경 · 121행 누락). owner 는 이 워크북을 직접 받아 검토하고 그 손질이 "
        "gold 리뷰 루프의 입력이 되므로, 틀린 xlsx 는 다음 라운드 데이터까지 오염시킨다. "
        "비교기는 scripts/check_master_xlsx_drift.py (스키마·정규화·행식별키를 "
        "build_master_xlsx/sync_master_xlsx_sheet 에서 import — 재타이핑 금지). "
        "워크북은 읽기 전용으로만 연다(load+save 는 수식 캐시를 날린다). 실측 +11.9초.",
    "check_generic_anomalies":
        "DEWIRED 2026-08-25 — owner 지시로 게이트에서 분리(scripts/scan_generic_anomalies.py). "
        "근거: YELLOW 전용이라 RED 를 한 건도 낸 적이 없어 `blocked` 에 들어간 적이 구조적으로 "
        "없고(=push 를 막은 적이 없다), 게이트 YELLOW 297건 중 224건(75.4%)을 혼자 만들었다. "
        "마지막 데이터 수정 기여는 2026-06-19/20 라운드(교보 원수예실차·BNP 단위오류·코리안리 "
        "중복 43). 커버리지 불변은 변이시험으로 증명 "
        "(scripts/_probes/probe_20260825_coverage_equivalence.py). 되살리려면 run_gate() 의 "
        "주석을 풀고 여기 선언을 WIRED 로 바꿔라.",
}
DEWIRED_PREFIX = "DEWIRED"


def _dc_src() -> str:
    return (ROOT / "scripts" / "validate_data_contract.py").read_text(encoding="utf-8")


def test_every_data_contract_check_is_declared():
    """`validate_data_contract.py` 의 `check_*` 전부가 위 선언에 있어야 한다."""
    found = set(re.findall(r"^def (check_\w+)\(", _dc_src(), re.M))
    undeclared = sorted(found - set(DATA_CONTRACT_CHECKS))
    assert not undeclared, (
        f"미선언 검사 {undeclared} — run_gate() 에 걸었는지 정하고 "
        f"tests/test_push_gate_wiring.py 의 DATA_CONTRACT_CHECKS 에 사유와 함께 넣어라."
    )
    ghost = sorted(set(DATA_CONTRACT_CHECKS) - found)
    assert not ghost, f"선언에만 있고 함수가 없다 {ghost} — 개명/삭제됐다면 선언도 고쳐라"


def _run_gate_body() -> str:
    m = re.search(r"^def run_gate\(.*?\n(.*?)^\S", _dc_src(), re.M | re.S)
    assert m, "validate_data_contract.py 에서 run_gate() 본문을 못 찾았다"
    return m.group(1)


@pytest.mark.parametrize("name", sorted(DATA_CONTRACT_CHECKS))
def test_data_contract_check_wiring_matches_declaration(name):
    """선언(WIRED/DEWIRED)과 `run_gate()` 본문의 실제 호출이 일치해야 한다.

    주석 처리된 호출은 호출이 아니다 — 주석까지 세면 '뺐는데 배선됐다'로 읽힌다."""
    body = _run_gate_body()
    live = [ln for ln in body.splitlines()
            if re.search(rf"^\s*{re.escape(name)}\(res, env\)", ln)]
    declared_dewired = DATA_CONTRACT_CHECKS[name].startswith(DEWIRED_PREFIX)
    if declared_dewired:
        assert not live, (
            f"{name} 은 DEWIRED 로 선언됐는데 run_gate() 가 실제로 부르고 있다. "
            f"되살린 것이라면 선언을 WIRED 로 고쳐라 — 안 고치면 다음에 또 빠져도 아무도 모른다."
        )
    else:
        assert live, (
            f"{name} 이 WIRED 로 선언됐는데 run_gate() 에서 호출을 못 찾았다. "
            f"검사가 조용히 빠졌다 — 되돌리거나 선언을 DEWIRED 로 바꾸고 사유를 적어라."
        )


def test_dewired_check_has_a_reason_and_a_home():
    """뺀 검사는 **사유**와 **손으로 돌리는 경로**가 둘 다 있어야 한다.

    사유 없이 빼는 것이 이 저장소가 두 달을 날린 false-green 의 시작이고, 돌릴 경로가 없으면
    그건 분리가 아니라 삭제다."""
    for name, reason in DATA_CONTRACT_CHECKS.items():
        if not reason.startswith(DEWIRED_PREFIX):
            continue
        assert len(reason) >= 120, f"{name}: DEWIRED 사유가 너무 짧다 — 근거 수치를 적어라"
        m = re.search(r"scripts/(\w+\.py)", reason)
        assert m, f"{name}: 손으로 돌리는 스크립트 경로가 사유에 없다"
        assert (ROOT / "scripts" / m.group(1)).exists(), (
            f"{name}: 사유가 가리키는 scripts/{m.group(1)} 이 없다 — 분리가 아니라 삭제다"
        )


# ---------------------------------------------------------------------------
# 라이브 아티팩트 배선 매트릭스 (2026-08-25 신설) — 불변식 1번을 기계가 강제한다
# ---------------------------------------------------------------------------
# `CLAUDE.md` 불변식 1: **게이트가 검사하는 파일 = 사용자가 보는 파일.**
# 위 두 매니페스트는 "어떤 게이트가 도는가"(파일 단위)와 "게이트 안 어떤 검사가 도는가"
# (check 단위)를 강제한다. 그런데 **그 검사가 어떤 파일을 읽는가**는 아무도 안 봤다.
#
# 2026-08-25 에 런타임 추적으로 전수 대조했더니(`scripts/_probes/
# probe_20260825_trace_validator_reads.py` — 정적 문자열 census 는 동적 경로 조립
# `VIZ / "x.json"` 을 놓쳐 양방향으로 틀린다) `origin/main` 배포 HTML 4종이 fetch 하는
# .json **16개 중 6개를 어떤 검사기도 읽지 않고 있었다.** 게다가 읽고는 있는데 **배포본이
# 아니라 파서 중간산출물**을 읽던 축이 하나 더 있었다(`validate_master_tables` 의 PL 축:
# `data/dart/viz/pl_breakdown_master.json`. 그 결과 배포본에만 있던 1,307셀이 PL 항등식을
# 한 번도 안 거쳤고, 게이트가 찍던 HOLE-PL 24건은 24/24 전부 phantom 이었다).
#
# 그래서 여기서 못 박는다:
#   · 라이브가 fetch 하는 .json 은 **전부** 어느 검사기가 읽는지 선언돼 있어야 한다.
#   · 배포본과 중간산출물이 둘 다 있으면 검사기는 **배포본**을 읽어야 한다.
#   · 화면에 새 파일이 붙으면 선언이 없어서 여기서 막힌다.

# 라이브 HTML 이 fetch 하는 .json -> 그 파일을 **읽는** 검사기(들).
# 값은 사람이 읽는 용도가 아니라 기계 검사 대상이다: 이름이 적힌 스크립트 소스에 그 경로
# 리터럴이 실제로 있어야 통과한다.
LIVE_ARTIFACT_READERS = {
    "CSM_waterfall.json": ["validate_data_contract", "validate_csm_continuity",
                           "validate_master_tables", "validate_live_artifacts"],
    "PL_breakdown.json": ["validate_data_contract", "validate_master_tables",
                          "validate_live_artifacts"],
    "IFRS17_BS.json": ["validate_statutory_reserves"],
    "dividend.json": ["validate_data_contract"],
    "kics_disclosure.json": ["validate_kics_disclosure", "validate_kics_rate_sensitivity"],
    "kics_rate_sensitivity.json": ["validate_kics_rate_sensitivity"],
    "kics_forward_capital.json": ["validate_data_contract"],
    "kics_tier1_utilization.json": ["validate_live_artifacts"],
    "kics_tier2_utilization.json": ["validate_live_artifacts"],
    "NB_CSM_multiple.json": ["validate_live_artifacts"],
    "data/dart/viz/csm_amort_schedule.json": ["validate_live_artifacts"],
    "data/dart/viz/insurance_pl_breakdown.json": ["validate_live_artifacts"],
    "data/dart/viz/csm_waterfall.json": ["validate_csm_waterfall", "validate_nb_csm_multiple"],
    "data/dart/viz/sensitivity_heatmap.json": ["validate_data_contract",
                                               "validate_master_tables"],
    "data/ir/nb_csm_ratio.json": ["validate_nb_csm_multiple"],
    # `/` 로 끝나면 **접두 선언**이다 — 그 폴더 아래 전부를 한 검사기가 덮는다는 뜻.
    # `public_exports/` 는 사용자가 내려받는 12개 스냅샷인데(download-survey.js), 파일 목록이
    # `export_public_sheets.MASTERS` 하나에서 나오고 `validate_live_artifacts` 도 그 목록을
    # import 해서 돈다. 그래서 시트가 늘면 검사도 자동으로 는다 — 여기에 12줄을 손으로 베껴
    # 두면 오히려 13번째 시트가 조용히 무검사로 통과한다(2026-08-30 배선).
    "public_exports/": ["validate_live_artifacts"],
}

# (배포본, 중간산출물) 짝 — 같은 개념이 두 파일로 존재하는 자리. 검사기가 중간산출물 쪽만
# 읽고 있으면 "맞는 산수 · 틀린 소스" 가 통과한다. 값 = 배포본을 반드시 읽어야 하는 검사기.
DEPLOYED_VS_UPSTREAM = {
    "PL_breakdown.json": ("data/dart/viz/pl_breakdown_master.json",
                          ["validate_master_tables", "validate_data_contract"]),
    "NB_CSM_multiple.json": ("data/ir/nb_csm_ratio.json", ["validate_live_artifacts"]),
    "kics_tier1_utilization.json": ("output/tier1_utilization/", ["validate_live_artifacts"]),
    "kics_tier2_utilization.json": ("output/tier2_utilization/", ["validate_live_artifacts"]),
}

_HTML = ["index.html", "K-ICS.html", "IFRS17.html", "공시보고서.html"]


_JSON_LITERAL = re.compile(r"""['"`]([^'"`\s]+?\.json)['"`]""")


def _origin_main_fetches() -> set[str] | None:
    """`origin/main` 의 배포본이 참조하는 .json 경로. 못 읽으면 None(슬림/무리모트).

    **HTML 만 훑으면 안 된다.** 2026-08-30 실측: 배포 HTML 4종이 전부
    `<script src="download-survey.js">` 를 로드하고, 사용자가 실제로 내려받는
    `public_exports/*.json` 12개는 그 JS 안에만 리터럴로 있다. HTML 만 보던 이 헬퍼는 그
    12개를 한 번도 못 봤고, 그래서 "라이브가 fetch 하는 파일은 전부 검사기가 선언돼 있어야
    한다" 는 아래 테스트가 통과하는 채로 **그 12개가 무검사였다**. 이 테스트 자신의 사각이었다
    — 화면이 로드하는 같은 저장소의 JS 까지 따라가서 다시는 같은 식으로 새지 않게 한다.
    """
    import subprocess

    def _show(path: str):
        p = subprocess.run(["git", "show", f"origin/main:{path}"], cwd=str(ROOT),
                           capture_output=True)
        return None if p.returncode != 0 else p.stdout.decode("utf-8", errors="replace")

    out: set[str] = set()
    any_ok = False
    scripts: set[str] = set()
    for h in _HTML:
        body = _show(h)
        if body is None:
            continue
        any_ok = True
        for m in _JSON_LITERAL.finditer(body):
            out.add(m.group(1).lstrip("./"))
        # 같은 저장소의 JS 만 따라간다(CDN 은 우리 아티팩트가 아니다).
        for m in re.finditer(r"""<script[^>]*\bsrc=['"]([^'":]+?\.js)['"]""", body):
            scripts.add(m.group(1).lstrip("./"))
    for js in sorted(scripts):
        body = _show(js)
        if body is None:
            continue
        for m in _JSON_LITERAL.finditer(body):
            out.add(m.group(1).lstrip("./"))
    return out if any_ok else None


def _declared_readers(artifact: str) -> list[str] | None:
    """정확 일치 선언, 없으면 가장 긴 접두(`.../`) 선언을 쓴다."""
    if artifact in LIVE_ARTIFACT_READERS:
        return LIVE_ARTIFACT_READERS[artifact]
    pref = [k for k in LIVE_ARTIFACT_READERS
            if k.endswith("/") and artifact.startswith(k)]
    if not pref:
        return None
    return LIVE_ARTIFACT_READERS[max(pref, key=len)]


def test_every_live_fetched_artifact_has_a_declared_reader():
    """화면이 fetch 하는 .json 은 전부 선언돼 있어야 한다.

    새 파일이 화면에 붙는 순간 여기서 막힌다 — 그때 "이건 누가 검사하나?" 를 한 번은
    생각하게 된다. 그 질문을 아무도 안 해서 6개가 무검사로 방치됐다."""
    fetched = _origin_main_fetches()
    if fetched is None:
        pytest.skip("origin/main 의 배포 HTML 을 읽을 수 없다(슬림 워크트리/무리모트)")
    undeclared = sorted(a for a in fetched if _declared_readers(a) is None)
    assert not undeclared, (
        f"라이브가 fetch 하는데 선언이 없는 아티팩트 {undeclared} — 어떤 검사기가 읽을지 "
        f"정하고 LIVE_ARTIFACT_READERS 에 넣어라. 선언만 하고 안 읽으면 아래 테스트가 막는다."
    )
    ghost = sorted(k for k in LIVE_ARTIFACT_READERS
                   if (k.endswith("/") and not any(a.startswith(k) for a in fetched))
                   or (not k.endswith("/") and k not in fetched))
    assert not ghost, (
        f"선언에만 있고 라이브가 더는 fetch 하지 않는 아티팩트 {ghost} — 화면에서 빠졌다면 "
        f"선언도 지워라(죽은 사본을 계속 검사하게 된다)."
    )


@pytest.mark.parametrize("artifact", sorted(LIVE_ARTIFACT_READERS))
def test_declared_reader_actually_references_the_artifact(artifact):
    """선언한 검사기의 소스에 그 경로가 실제로 있어야 한다 — 선언만 하고 안 읽는 것을 막는다."""
    readers = LIVE_ARTIFACT_READERS[artifact]
    assert readers, f"{artifact}: 읽는 검사기가 하나도 선언돼 있지 않다"
    for name in readers:
        p = ROOT / "scripts" / f"{name}.py"
        if not p.exists():
            pytest.skip(f"slim 워크트리: scripts/{name}.py 없음")
        src = p.read_text(encoding="utf-8")
        # 경로 전체 또는 (동적 조립인 경우) 파일명 조각이 소스에 있어야 한다.
        # 접두 선언(`.../`)은 폴더 이름이 소스에 있으면 된다 — 그 아래 파일명은 목록에서
        # 나오지 소스에 리터럴로 박혀 있지 않다(그게 접두 선언을 쓰는 이유다).
        base = artifact.rstrip("/").rsplit("/", 1)[-1]
        assert artifact in src or f'"{base}"' in src or f"'{base}'" in src, (
            f"{name} 이 {artifact} 를 읽는다고 선언됐는데 소스에서 그 경로를 못 찾았다. "
            f"읽지 않는다면 선언에서 빼고, 다른 검사기가 읽는다면 그 이름을 적어라."
        )


@pytest.mark.parametrize("deployed", sorted(DEPLOYED_VS_UPSTREAM))
def test_gate_reads_the_deployed_artifact_not_the_upstream_copy(deployed):
    """배포본과 중간산출물이 둘 다 있으면 게이트는 **배포본**을 읽어야 한다.

    2026-08-25 이전 `validate_master_tables` 는 PL 축에서 중간산출물을 읽었다. 산수는 맞는데
    소스가 틀린 통과 — 이 저장소의 반복 사고 유형이고 `CLAUDE.md` 불변식 1번 위반이다.
    """
    upstream, must_read = DEPLOYED_VS_UPSTREAM[deployed]
    base = deployed.rsplit("/", 1)[-1]
    for name in must_read:
        p = ROOT / "scripts" / f"{name}.py"
        if not p.exists():
            pytest.skip(f"slim 워크트리: scripts/{name}.py 없음")
        src = p.read_text(encoding="utf-8")
        assert deployed in src or f'"{base}"' in src or f"'{base}'" in src, (
            f"{name} 이 배포본 {deployed} 를 읽지 않는다. 상류 사본({upstream})만 읽고 있다면 "
            f"그건 사용자가 보는 파일을 검사하지 않는 것이다 — 불변식 1번 위반."
        )
        # 상류를 **읽기 경로로** 쓰고 있지 않은지: 주석/참고 상수는 허용하되 실제 로드는 금지.
        for ln in src.splitlines():
            s = ln.strip()
            if upstream not in s or s.startswith("#"):
                continue
            assert not re.search(r"(load_long|json\.loads?|read_text|open)\s*\(", s), (
                f"{name} 이 상류 사본을 직접 로드하는 줄이 남아 있다: {s[:120]}\n"
                f"배포본({deployed})을 읽어야 한다."
            )


# ---------------------------------------------------------------------------
# owner 상시 규칙: **화면에 있는 그래프는 전부 마스터 테이블에 담는다.**
#
# 2026-08-30 실측: 이 규칙이 문서에만 있었고 검사하는 것이 없어서, `IFRS17.html`
# "7) 민감도(ΔCSM)" 패널이 **마스터 시트 없이** 오래 방치돼 있었다. 하필 마스터에
# `금리민감도` 라는 비슷한 이름의 시트(K-ICS 지급여력비율의 금리 ±bp 민감도)가 있어서
# 같은 것으로 오인되기 딱 좋았다 — 사람이 눈으로 보는 방식으로는 이 종류를 못 잡는다.
#
# 그래서 기계로 건다. 화면이 fetch 하는 .json 은 전부
#   (a) 그 자체가 마스터 JSON 이거나
#   (b) 아래 `PANEL_DERIVED_FROM` 이 어느 마스터의 파생인지 선언하고 있어야 한다.
# 새 패널이 화면에 붙는 순간 여기서 막히고, 그때 "이 그래프는 어느 시트에 담기나?" 를
# 한 번은 답해야 한다. `public_exports/` 는 마스터의 공개 사본이라 이 검사에서 뺀다.
#
# `bs_snapshot.json` · `csm_waterfall_history.json` 은 여기 없다 — 패널 빌더가 만들지만
# **배포 HTML/JS 가 더는 fetch 하지 않는다**(2026-08-30 실측, 아래 ghost 검사로 확인).
# 화면에 없으니 이 규칙의 대상이 아니다. 다시 붙으면 ghost 검사가 아니라 위 gap 검사에
# 걸리므로 그때 선언하면 된다.
PANEL_DERIVED_FROM = {
    "data/dart/viz/csm_amort_schedule.json":     "CSM_amortization.json",
    "data/dart/viz/csm_waterfall.json":          "CSM_waterfall.json",
    "data/dart/viz/insurance_pl_breakdown.json": "PL_breakdown.json",
    "data/dart/viz/sensitivity_heatmap.json":    "CSM_sensitivity.json",
    "data/ir/nb_csm_ratio.json":                 "NB_CSM_multiple.json",
}


def test_every_live_fetched_artifact_lands_in_a_master_sheet():
    """화면이 그리는 데이터는 전부 마스터 xlsx 의 어느 시트에 담겨야 한다(owner 상시 규칙)."""
    import sys
    fetched = _origin_main_fetches()
    if fetched is None:
        pytest.skip("origin/main 의 배포본을 읽을 수 없다(슬림 워크트리/무리모트)")
    if not (ROOT / "scripts" / "build_master_xlsx.py").exists():
        pytest.skip("slim 워크트리: scripts/build_master_xlsx.py 없음")
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_master_xlsx import MASTERS
    sheet_of = {j: s for j, s, *_ in MASTERS}

    gaps = []
    for f in sorted(fetched):
        base = f.lstrip("./")
        if base.startswith("public_exports/"):
            continue          # 마스터의 공개 사본 — 원본이 이미 검사된다
        master = base if base in sheet_of else PANEL_DERIVED_FROM.get(base)
        if not master or master not in sheet_of:
            gaps.append(base)
    assert not gaps, (
        f"화면이 그리는데 마스터 시트가 없는 데이터 {gaps} — owner 상시 규칙 위반. "
        f"그 데이터를 담을 마스터를 만들어 `build_master_xlsx.MASTERS` 에 등재하고, "
        f"패널 JSON 이면 PANEL_DERIVED_FROM 에 어느 마스터의 파생인지 선언해라."
    )

    # 선언만 하고 실제로는 화면이 더는 안 읽는 항목도 막는다(죽은 선언 방지).
    ghost = sorted(k for k in PANEL_DERIVED_FROM
                   if k not in {f.lstrip("./") for f in fetched})
    assert not ghost, (
        f"PANEL_DERIVED_FROM 에만 있고 화면이 더는 fetch 하지 않는 것 {ghost} — 선언을 지워라."
    )
