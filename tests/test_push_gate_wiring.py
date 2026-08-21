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
}

# push 를 막지 않는 것들. **사유 없이 여기 넣지 말 것** — 그게 이 테스트를 무력화하는 방법이다.
NOT_A_PUSH_GATE = {
    "validate_csm_waterfall":
        "2026-08-21 현재 exit 1 (`balance_incomplete:assumption`). 데이터가 실제로 미완이라 "
        "지금 배선하면 모든 push 를 막는다. ifrs17 레인이 닫으면 WIRED 로 옮긴다 "
        "(inbox 티켓 20260821T1900Z). **통과하기 시작하면 이 사유는 거짓이 된다** — "
        "test_unwired_gates_still_fail 이 그때 막는다.",
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
    rc = subprocess.run([sys.executable, str(script)], cwd=str(ROOT),
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace").returncode
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
