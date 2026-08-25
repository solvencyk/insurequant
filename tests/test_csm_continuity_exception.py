# -*- coding: utf-8 -*-
"""`_CSM_CONTINUITY_EXCEPTIONS` (CSM FY 경계 면제) 의 **변이시험**.

## 왜 이 파일이 있나

`check_csm_continuity` 의 docstring 은 "**break = 무조건 RED, 면제 없음**" 이라고 못박는다.
그 원칙이 생긴 이유가 postmortem 에 남아 있다 — "소급재작성이라 주장했는데 오파싱이었던
2026.1Q 5사". 2026-08-25 에 그 원칙에 **첫 예외**가 들어왔다(하나생명 2024.4Q, owner 유지 승인).

예외가 들어오는 순간 그 축은 이 저장소에서 가장 위험한 코드가 된다. 그래서 여기 면제는
'끄기' 가 아니라 **잔차 박제**여야 하고, "박제를 흔들면 RED 가 돌아온다" 를 시험으로
증명하지 않으면 blanket skip 과 구분되지 않는다 —
`tests/test_tier2_issuer_inconsistent_exemption.py` 가 tier2 면제에 요구하는 것과 같은 잣대다.

**등재 직후의 형태는 이 잣대에 미달이었다**(validation iter4 심사 실측):
  · 기초를 +1,000억 밀어 Δ 를 +73 -> +1,073 으로 바꿔도 여전히 YELLOW.
  · 기초를 결측으로 만들면 완전 침묵(RED=0 YELLOW=0).
  · 경계가 닫혀 면제가 무용해져도 아무 말 없음.
스코프(다른 회사·다른 분기로 안 새는 것)만 처음부터 맞았다. 이 파일은 그 세 구멍이
다시 열리지 않게 못 박는다.

합성이 아니라 **라이브 마스터**를 쓴다 — 등재된 그 버킷이 실제로 재검산되는지가 요점이고,
합성으로는 "코드가 돈다" 까지만 보인다.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_data_contract as gate  # noqa: E402

KEY = ("하나생명보험", "2024.4Q")


class _FakeEnv:
    def __init__(self, wf):
        self.wf = wf


@pytest.fixture(scope="module")
def wf():
    """env.wf 와 같은 모양: {(회사, 분기): {항목명(공백제거): 값}}."""
    recs = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
    recs = recs["records"] if isinstance(recs, dict) else recs
    out: dict = {}
    for r in recs:
        co, q = r.get("원수사명"), r.get("공시분기")
        if co is None or q is None:
            continue
        out.setdefault((co, q), {})[str(r.get("항목명") or "").replace(" ", "")] = r.get("값")
    return out


def _run(wf_map):
    res = gate.GateResult()
    gate.check_csm_continuity(res, _FakeEnv(wf_map))
    return res.findings


def _rules(finds, co=None, q=None):
    return {f.rule for f in finds
            if (co is None or f.company == co) and (q is None or f.quarter == q)}


# ---------------------------------------------------------------------------
# 0. 평시 — 등재분이 실제로 재검산을 통과하는가
# ---------------------------------------------------------------------------
def test_the_live_master_matches_the_pin(wf):
    """평시엔 RED 0. 하나라도 RED 면 등재의 전제가 이미 깨진 것이다."""
    finds = _run(wf)
    red = [f for f in finds if f.severity == "RED"]
    assert red == [], f"continuity 축에 RED 가 있다: {[(f.company, f.quarter, f.rule) for f in red]}"
    assert _rules(finds, *KEY) == {"CSM_CONTINUITY_FY_BOUNDARY_EXCEPTED"}, (
        "등재 버킷이 '박제 재검산 통과' 상태가 아니다")


def test_the_registry_stays_at_one_bucket():
    """조용히 한 버킷이 더 들어오면 여기서 막힌다. 늘릴 땐 이 숫자와 근거를 같이 고쳐라 —
    이 축의 기본값은 '면제 없음' 이고, 예외는 owner 승인 + raw 확정을 거친 것만이다."""
    assert len(gate._CSM_CONTINUITY_EXCEPTIONS) == 1, (
        f"continuity 면제가 1 -> {len(gate._CSM_CONTINUITY_EXCEPTIONS)} 로 늘었다. "
        f"현재 키: {sorted(gate._CSM_CONTINUITY_EXCEPTIONS)}")
    assert KEY in gate._CSM_CONTINUITY_EXCEPTIONS


def test_every_registered_bucket_pins_cells_a_gap_and_a_citation():
    """세 겹 중 하나라도 비면 그 면제는 다시 산문이 된다 — 구조로 강제한다."""
    for key, spec in gate._CSM_CONTINUITY_EXCEPTIONS.items():
        assert isinstance(spec, dict), f"{key}: 산문 문자열 등재는 금지(박제가 없다)"
        pins = spec.get("pins") or {}
        assert pins.get("prev_close") is not None and pins.get("opening") is not None, \
            f"{key}: 경계 양끝 셀 박제가 없다 — 데이터가 움직여도 모른다"
        assert spec.get("expected_gap") is not None, f"{key}: 잔차 박제가 없다"
        assert spec.get("tol", 1e9) <= 0.2, f"{key}: 잔차 허용오차가 느슨하다 = blanket skip"
        v = spec.get("verify") or {}
        assert v.get("file") and v.get("present_markers"), \
            f"{key}: 기계검증 가능한 인용(file + present_markers)이 없다"
        assert spec.get("why"), f"{key}: 사람이 읽을 사유가 없다"


# ---------------------------------------------------------------------------
# 1. 겹 ① — 데이터를 흔들면 RED 가 돌아온다
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("item,delta", [("기초CSM", 1000.0), ("기초CSM", 0.5)])
def test_input_drift_revives_the_red(wf, item, delta):
    """박제한 경계 셀을 흔들면 `CSM_CONTINUITY_EXCEPTION_DRIFT` + 원래 RED 가 돌아온다.

    큰 폭(+1,000)과 작은 폭(+0.5) 둘 다 건다 — 작은 폭을 놓치면 그 순간 '대충 비슷하면 통과'다.
    """
    m = copy.deepcopy(wf)
    m[KEY][item] += delta
    r = _rules(_run(m), *KEY)
    assert "CSM_CONTINUITY_EXCEPTION_DRIFT" in r, f"{item} {delta:+} 흔들었는데 조용하다: {r}"
    assert "CSM_CONTINUITY_FY_BOUNDARY" in r, "전제가 깨졌는데 원래 RED 가 안 돌아왔다"
    assert "CSM_CONTINUITY_FY_BOUNDARY_EXCEPTED" not in r, "깨진 버킷이 여전히 면제되고 있다"


def test_the_far_end_of_the_boundary_is_pinned_too(wf):
    """경계는 두 셀로 이뤄진다. 직전 FY 기말만 흔들어도 면제가 깨져야 한다 —
    한쪽만 박으면 반대쪽이 사각이 된다."""
    m = copy.deepcopy(wf)
    m[("하나생명보험", "2023.4Q")]["기말CSM"] += 40.0
    r = _rules(_run(m), *KEY)
    assert "CSM_CONTINUITY_EXCEPTION_DRIFT" in r, f"직전기말을 흔들었는데 조용하다: {r}"


def test_a_missing_input_is_red_not_skip(wf):
    """**결측은 SKIP 이 아니라 RED 다.** 종전 코드는 `if ... is None: continue` 로 완전히
    침묵했다 — 등재 버킷이면 박제를 확인할 수 없으니 면제 자체가 성립하지 않는다."""
    for item in ("기초CSM",):
        m = copy.deepcopy(wf)
        m[KEY][item] = None
        r = _rules(_run(m), *KEY)
        assert "CSM_CONTINUITY_INPUT_MISSING" in r, f"{item} 결측인데 조용하다: {r}"
        assert "CSM_CONTINUITY_FY_BOUNDARY_EXCEPTED" not in r


def test_a_missing_input_on_an_unregistered_bucket_is_also_red(wf):
    """면제와 무관하게 결측 SKIP 자체를 막는다. 직전 FY 4Q 행이 **있는데** 경계 양끝 중
    하나가 비면 그 경계는 '깨끗한' 게 아니라 검산되지 않은 것이다."""
    victim = next(k for k in wf
                  if k[0] != KEY[0] and k[1] == "2024.4Q"
                  and (k[0], "2023.4Q") in wf
                  and wf[k].get("기초CSM") is not None)
    m = copy.deepcopy(wf)
    m[victim]["기초CSM"] = None
    assert "CSM_CONTINUITY_INPUT_MISSING" in _rules(_run(m), *victim)


# ---------------------------------------------------------------------------
# 2. 겹 ② — 잔차 박제
# ---------------------------------------------------------------------------
def test_the_pinned_gap_is_the_delta_the_issuer_actually_disclosed():
    """박제한 잔차가 발행사 명문 공시(전기초 재작성 +7,292,841천원 = +72.93억)와 같은 크기인지.

    마스터가 소수 1자리라 관측 잔차는 +73.0 이다. 이 숫자가 슬그머니 바뀌면 등재 근거와
    실제 면제 폭이 갈라진다."""
    spec = gate._CSM_CONTINUITY_EXCEPTIONS[KEY]
    assert abs(spec["expected_gap"] - 73.0) < 0.05
    assert abs(spec["pins"]["opening"] - spec["pins"]["prev_close"]
               - spec["expected_gap"]) < 0.051, "박제한 두 셀의 차이가 박제한 잔차와 다르다"


# ---------------------------------------------------------------------------
# 3. 겹 ③ — 인용
# ---------------------------------------------------------------------------
def _cited_file() -> Path:
    return ROOT / gate._CSM_CONTINUITY_EXCEPTIONS[KEY]["verify"]["file"]


@pytest.mark.skipif(not _cited_file().exists(),
                    reason="raw 는 .gitignore 대상 — 없는 클론에서는 게이트가 "
                           "CSM_CONTINUITY_EXCEPTION_UNCHECKABLE YELLOW 로 스스로 말한다")
def test_the_citation_actually_contains_the_numbers_it_claims(wf):
    """등재 근거가 **기계가 열어볼 수 있는 인용**인지. 산문이면 아무도 반박할 수 없다."""
    assert "CSM_CONTINUITY_EXCEPTION_UNCHECKABLE" not in _rules(_run(wf), *KEY)
    txt = _cited_file().read_text(encoding="utf-8", errors="replace")
    v = gate._CSM_CONTINUITY_EXCEPTIONS[KEY]["verify"]
    for mk in v["present_markers"]:
        assert mk in txt, f"인용한 raw 에 {mk} 가 없다 — 등재 근거가 반증됐다"
    for mk in v.get("absent_markers") or []:
        assert mk not in txt, (
            f"없어야 할 {mk}(재작성 전 값)가 인용 파일에 있다 — '단일 표에서 왔다' 전제가 깨진다")


@pytest.mark.skipif(not _cited_file().exists(), reason="raw 없는 클론")
def test_a_citation_that_does_not_support_the_claim_is_red(wf):
    """인용이 근거를 뒷받침하지 않으면 RED. 배선을 실제로 흔들어 확인한다."""
    spec = gate._CSM_CONTINUITY_EXCEPTIONS[KEY]
    broken = copy.deepcopy(spec)
    broken["verify"]["present_markers"] = list(broken["verify"]["present_markers"]) + ["999,999,999"]
    gate._CSM_CONTINUITY_EXCEPTIONS[KEY] = broken
    try:
        r = _rules(_run(wf), *KEY)
    finally:
        gate._CSM_CONTINUITY_EXCEPTIONS[KEY] = spec
    assert "CSM_CONTINUITY_EXCEPTION_DRIFT" in r and "CSM_CONTINUITY_FY_BOUNDARY" in r


def test_a_missing_citation_file_is_reported_not_silently_accepted(wf):
    """raw 가 없는 클론은 정상이지만, 그 실행이 근거를 **확인하지 못했다**는 사실은 말해야 한다.
    조용히 통과하면 '확인했다' 와 구분되지 않는다."""
    spec = gate._CSM_CONTINUITY_EXCEPTIONS[KEY]
    broken = copy.deepcopy(spec)
    broken["verify"]["file"] = "data/dart/__no_such_dir__/nope.xml"
    gate._CSM_CONTINUITY_EXCEPTIONS[KEY] = broken
    try:
        finds = _run(wf)
    finally:
        gate._CSM_CONTINUITY_EXCEPTIONS[KEY] = spec
    r = _rules(finds, *KEY)
    assert "CSM_CONTINUITY_EXCEPTION_UNCHECKABLE" in r
    assert not [f for f in finds if f.severity == "RED"], \
        "raw 없는 클론에서 push 를 막으면 안 된다(YELLOW 로 말하는 것이 맞다)"


def test_a_prose_only_registration_cannot_pass(wf):
    """박제 없이 산문만 넣는 **후퇴 경로**를 막는다 — 이 면제가 처음 들어온 형태가 그것이었다."""
    spec = gate._CSM_CONTINUITY_EXCEPTIONS[KEY]
    gate._CSM_CONTINUITY_EXCEPTIONS[KEY] = {"why": "raw 로 확인했다(라고 주장)"}
    try:
        r = _rules(_run(wf), *KEY)
    finally:
        gate._CSM_CONTINUITY_EXCEPTIONS[KEY] = spec
    assert "CSM_CONTINUITY_EXCEPTION_DRIFT" in r and "CSM_CONTINUITY_FY_BOUNDARY" in r


# ---------------------------------------------------------------------------
# 4. 스코프 — 면제가 넓어지지 않는다
# ---------------------------------------------------------------------------
def test_the_exemption_does_not_spread_to_other_quarters_of_the_same_company(wf):
    m = copy.deepcopy(wf)
    m[("하나생명보험", "2025.4Q")]["기초CSM"] += 500.0
    assert "CSM_CONTINUITY_FY_BOUNDARY" in _rules(_run(m), "하나생명보험", "2025.4Q")


def test_the_exemption_does_not_spread_to_other_companies(wf):
    victim = next(k for k in wf
                  if k[0] != KEY[0] and k[1] == "2024.4Q" and (k[0], "2023.4Q") in wf
                  and wf[k].get("기초CSM") is not None
                  and wf[(k[0], "2023.4Q")].get("기말CSM") is not None)
    m = copy.deepcopy(wf)
    m[victim]["기초CSM"] += 5000.0
    assert "CSM_CONTINUITY_FY_BOUNDARY" in _rules(_run(m), *victim)


# ---------------------------------------------------------------------------
# 5. 무용해진 면제를 조용히 두지 않는다
# ---------------------------------------------------------------------------
def test_an_exemption_that_stopped_firing_is_reported(wf):
    """경계가 닫히면 `CSM_CONTINUITY_EXCEPTION_INERT` 로 인쇄된다. 죽은 핀을 남기면 다음
    세션이 '그 축은 면제됐다' 로 오독한다 — tier2 면제의 INERT 와 같은 관행이다."""
    m = copy.deepcopy(wf)
    m[KEY]["기초CSM"] = m[("하나생명보험", "2023.4Q")]["기말CSM"]
    r = _rules(_run(m), *KEY)
    assert "CSM_CONTINUITY_EXCEPTION_INERT" in r
    assert "CSM_CONTINUITY_FY_BOUNDARY" not in r


def test_a_vanished_bucket_is_reported_too(wf):
    """등재 버킷이 마스터에서 통째로 사라져도 조용하면 안 된다."""
    m = {k: v for k, v in wf.items() if k != KEY}
    assert "CSM_CONTINUITY_EXCEPTION_INERT" in _rules(_run(m), *KEY)


# ---------------------------------------------------------------------------
# 6. 면제는 '끄기' 가 아니다
# ---------------------------------------------------------------------------
def test_the_exempted_boundary_never_disappears_from_the_findings(wf):
    """면제돼도 finding 은 남는다 — 조용히 사라지면 다음에 진짜 파싱사고가 와도 같은 자리에서
    안 보인다."""
    finds = _run(wf)
    hit = [f for f in finds if (f.company, f.quarter) == KEY]
    assert hit, "면제된 경계가 findings 에서 통째로 사라졌다"
    assert hit[0].severity == "YELLOW"
    assert "Δ+73" in hit[0].message, "면제 메시지가 실제 잔차를 인쇄하지 않는다"
