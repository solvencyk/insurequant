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
    "validate_csm_waterfall":
        "CSM 워터폴 항등식 + 단계 커버리지. 2026-08-21 에 18건 실패 상태로 발견됐고(호출처 0 이라 "
        "아무도 몰랐다) 같은 날 exit 0 까지 닫혀 WIRED 로 옮겼다. 구조적 제외 6건(IFRS17 시행 전 "
        "FY2022 필링)은 조용한 skip 이 아니라 매 실행 이름과 함께 인쇄된다.",
}

# push 를 막지 않는 것들. **사유 없이 여기 넣지 말 것** — 그게 이 테스트를 무력화하는 방법이다.
NOT_A_PUSH_GATE = {
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


def _origin_main_fetches() -> set[str] | None:
    """`origin/main` 의 배포 HTML 이 참조하는 .json 경로. 못 읽으면 None(슬림/무리모트)."""
    import subprocess
    out: set[str] = set()
    any_ok = False
    for h in _HTML:
        p = subprocess.run(["git", "show", f"origin/main:{h}"], cwd=str(ROOT),
                           capture_output=True)
        if p.returncode != 0:
            continue
        any_ok = True
        src = p.stdout.decode("utf-8", errors="replace")
        for m in re.finditer(r"""['"`]([^'"`\s]+?\.json)['"`]""", src):
            out.add(m.group(1).lstrip("./"))
    return out if any_ok else None


def test_every_live_fetched_artifact_has_a_declared_reader():
    """화면이 fetch 하는 .json 은 전부 선언돼 있어야 한다.

    새 파일이 화면에 붙는 순간 여기서 막힌다 — 그때 "이건 누가 검사하나?" 를 한 번은
    생각하게 된다. 그 질문을 아무도 안 해서 6개가 무검사로 방치됐다."""
    fetched = _origin_main_fetches()
    if fetched is None:
        pytest.skip("origin/main 의 배포 HTML 을 읽을 수 없다(슬림 워크트리/무리모트)")
    undeclared = sorted(fetched - set(LIVE_ARTIFACT_READERS))
    assert not undeclared, (
        f"라이브가 fetch 하는데 선언이 없는 아티팩트 {undeclared} — 어떤 검사기가 읽을지 "
        f"정하고 LIVE_ARTIFACT_READERS 에 넣어라. 선언만 하고 안 읽으면 아래 테스트가 막는다."
    )
    ghost = sorted(set(LIVE_ARTIFACT_READERS) - fetched)
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
        # 경로 전체 또는 (동적 조립인 경우) 파일명 조각이 소스에 있어야 한다
        base = artifact.rsplit("/", 1)[-1]
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
