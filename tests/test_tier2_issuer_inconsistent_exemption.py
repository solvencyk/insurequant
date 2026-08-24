# -*- coding: utf-8 -*-
"""`_TIER2_ISSUER_INCONSISTENT` (tier2/다리 발행사 자기모순 면제) 의 **변이시험**.

## 왜 이 파일이 있나

면제는 이 저장소에서 가장 위험한 코드다. 한 번 등재되면 그 셀은 아무도 안 본다 — 그게
`docs/postmortems/` 가 반복해서 기록한 실패모드다. 그래서 이 저장소의 면제는 '끄기' 가
아니라 **잔차 박제**이고, "박제값을 흔들면 RED 가 돌아온다" 를 시험으로 증명하지 않으면
그냥 skip 과 구분되지 않는다.

이 면제는 **두 겹**이라 두 겹 다 흔든다:

  ① `cells`   — raw 로 판독한 마스터 값. 데이터가 움직이면 `TIER2_EXEMPTION_INPUT_DRIFT`,
                결측이면 `TIER2_EXEMPTION_INPUT_MISSING`.
  ② `findings`— 그 축이 실제로 내는 RED 의 잔차·사유. 움직이면 `TIER2_EXEMPTION_RESIDUAL_DRIFT`,
                RED 가 사라지면 `TIER2_EXEMPTION_INERT` (review).

①만 있으면 룰이 바뀐 것을 못 보고, ②만 있으면 데이터가 바뀐 것을 못 본다. 둘 다 건다.

## 합성이 아니라 **라이브 마스터**를 쓴다

면제는 실제 등재분에 대해서만 의미가 있다. 합성 버킷으로 시험하면 "코드가 돈다" 만 보이고
"등재된 13버킷이 실제로 재검산된다" 는 안 보인다 — 그 구분이 정확히 false-green 의 자리다.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
MASTER = ROOT / "kics_disclosure.json"

import validate_kics_disclosure as gate  # noqa: E402

from solvency.validation.kics_json_rules import (  # noqa: E402
    KEY_CODE,
    KEY_ITEM,
    KEY_QUARTER,
    KEY_VALUE,
    KEY_VALUE_POST,
    run_validation,
)

COL_KEY = {"값": KEY_VALUE, "값_적용후": KEY_VALUE_POST}


@pytest.fixture(scope="module")
def records():
    raw = json.loads(MASTER.read_text(encoding="utf-8"))
    return raw["records"] if isinstance(raw, dict) else raw


@pytest.fixture(scope="module")
def findings(records):
    rep = run_validation(records,
                         source_has_breakdown=gate._scan_breakdown_presence(records),
                         tfi_applicability=gate._load_tfi_applicability())
    return rep.get("findings", [])


def _run(recs, finds):
    return gate._tier2_issuer_inconsistent(recs, finds)


def _mutate_cell(records, code, quarter, item, col, new):
    """마스터 사본에서 한 칸만 바꾼다. `new=None` 이면 결측으로 만든다."""
    out = copy.deepcopy(records)
    key = COL_KEY[col]
    for r in out:
        if r.get(KEY_CODE) != code or r.get(KEY_QUARTER) != quarter:
            continue
        try:
            if int(r.get(KEY_ITEM)) != item:
                continue
        except (TypeError, ValueError):
            continue
        if new is None:
            r.pop(key, None)
        else:
            r[key] = new
        return out
    raise AssertionError(f"셀을 못 찾았다: {code} {quarter} item{item} [{col}]")


# ---------------------------------------------------------------------------
# 0. 등재 자체가 의미를 갖는가 — 현행 마스터에서 전부 일치해야 한다
# ---------------------------------------------------------------------------
def test_every_registered_bucket_matches_its_pin_on_the_live_master(records, findings):
    """평시엔 조용해야 한다. 하나라도 RED 면 등재의 전제가 이미 깨진 것이다."""
    accepted, red, review, detail = _run(records, findings)
    assert red == [], f"면제 전제가 깨졌다: {red}"
    assert review == [], f"무용해진 면제가 있다: {review}"
    n_pins = sum(len(s["findings"]) for s in gate._TIER2_ISSUER_INCONSISTENT.values())
    assert len(accepted) == n_pins, "박제한 축 수와 면제된 finding 수가 다르다"


def test_the_exemption_is_narrow_and_does_not_touch_the_held_buckets(records, findings):
    """면제가 **넓어지지 않았다**를 기계로 못 박는다. 이 버킷들은 RED 로 남아야 한다.

    2026-08-24 (2차 owner 위임): 이 목록에서 **네 버킷이 빠졌다** — 예별손해 2025.1Q ·
    BNP카디프 2024.3Q · 롯데손해 2023.1Q(전부 raw 확증은 이미 끝났고 1차 위임 목록 밖이라
    보류돼 있던 것들) · 한화생명 2025.2Q(owner 가 raw 를 직접 열어 보고 오차 용인 결정,
    원장 status=VERIFIED_BY_OWNER). **남은 보류 두 건은 성격이 정반대다:**

      · NH농협 2024.3Q — **미조사**. 다리 잔차 −522 의 원인을 아직 안 봤다. 조사 전 등재는
        근거가 아니라 추측이다.
      · 삼성화재 2025.3Q — **고칠 것**이라 면제 대상이 아니다. owner 2026-08-24 결정으로
        parser 가 값을 정정한다(`inbox/parser/20260824T0400Z` §G). 여기 등재하면
        고쳐진 뒤에도 죽은 핀이 남아 "그 축은 면제됐다" 로 오독된다.

    **두 버킷의 기대가 다르다는 점이 중요하다.** 둘 다 '레지스트리에 절대 없어야 한다' 는
    같지만, RED 의 운명은 반대다:
      · NH농협 2024.3Q 는 **RED 가 살아 있어야 한다** — 모르는 것을 사면하지 않았다는 증거다.
        여기서 RED 가 조용히 사라지면 그건 조사가 끝나서가 아니라 무언가 새어 나간 것이다.
      · 삼성화재 2025.3Q 는 **RED 가 사라지는 것이 성공**이다(정정되면 축이 저절로 닫힌다).
        그래서 RED 존속을 요구하면 안 된다 — 요구하면 고친 사람이 이 시험 때문에 막힌다.
    두 기대를 한 집합으로 뭉치면 그 구분이 사라진다(2026-08-24 실제로 그렇게 썼다가 parser 가
    삼성화재를 고친 순간 이 시험이 잘못 실패했다)."""
    # 2026-08-24 (3차): **NH농협 2024.3Q 가 보류 목록에서 나갔다.** 위 docstring 이 "미조사"
    # 라고 적어 둔 그 전제가 조사로 바뀌었다 — orchestrator 가 raw
    # `FY2024_Q3/raw/KR0032_NH농협손해보험_amended.pdf` p12 를 직접 열어, 발행사가 **자기 각주
    # 주2) 공식과 그 공식을 만족하지 않는 숫자를 같은 페이지에 함께 인쇄**하는 것을 확인했다
    # (순자산 23,478 − 불인정 0 − 재분류 8,867 = 14,611 vs 인쇄된 기본자본 14,089, 차 522).
    # 다리가 닫히려면 한도초과 = −522 여야 하는데 '초과액'이 음수일 수 없고 불인정항목이 0 이라
    # 들어갈 자리가 없다. 원장에 `present_markers` 7개로 기계검증 가능하게 등재했다.
    # **보류가 풀린 이유는 "owner 가 위임했으니까"가 아니라 "원문을 봤으니까"다.**
    #
    # 남은 보류는 삼성화재 하나다 — 그건 고칠 것이라 면제 대상이 아니다(위 docstring 참조).
    never_exempt = {("KR0008", "2025.3Q")}
    must_stay_red: set = set()
    registered = set(gate._TIER2_ISSUER_INCONSISTENT)
    assert never_exempt & registered == set(), "보류 버킷이 면제로 새어 들어갔다"

    # 보류 목록이 1개로 줄면서 이 시험이 약해졌다. 그 자리를 **레지스트리 크기 고정**으로 메운다 —
    # 조용히 한 버킷이 더 들어오면 여기서 막힌다. 늘릴 땐 이 숫자와 근거를 같이 고쳐야 한다.
    assert len(registered) == 19, (
        f"면제 레지스트리 크기가 19 -> {len(registered)} 로 바뀌었다. 등재를 늘렸다면 "
        f"원장(`data/_gold/kics_exemption_provenance.json`)의 근거와 이 숫자를 같이 고쳐라. "
        f"현재 키: {sorted(registered)}"
    )

    accepted, _red, _review, _detail = _run(records, findings)
    exempted = {(f.get(KEY_CODE), f.get(KEY_QUARTER)) for f in accepted}
    assert never_exempt & exempted == set()
    still_red = {(f.get(KEY_CODE), f.get(KEY_QUARTER))
                 for f in findings if f.get("status") == "RED"}
    assert must_stay_red <= still_red, f"미조사 버킷의 RED 가 사라졌다: {must_stay_red - still_red}"


# ---------------------------------------------------------------------------
# 1. 겹 ① — 데이터를 흔들면 RED 가 돌아온다
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("code,quarter,item,col", [
    ("KR1000", "2023.4Q", 47, "값"),     # 두 표가 다른 값 계열
    ("KR1000", "2024.4Q", 13, "값"),     # 다리 계열
    ("KR0003", "2026.1Q", 48, "값"),     # 전기 표 재게시 계열
    ("KR0075", "2024.4Q", 49, "값"),     # 표가 자기 안에서 안 닫힘 계열
    ("KR0087", "2025.2Q", 12, "값"),     # 각주 위반 계열
    # iter-7 신규. **이게 NH농협 면제의 해제조건 그 자체다** — orchestrator 발주가
    # "발행사가 표 구성을 바꾸거나 item54 가 변하면 자동 RED" 를 요구했고, item54 를
    # 박제 셀에 넣었으므로 흔들면 TIER2_EXEMPTION_INPUT_DRIFT 가 떠야 한다.
    ("KR0032", "2025.4Q", 54, "값"),     # 발행사 표 구성 관행 계열(후순위채무 메모행)
    # ---- 2026-08-24 2차 owner 위임 등재분 4버킷 -------------------------------
    ("KR0003", "2023.1Q", 51, "값"),     # 두 표가 다른 값 + TFI 적용전만 안 닫힘
    ("KR0075", "2024.3Q", 47, "값"),     # 표가 자기 안에서 안 닫힘(메모행 둘 다 대시)
    ("KR0004", "2025.1Q", 48, "값"),     # 합계는 같은데 tier 분할만 다름
    # 한화생명은 **다리 입력 4칸 전부**를 흔든다. orchestrator 발주가 "item2·4·12·13 중
    # 하나라도 바뀌면 자동 RED" 를 요구했고, 인과가 미규명인 면제라 해제조건이 유일한 안전장치다.
    ("KR0068", "2025.2Q", 2, "값"),
    ("KR0068", "2025.2Q", 4, "값"),
    ("KR0068", "2025.2Q", 12, "값"),
    ("KR0068", "2025.2Q", 13, "값"),
])
def test_input_drift_revives_the_red(records, findings, code, quarter, item, col):
    """박제한 셀을 한 칸만 흔들면 `TIER2_EXEMPTION_INPUT_DRIFT` RED 가 뜬다.

    허용오차(0.01)보다 확실히 큰 폭으로 민다 — 느슨하게 잡으면 그 순간 blanket skip 이다."""
    pin = gate._TIER2_ISSUER_INCONSISTENT[(code, quarter)]["cells"][item][col]
    mutated = _mutate_cell(records, code, quarter, item, col, pin + 5.0)
    _acc, red, _rev, _det = _run(mutated, findings)
    kinds = {r["rule"] for r in red}
    assert "TIER2_EXEMPTION_INPUT_DRIFT" in kinds, f"{code} {quarter} item{item} 흔들었는데 조용하다"
    hit = [r for r in red if r["rule"] == "TIER2_EXEMPTION_INPUT_DRIFT"]
    assert any(r["code"] == code and r["quarter"] == quarter and r["item"] == item for r in hit)


def test_a_drift_smaller_than_the_pin_tolerance_is_still_caught_when_it_matters(records, findings):
    """박제 허용오차가 '박제' 로 남아 있는지 — tol 을 살짝 넘기면 바로 RED 다."""
    code, quarter, item = "KR1000", "2023.4Q", 47
    pin = gate._TIER2_ISSUER_INCONSISTENT[(code, quarter)]["cells"][item]["값"]
    mutated = _mutate_cell(records, code, quarter, item, "값", pin + 0.02)
    _acc, red, _rev, _det = _run(mutated, findings)
    assert any(r["rule"] == "TIER2_EXEMPTION_INPUT_DRIFT" for r in red)


@pytest.mark.parametrize("code,quarter,item", [
    ("KR1000", "2023.2Q", 51),
    ("KR0003", "2025.1Q", 4),
    ("KR0087", "2025.2Q", 47),
])
def test_a_missing_input_is_red_not_skip(records, findings, code, quarter, item):
    """**결측은 SKIP 이 아니라 RED 다.** 박제값을 확인할 수 없으면 면제가 성립하지 않는다 —
    SKIP-on-missing 은 이 저장소가 반복해서 데인 검증 무력화 경로다."""
    mutated = _mutate_cell(records, code, quarter, item, "값", None)
    _acc, red, _rev, _det = _run(mutated, findings)
    kinds = {r["rule"] for r in red}
    assert "TIER2_EXEMPTION_INPUT_MISSING" in kinds


def test_a_drifted_bucket_loses_its_exemption_entirely(records, findings):
    """전제가 깨진 버킷은 그 버킷의 finding 이 **하나도** 면제되지 않는다 — 일부만 남기면
    그 셀이 반쯤 사각지대가 된다."""
    code, quarter = "KR0003", "2026.1Q"
    pin = gate._TIER2_ISSUER_INCONSISTENT[(code, quarter)]["cells"][48]["값"]
    mutated = _mutate_cell(records, code, quarter, 48, "값", pin + 5.0)
    accepted, _red, _rev, _det = _run(mutated, findings)
    assert not any(f.get(KEY_CODE) == code and f.get(KEY_QUARTER) == quarter for f in accepted)


def test_the_whole_bucket_vanishing_is_red(records, findings):
    """등재분의 (회사,분기) 버킷이 마스터에서 통째로 사라져도 조용하면 안 된다."""
    code, quarter = "KR1000", "2024.1Q"
    mutated = [r for r in records
               if not (r.get(KEY_CODE) == code and r.get(KEY_QUARTER) == quarter)]
    _acc, red, _rev, _det = _run(mutated, findings)
    assert any(r["rule"] == "TIER2_EXEMPTION_INPUT_MISSING"
               and r["code"] == code and r["quarter"] == quarter for r in red)


# ---------------------------------------------------------------------------
# 2. 겹 ② — 룰 산출을 흔들면 RED 가 돌아온다
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("code,quarter,rule", [
    ("KR1000", "2023.4Q", "3_tier2_composition"),
    ("KR1000", "2024.4Q", "2_tier1_bridge"),
    # 2026-08-24 (iter-7): 종전 ("KR0003","2026.1Q","50_tfi_tier_split") 을 이 자리로 교체했다.
    # 축 E 의 comparand 가 item1(헤드라인)에서 item52(같은 표 지급여력금액 행)로 승격되면서
    # 그 버킷은 그 축에서 정확히 닫힌다 — 재게시된 전기 표는 자기 안에서는 일관되기 때문이다.
    # 죽은 핀은 원장에서 뺐고(게이트가 TIER2_EXEMPTION_INERT 로 먼저 알려 줬다), 재게시라는
    # 사실 자체는 같은 버킷의 `3_tier2_composition` 이 그대로 잡으므로 사각이 생기지 않는다.
    ("KR0003", "2026.1Q", "3_tier2_composition"),
    ("KR0075", "2024.4Q", "51_tfi_tier2_composition"),
    ("KR0087", "2025.2Q", "2_tier1_bridge"),
    # iter-7 신규 등재분도 같은 잣대로 흔든다 — 등재만 하고 재검산을 안 걸면 blanket skip 이다.
    ("KR0032", "2025.4Q", "51_tfi_tier2_composition"),
    # ---- 2026-08-24 2차 owner 위임 등재분 4버킷 -------------------------------
    ("KR0003", "2023.1Q", "50_tfi_tier_split"),
    ("KR0075", "2024.3Q", "51_tfi_tier2_composition"),
    ("KR0004", "2025.1Q", "3_tier2_composition"),
    ("KR0068", "2025.2Q", "2_tier1_bridge"),
])
def test_residual_drift_revives_the_red(records, findings, code, quarter, rule):
    """잔차가 박제값에서 벗어나면 `TIER2_EXEMPTION_RESIDUAL_DRIFT` RED 다."""
    finds = copy.deepcopy(findings)
    for f in finds:
        if (f.get("status") == "RED" and f.get("rule") == rule
                and f.get(KEY_CODE) == code and f.get(KEY_QUARTER) == quarter):
            f["diff"] = (f.get("diff") or 0.0) + 7.0
            break
    else:
        pytest.fail(f"{code} {quarter} {rule} 의 RED 가 findings 에 없다")
    _acc, red, _rev, _det = _run(records, finds)
    assert any(r["rule"] == "TIER2_EXEMPTION_RESIDUAL_DRIFT" and r.get("axis") == rule
               for r in red)


def test_a_different_failure_reason_on_the_same_axis_is_red(records, findings):
    """같은 축이 **다른 사유**로 깨지면 면제가 안 된다. 잔차만 보면 사유가 바뀐 것을 못 본다 —
    `TIER2_LIMIT_STALE` 로 박제한 자리에 `TIER2_DUPLICATE_ROW` 가 와도 통과해 버린다."""
    finds = copy.deepcopy(findings)
    for f in finds:
        if (f.get("status") == "RED" and f.get("rule") == "47_tier2_census"
                and f.get(KEY_CODE) == "KR0003" and f.get(KEY_QUARTER) == "2026.1Q"):
            f["detail"] = "TIER2_NEGATIVE: 전혀 다른 사유"
            break
    else:
        pytest.fail("KR0003 2026.1Q 47_tier2_census RED 가 없다")
    _acc, red, _rev, _det = _run(records, finds)
    assert any(r["rule"] == "TIER2_EXEMPTION_RESIDUAL_DRIFT"
               and r.get("axis") == "47_tier2_census" for r in red)


def test_a_census_pin_that_grows_a_residual_is_red(records, findings):
    """잔차 없는 census 플래그로 박제한 축에 diff 가 생기면 축의 성격이 바뀐 것이다."""
    finds = copy.deepcopy(findings)
    for f in finds:
        if (f.get("status") == "RED" and f.get("rule") == "47_tier2_census"
                and f.get(KEY_CODE) == "KR0087" and f.get(KEY_QUARTER) == "2025.2Q"):
            f["diff"] = 1.0
            break
    else:
        pytest.fail("KR0087 2025.2Q 47_tier2_census RED 가 없다")
    _acc, red, _rev, _det = _run(records, finds)
    assert any(r["rule"] == "TIER2_EXEMPTION_RESIDUAL_DRIFT" for r in red)


def test_an_exemption_that_stopped_firing_is_reported_not_silently_kept(records, findings):
    """RED 가 사라지면 `TIER2_EXEMPTION_INERT` review 가 뜬다 — 무용해진 면제를 조용히 두면
    그 자체가 사각지대다."""
    code, quarter, rule = "KR1000", "2023.3Q", "3_tier2_composition"
    finds = [f for f in findings
             if not (f.get("status") == "RED" and f.get("rule") == rule
                     and f.get(KEY_CODE) == code and f.get(KEY_QUARTER) == quarter)]
    _acc, _red, review, _det = _run(records, finds)
    assert any(r["rule"] == "TIER2_EXEMPTION_INERT" and r["code"] == code
               and r["quarter"] == quarter and r.get("axis") == rule for r in review)


# ---------------------------------------------------------------------------
# 3. 면제가 '끄기' 가 아님을 구조로 못 박는다
# ---------------------------------------------------------------------------
def test_findings_are_never_deleted_only_uncounted(records, findings):
    """면제된 finding 은 **findings 매트릭스에 그대로 남는다.** 골든이 고정하는 것도, 다음
    사람이 읽는 것도 '룰이 무엇을 봤는가' 이고, 면제는 '그중 무엇을 차단하지 않기로 했는가'
    라 층이 다르다."""
    accepted, _red, _rev, _det = _run(records, findings)
    assert accepted, "면제된 finding 이 하나도 없다 — 시험이 무의미하다"
    for f in accepted:
        assert f in findings
        assert f.get("status") == "RED", "면제가 status 를 갈아치우면 안 된다"


def test_pin_tolerance_stays_tight():
    """박제 허용오차를 느슨하게 잡는 순간 '박제' 가 아니라 또 하나의 blanket skip 이 된다.
    마스터 셀은 소수 2자리라 재계산이 결정론적이다."""
    assert gate._TIER2_PIN_TOL <= 0.01


def test_every_pinned_bucket_pins_at_least_one_cell_and_one_axis():
    """축만 박고 셀을 안 박으면 데이터 변화를 못 보고, 셀만 박고 축을 안 박으면 룰 변화를
    못 본다. 두 겹이 비어 있지 않은지 구조로 강제한다."""
    for (code, quarter), spec in gate._TIER2_ISSUER_INCONSISTENT.items():
        assert spec.get("cells"), f"{code} {quarter}: 박제한 셀이 없다"
        assert spec.get("findings"), f"{code} {quarter}: 박제한 축이 없다"


def test_the_registry_is_wired_into_the_provenance_check():
    """레지스트리를 `_exemption_registries()` 에 등록하지 않으면 그 면제는 **근거 없이 조용히
    산다.** 등록돼 있어야 원장에 기계검증 가능한 인용이 없을 때 RED 가 난다."""
    assert "_TIER2_ISSUER_INCONSISTENT" in gate._exemption_registries()


# ---------------------------------------------------------------------------
# 4. 두 게이트가 같은 답을 해야 한다 — 룰만 위임하고 면제를 안 위임하면 안 된다
# ---------------------------------------------------------------------------
def test_the_data_contract_gate_delegates_the_exemption_not_only_the_rules():
    """`validate_data_contract.py` 는 K-ICS 룰을 **위임**해서 RED 를 들어 올린다. 면제를 같이
    위임하지 않으면 같은 finding 을 놓고 두 게이트가 서로 다른 대답을 하고, 등재가 조용히
    무효가 된다(2026-08-24 실측: 등재 직후 데이터계약 게이트에 21건이 그대로 남아 있었다).

    **재구현이 아니라 같은 함수를 부르는지**를 소스에서 강제한다 — 면제 재검산이 두 벌이 되면
    한쪽만 깨지는 경로가 생긴다."""
    src = (ROOT / "scripts" / "validate_data_contract.py").read_text(encoding="utf-8")
    assert "_tier2_issuer_inconsistent" in src, "데이터계약 게이트가 tier2 면제를 위임하지 않는다"
    assert "_life8_issuer_inconsistent" in src, "데이터계약 게이트가 8_life 면제를 위임하지 않는다"
    assert "_TIER2_ISSUER_INCONSISTENT" not in src, "면제 레지스트리를 복사했다 — 위임해야 한다"


def test_the_report_artifact_records_what_was_exempted():
    """**게이트가 말하는 것과 남기는 것이 같아야 한다.** 면제 블록은 report 를 디스크에 쓴 뒤에
    붙기 때문에, 마지막에 다시 쓰지 않으면 콘솔에는 "무엇을 차단하지 않았는가" 가 찍히는데
    아티팩트에는 없다(2026-08-24 발견: `life8_issuer_inconsistent_exception` 도 그동안 디스크에
    없었다). 순서를 소스에서 강제한다."""
    src = (ROOT / "scripts" / "validate_kics_disclosure.py").read_text(encoding="utf-8")
    assign = src.index('report["tier2_issuer_inconsistent_exception"]')
    assert src.index('out_path.write_text', assign) > assign, \
        "면제 블록을 붙인 뒤 report 를 다시 쓰지 않는다 — 아티팩트에 면제 기록이 안 남는다"
    assert src.index('report_latest.json', assign) > assign


def test_a_broken_exemption_still_reds_in_the_data_contract_gate(records, findings):
    """면제가 깨지면(`tier2_exempt_red`) 데이터계약 게이트도 RED 를 낸다 — 위임이 '조용히 빼기'
    가 아니라 '재검산에 통과한 것만 빼기' 임을 못 박는다."""
    code, quarter = "KR0075", "2024.4Q"
    pin = gate._TIER2_ISSUER_INCONSISTENT[(code, quarter)]["cells"][49]["값"]
    mutated = _mutate_cell(records, code, quarter, 49, "값", pin + 5.0)
    accepted, red, _rev, _det = _run(mutated, findings)
    assert red, "전제가 깨졌는데 조용하다"
    assert not any(f.get(KEY_CODE) == code and f.get(KEY_QUARTER) == quarter for f in accepted), \
        "전제가 깨진 버킷이 여전히 면제되고 있다"


def _ledger_entries():
    ledger = json.loads((ROOT / "data" / "_gold" /
                         "kics_exemption_provenance.json").read_text(encoding="utf-8"))
    return {(e.get("company"), e.get("quarter")): e for e in ledger["entries"]
            if e.get("registry") == "_TIER2_ISSUER_INCONSISTENT"}


def test_every_registered_bucket_has_a_verifiable_provenance_entry():
    """원장에 기록이 있고, 그 기록이 기계검증 가능한 인용(파일+페이지+마커)을 든다.

    2026-08-24: status 가 두 값이 됐다. `VERIFIED_BY_OWNER` 는 **마커 검사를 면제하지 않는다** —
    owner 판단은 '이 잔차를 용인한다' 이지 '숫자를 다시 안 봐도 된다' 가 아니다. 그래서 아래
    마커 요구는 두 status 에 똑같이 건다."""
    have = _ledger_entries()
    for key in gate._TIER2_ISSUER_INCONSISTENT:
        assert key in have, f"{key} 의 근거 원장 기록이 없다"
        e = have[key]
        assert e.get("status") in ("VERIFIED", "VERIFIED_BY_OWNER"), \
            f"{key}: status={e.get('status')} — 근거 없는 면제다"
        v = e.get("verify") or {}
        assert v.get("file") and v.get("present_markers"), f"{key}: 기계검증 가능한 인용이 없다"
        assert (ROOT / v["file"]).exists(), f"{key}: 인용한 파일이 디스크에 없다"


def test_an_owner_judgement_entry_must_say_who_read_what_and_when():
    """`VERIFIED_BY_OWNER` 는 산수 증명이 없는 대신 **누가·언제·무엇을 보고 무엇을 결정했는지**
    로 서 있다. 그 블록이 비면 '누군가 확인했다' 는 산문과 같다 — 게이트가 RED 로 막는다."""
    have = _ledger_entries()
    owner_kind = {k: e for k, e in have.items() if e.get("status") == "VERIFIED_BY_OWNER"}
    assert owner_kind, "이 status 를 쓰는 항목이 하나도 없다 — 시험이 무의미하다"
    for key, e in owner_kind.items():
        oc = e.get("owner_confirmation") or {}
        for f in ("read_by", "date", "what_was_read", "verdict"):
            assert oc.get(f), f"{key}: owner_confirmation.{f} 가 비어 있다"

    # 그리고 그 요구가 **게이트에 실제로 배선돼 있는지**를 흔들어 확인한다(선언만 하고 안 도는
    # 검사를 막는다). 필드를 하나 지우면 RED 가 떠야 한다.
    key = next(iter(owner_kind))
    broken = copy.deepcopy(owner_kind[key])
    broken["owner_confirmation"].pop("what_was_read")
    ledger = {"entries": [broken]}
    red, _review = gate._exemption_provenance_findings(
        registries={"_TIER2_ISSUER_INCONSISTENT": frozenset({key})}, ledger=ledger)
    assert any(r["rule"] == "EXEMPTION_OWNER_RECORD_INCOMPLETE" for r in red), \
        f"owner_confirmation 을 깨뜨렸는데 조용하다: {red}"


def test_an_owner_judgement_entry_still_has_to_pass_the_marker_check():
    """owner 가 봤다는 사실이 **숫자 재확인을 면제하지 않는다.** verify 마커를 비우면 RED."""
    have = _ledger_entries()
    key, e = next((k, v) for k, v in have.items() if v.get("status") == "VERIFIED_BY_OWNER")
    broken = copy.deepcopy(e)
    broken["verify"] = {"file": broken["verify"]["file"]}   # 마커만 제거
    red, _review = gate._exemption_provenance_findings(
        registries={"_TIER2_ISSUER_INCONSISTENT": frozenset({key})},
        ledger={"entries": [broken]})
    assert any(r["rule"] == "EXEMPTION_VERIFIED_WITHOUT_MARKERS" for r in red), \
        f"마커를 지웠는데 통과했다: {red}"


def test_an_owner_judgement_exemption_never_goes_quiet():
    """인과가 규명된 면제와 **owner 판단으로만 서 있는 면제**를 게이트가 매 실행 구분해 인쇄한다.
    조용해지면 다음 세션이 '이건 증명된 것' 으로 오독한다 — 이 저장소의 반복 실패모드다."""
    _red, review = gate._exemption_provenance_findings()
    hits = [r for r in review if r["rule"] == "EXEMPTION_STANDS_ON_OWNER_JUDGEMENT"]
    assert hits, "owner 판단 면제가 review 로 인쇄되지 않는다"
    assert {(r["code"], r["quarter"]) for r in hits} == {
        k for k, e in _ledger_entries().items() if e.get("status") == "VERIFIED_BY_OWNER"}


def test_the_two_readings_of_the_hanwha_residual_are_both_recorded():
    """한화생명 면제는 **박제값(−30,095)이 owner 에게 제시된 숫자(826)와 다르다.** 같은 축의
    같은 불일치를 각주 괄호(보완자본 한도 초과액 제외)를 어떻게 읽느냐로 다르게 잰 값이다.

    두 값을 다 적어 두지 않으면 다음 세션이 "박제값이 발주와 다르다" 로 읽고 826 으로 고친다 —
    그 순간 면제가 성립하지 않아(RESIDUAL_DRIFT) 조용히 RED 가 되거나, 더 나쁘게는 허용오차를
    건드려 푼다. 그래서 원장에 **둘 다** 있는 것을 기계로 강제한다."""
    e = _ledger_entries()[("KR0068", "2025.2Q")]
    assert e["expected_residual"]["2_tier1_bridge|적용전"] == -30095.0
    alt = e.get("expected_residual_alt_reading") or {}
    assert any(v == 826.0 for k, v in alt.items() if not k.startswith("_")), \
        "owner 에게 제시된 826 이 원장에 없다"
    assert alt.get("_why"), "두 값이 왜 다른지가 적혀 있지 않다"
    # 박제값은 룰이 실제로 내는 값이어야 한다 — 코드와 원장이 어긋나면 그것부터 사고다.
    assert gate._TIER2_ISSUER_INCONSISTENT[("KR0068", "2025.2Q")]["findings"][
        "2_tier1_bridge"]["residual"] == -30095.0


def test_the_hanwha_pin_catches_a_branch_change_not_only_a_residual_change(records, findings):
    """한화생명 다리는 `branch=CAPPED` 갈래에서만 −30,095 다. 갈래가 바뀌면 같은 잔차가 나와도
    **다른 사실**이므로 면제가 성립하지 않는다 — flag 대조가 그걸 잡는지 흔들어 확인한다."""
    finds = copy.deepcopy(findings)
    for f in finds:
        if (f.get("status") == "RED" and f.get("rule") == "2_tier1_bridge"
                and f.get(KEY_CODE) == "KR0068" and f.get(KEY_QUARTER) == "2025.2Q"):
            f["detail"] = f["detail"].replace("branch=CAPPED", "branch=NEITHER")
            break
    else:
        pytest.fail("KR0068 2025.2Q 2_tier1_bridge RED 가 없다")
    _acc, red, _rev, _det = _run(records, finds)
    assert any(r["rule"] == "TIER2_EXEMPTION_RESIDUAL_DRIFT" and r.get("axis") == "2_tier1_bridge"
               and r["code"] == "KR0068" for r in red)
