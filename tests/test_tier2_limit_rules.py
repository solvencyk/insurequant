# -*- coding: utf-8 -*-
"""보완자본 한도 3줄(항목 47·48·49) 축의 **변이시험**.

## 왜 이 파일이 있나

2026-08-21, parser 가 47/48/49 를 1,299칸 적재했는데 **게이트는 exit 0 이었다.** 산수가
틀렸는데도 통과한 게 아니라, 그 세 항목을 보는 룰이 **하나도 없어서** 통과했다. 손으로
검산해서야 교보생명 홀수분기 5건 100배 · DB생명 100만배가 드러났다.

그래서 "룰을 넣었다"로 끝내지 않는다. **"그 룰이 이 칸을 실제로 본다"** 를 매번 다시 증명한다.
두 문장은 다른 말이고, 이 저장소는 그 차이로 두 달을 날린 적이 있다.

## 네 축이 서로 다른 증거력을 갖는다 — 그 차이도 시험한다

  · `2_tier1_bridge`      (RED)    주 룰. 로더가 강제하지 않는 관계.
  · `3_tier2_composition` (RED)    관행 분류 + item47·49 의 유일한 값 단위 검사.
  · `47_tier2_census`     (RED)    완전성·부호·자릿수. 스코프와 무관해 적용후도 blocking.
  · `48_tier2_limit`      (YELLOW) **로더가 이 식으로 배율을 골랐다 → 통과가 증거가 아니다.**

마지막 축이 YELLOW 인 것은 임계를 느슨하게 잡은 게 아니라 증거력이 없기 때문이다. 그래서
"결함을 넣으면 GREEN 이 아니게 된다" 까지만 시험하고, 같은 결함을 **blocking 으로 잡는 것은
census 축**임을 따로 못 박는다. 이 구분이 무너지면 RED=0 의 의미가 오염된다.

## 합성 데이터를 쓰는 이유

실데이터로 "불일치 0건"을 확인하는 것은 통과가 아니라 무검사일 수 있다 — 애초에 이 사고를
만든 함정이다. 시험값은 실제 필링에서 가져오되(한화손해 2023.1Q·푸본현대 2026.1Q·DB생명
2026.1Q), 결함은 인위적으로 주입해 **발화 여부**를 본다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import (  # noqa: E402
    STATUS_GREEN,
    STATUS_RED,
    STATUS_SKIP,
    STATUS_YELLOW,
    TIER2_ITEMS,
    TIER2_LIMIT_RATIO,
    TIER2_SCALE_CEILING,
    run_validation,
)

CODE, QUARTER = "KR9999", "2026.1Q"

BRIDGE, BRIDGE_POST = "2_tier1_bridge", "2_tier1_bridge_post"
COMP, COMP_POST = "3_tier2_composition", "3_tier2_composition_post"
CENSUS, CENSUS_POST = "47_tier2_census", "47_tier2_census_post"
LIMIT, LIMIT_POST = "48_tier2_limit", "48_tier2_limit_post"
SPLIT, SPLIT_POST = "50_tfi_tier_split", "50_tfi_tier_split_post"
TCOMP, TCOMP_POST = "51_tfi_tier2_composition", "51_tfi_tier2_composition_post"
ALL_RULES = (BRIDGE, BRIDGE_POST, COMP, COMP_POST, CENSUS, CENSUS_POST, LIMIT, LIMIT_POST)

# 한화손해(KR0002) 2023.1Q 실제 필링. raw p8/p9 에서 단어 좌표로 직접 판독한 값이다.
#   기본자본 26,838 = 순자산 51,965 − 불인정 639 − 재분류 24,488          (다리 정확히 닫힘)
#   보완자본 30,385 = min(한도적용전 10,258, 한도 16,193) + 초과분 20,126  (CAPPED)
#   한도 16,193 = 지급여력기준금액 32,387 × 50%
BASE = {2: 26_838.0, 3: 30_385.0, 4: 51_965.0, 12: 639.0, 13: 24_488.0,
        14: 32_387.0, 47: 10_258.0, 48: 16_193.0, 49: 20_126.0}


def _rec(item: int, pre=None, post=None, quarter: str = QUARTER) -> dict:
    """한 행. `post=None` 이면 `값_적용후` 키 자체를 넣지 않는다 — 엔진이 키 유무로
    '적용후 셀이 있는가' 를 판정하므로 None 을 채워 넣으면 시험이 무의미해진다."""
    row = {"원보험사코드": CODE, "원수사명": "시험보험", "공시분기": quarter,
           "항목번호": item, "항목명": f"시험항목{item}"}
    if pre is not None:
        row["값"] = pre
    if post is not None:
        row["값_적용후"] = post
    return row


def _mk(pre: dict | None = None, post: dict | None = None,
        quarter: str = QUARTER) -> list[dict]:
    pre, post = (pre or {}), (post or {})
    return [_rec(i, pre.get(i), post.get(i), quarter)
            for i in sorted(set(pre) | set(post))]


def _findings_q(records, quarter: str, tfi: dict | None = None) -> dict[str, dict]:
    """여러 분기가 섞인 레코드에서 **특정 분기의** finding 만 골라 낸다.
    분기간(stale) 검사는 두 분기를 같이 넣어야 발화한다."""
    from solvency.validation.kics_json_rules import run_validation as _rv
    return {f["rule"]: f for f in _rv(records, tfi_applicability=tfi)["findings"]
            if f["공시분기"] == quarter}


def _base(over: dict | None = None) -> dict:
    """BASE 사본에 덮어쓸 항목만 바꾼다. 키가 int 라 **kwargs 로는 못 받는다."""
    d = dict(BASE)
    d.update(over or {})
    return d


def _findings(records, tfi: dict | None = None) -> dict[str, dict]:
    return {f["rule"]: f
            for f in run_validation(records, tfi_applicability=tfi)["findings"]}


def _status(records, rule: str) -> str:
    found = _findings(records)
    assert rule in found, f"룰 {rule} 이 finding 을 하나도 안 냈다 — 배선이 끊겼다"
    return found[rule]["status"]


def _branch_of(detail: str) -> str:
    """detail 에서 갈래 이름을 **정확히** 뽑는다.

    `"branch=CAPPED" in detail` 같은 부분문자열 검사는 `branch=I49_IN_I47_CAPPED` 도 참으로
    만들어 두 갈래를 한 이름으로 뭉갠다(2026-08-24 스코프 갈래 신설 때의 함정)."""
    i = detail.find("branch=")
    return "" if i < 0 else detail[i + len("branch="):].split()[0]


# ---------------------------------------------------------------------------
# 0. 배선 — 데이터가 없어도 룰은 자기 존재와 결측 사유를 알려야 한다
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rule", ALL_RULES)
def test_every_axis_emits_even_with_no_tier2_data(rule):
    """47/48/49 가 0칸이어도 여덟 축 모두 finding 을 낸다.

    침묵은 통과로 읽힌다. 결측은 **사유 문자열이 붙은 비-GREEN** 이어야 게이트가 사유별로
    세고, '1,299칸이 조용히 무검사' 상태가 다시 오면 그 카운트로 드러난다.

    census 두 축만 SKIP 이 아니라 **YELLOW(review)** 다. 여기서는 적용여부 사이드카를 안
    실었으므로 부재가 정상인지 추출갭인지 판정할 근거가 없고, 근거 없는 부재를 SKIP 으로
    적으면 그것이 곧 통과다(2026-08-22 iter-5). 판정 근거가 실리면 §8 시험대로 갈린다."""
    found = _findings(_mk({2: 100.0, 14: 200.0}))
    assert rule in found, f"{rule} 이 아예 안 나온다 — 결측이 침묵이 됐다"
    expected = STATUS_YELLOW if rule in (CENSUS, CENSUS_POST) else STATUS_SKIP
    assert found[rule]["status"] == expected
    assert found[rule]["detail"].strip(), f"{rule} 의 결측 사유가 비었다 — 집계할 수 없다"


def test_real_filing_passes_every_axis():
    """실제 필링(한화손해 2023.1Q)은 네 축 전부 통과해야 한다 — 오탐 방향 대조군."""
    found = _findings(_mk(BASE))
    for rule in (BRIDGE, COMP, CENSUS, LIMIT):
        assert found[rule]["status"] == STATUS_GREEN, (
            f"{rule} 이 정상 필링을 잡았다: {found[rule]['detail']}")


# ---------------------------------------------------------------------------
# 1. 주 룰 — 기본자본 다리 (로더가 강제하지 않는 관계)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("item", [2, 4, 12, 13])
def test_bridge_catches_every_input_it_claims_to_check(item):
    """다리에 들어가는 네 항목을 각각 흔들어 실제로 걸리는지 확인한다.

    '룰을 넣었다'와 '그 룰이 이 칸을 본다'는 다른 말이다 — 네 개를 따로 흔든다."""
    assert _status(_mk(_base({item: BASE[item] + 500.0})), BRIDGE) == STATUS_RED


def test_bridge_uses_the_excess_term_for_capped_issuers():
    """푸본현대 2026.1Q: 7,254 − (7,460 − 3,447.39) − 3,132 = 109.39 ≈ 공시 109.

    한도초과 항이 없으면 이 회사는 3,447 만큼 어긋난다 — 그래서 항이 필요하다."""
    pre = {2: 109.0, 3: 7_962.60, 4: 7_254.0, 12: 7_460.0, 13: 3_132.0,
           14: 13_925.20, 47: 10_409.99, 48: 6_962.60, 49: 1_000.0}
    assert _status(_mk(pre), COMP) == STATUS_GREEN          # CAPPED 로 분류돼야 하고
    assert _status(_mk(pre), BRIDGE) == STATUS_GREEN        # 그래야 다리가 닫힌다


def test_bridge_does_not_apply_excess_to_uncapped_issuers():
    """한화생명류(보완자본 = 한도적용전, 한도로 안 잘림)에 초과항을 더하면 안 된다.

    실측 근거: 초과항을 조건 없이 더하면 적용전 통과가 425 → 393 으로 **줄어든다**
    (한화생명 13분기 · KB손해 6분기가 새로 깨진다). 조건부만이 맞다."""
    # item3 == item47 → 한도 미구속. 초과액 개념이 없으므로 다리는 초과항 없이 닫혀야 한다.
    # 이 필링은 item47 이 item49 를 포함해 인쇄되는 쪽이라 갈래 이름은
    # `I49_IN_I47_UNCAPPED` 다(2026-08-24 스코프 인식 전에는 `UNCAPPED` 로 뭉개져 있었다).
    from solvency.validation.kics_json_rules import _TIER2_UNCAPPED_BRANCHES
    pre = {2: 26_838.0, 3: 20_000.0, 4: 51_965.0, 12: 639.0, 13: 24_488.0,
           14: 32_387.0, 47: 20_000.0, 48: 16_193.0, 49: 5_000.0}
    found = _findings(_mk(pre))
    assert _branch_of(found[COMP]["detail"]) in _TIER2_UNCAPPED_BRANCHES, (
        f"한도 미구속 갈래로 안 갔다: {_branch_of(found[COMP]['detail'])!r}")
    assert found[BRIDGE]["status"] == STATUS_GREEN, (
        "한도 미구속 회사에 초과항을 더해 다리를 깨뜨렸다")


def test_bridge_uses_the_debt_only_excess_for_i49_in_i47_issuers():
    """**한화생명 2025.2Q 재현 — 이 시험이 없었으면 그 −30,095 가 또 생긴다.**

    이 발행사는 `item47`(보완자본 한도 적용 전)에 `item49`(해약환급금 초과분)를 **포함해서**
    인쇄하고, 한도(`item48`)는 나머지 채무성 자본에만 걸린다. 그래서 한도초과액은
    `item47 − item48`(= 70,821.29) 이 아니라 `(item47 − item49) − item48`(= 825.74) 이다.

    값은 raw FY2025_Q2 p17·p18 그대로다. 여기 두 분기를 같이 넣는 이유는 스코프가 **회사
    단위 투표**이기 때문이다 — 2025.1Q(한도 미구속, `item3 == item47` 이고 item49 > 0)가
    "item49 가 item47 안에 있다"는 증거를 제공한다."""
    binding = {2: 82_506.0, 3: 139_303.0, 4: 213_475.0, 12: 30_921.0, 13: 100_874.0,
               14: 138_613.97, 47: 140_128.28, 48: 69_306.99, 49: 69_995.55}
    evidence = {3: 122_252.26, 14: 136_764.42,
                47: 122_252.26, 48: 68_382.21, 49: 64_328.43}
    found = _findings_q(_mk(binding) + _mk(evidence, quarter="2025.1Q"), QUARTER)
    assert _branch_of(found[COMP]["detail"]) == "I49_IN_I47_CAPPED", (
        f"스코프를 못 알아봤다: {_branch_of(found[COMP]['detail'])!r}")
    # 213,475 − (30,921 − 825.74) − 100,874 = 82,505.74  vs 공시 82,506  -> 잔차 0.26
    assert found[BRIDGE]["status"] == STATUS_GREEN, (
        f"다리가 안 닫힌다 (diff={found[BRIDGE]['diff']}) — 한도초과액이 item49 만큼 "
        "과대·과소 계산되고 있다. 갈래를 늘리면서 _TIER2_EXCESS_BEARING_BRANCHES 를 "
        "안 고치면 정확히 이 상태가 된다(초과액이 조용히 0 이 된다).")
    assert "825.74" in found[BRIDGE]["detail"], (
        f"한도초과액이 825.74 가 아니다: {found[BRIDGE]['detail']}")


def test_bridge_skips_on_missing_input_with_a_reason_never_falls_back():
    """**혼합기준 방지.** 적용후가 없는 항목을 적용전으로 메우면 서로 다른 기준의 값을 한
    식에 섞게 되고, 그렇게 나온 통과·실패는 둘 다 무의미하다."""
    found = _findings(_mk(BASE))          # 적용후 셀이 하나도 없다
    assert found[BRIDGE_POST]["status"] == STATUS_SKIP, (
        "적용후 입력이 없는데 판정을 내렸다 — 적용전 값을 적용후 통과로 세고 있다")
    assert "BRIDGE_INPUT_MISSING" in found[BRIDGE_POST]["detail"]


def test_bridge_runs_on_the_post_column_when_inputs_genuinely_exist():
    """적용전만 배선하고 끝내지 않았는지 — 적용후 입력이 진짜 있으면 계산한다."""
    post = {2: 31_073.0, 3: 26_150.0, 4: 51_965.0, 12: 639.0, 13: 24_488.0}
    found = _findings(_mk(BASE, post))
    assert found[BRIDGE_POST]["status"] != STATUS_SKIP
    assert "값_적용후" in found[BRIDGE_POST]["detail"]


# ---------------------------------------------------------------------------
# 2. 보완자본 구성 — item47·item49 가 값 단위로 검사되는 유일한 축
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("item", [3, 47, 49])
def test_composition_catches_each_of_its_inputs(item):
    """item47·item49 를 무검사로 두지 않았음을 증명한다.

    census(존재·부호·자릿수)만으로는 '값이 그럴듯하게 틀린' 경우를 못 잡는다. 이 축이
    그걸 잡는 유일한 축이라, 세 입력을 각각 흔들어 확인한다."""
    assert _status(_mk(_base({item: BASE[item] * 1.5 + 1_234.0})), COMP) == STATUS_RED


def test_composition_reports_both_candidates_when_neither_reproduces():
    found = _findings(_mk(_base({3: 99_999.0})))
    assert found[COMP]["status"] == STATUS_RED
    assert "COMPOSITION_NEITHER" in found[COMP]["detail"]


def test_composition_post_is_review_not_red_because_the_identity_is_unestablished():
    """**적용후 관계식을 확립하지 못했으면 위반이라고 단정하지 않는다.**

    반증 실측(한화손해 2023.2Q raw p11): `보완자본 한도 적용 전 1,022,151 / 11,442` 로
    적용후가 적용전의 1/89 인데 **원문이 실제로 그렇게 인쇄돼 있다**. 적용전 식은 정확히
    닫히고(30,730.03) 적용후만 5,872.17 어긋난다 — 추출이 아니라 식이 안 맞는 것이다.
    이걸 RED 로 걸면 220칸이 전부 오탐이 된다."""
    post = {3: 26_495.11, 47: 114.42, 48: 16_742.97, 49: 20_508.52}
    found = _findings(_mk(BASE, post))
    assert found[COMP_POST]["status"] == STATUS_YELLOW
    assert "POST_IDENTITY_UNESTABLISHED" in found[COMP_POST]["detail"]
    # 그러나 조용하지는 않다 — 잔차를 숫자로 남긴다
    assert found[COMP_POST]["diff"] is not None


# ---------------------------------------------------------------------------
# 3. census — 완전성 · 부호 · 자릿수 (스코프와 무관 → 적용후도 blocking)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("drop", TIER2_ITEMS)
def test_partial_rows_are_red(drop):
    """같은 표의 연속 3행이라 부분결측은 행 유실 신호다. 결측은 SKIP 이 아니라 RED."""
    pre = {k: v for k, v in BASE.items() if k != drop}
    found = _findings(_mk(pre))
    assert found[CENSUS]["status"] == STATUS_RED
    assert "TIER2_PARTIAL_ROWS" in found[CENSUS]["detail"]
    assert str(drop) in found[CENSUS]["detail"], "어느 항목이 빠졌는지 안 적으면 추적이 안 된다"


@pytest.mark.parametrize("item", TIER2_ITEMS)
def test_negative_amount_is_red(item):
    found = _findings(_mk(_base({item: -1.0})))
    assert found[CENSUS]["status"] == STATUS_RED
    assert "TIER2_NEGATIVE" in found[CENSUS]["detail"]


@pytest.mark.parametrize("item", TIER2_ITEMS)
def test_hundredfold_unit_scale_is_red_on_every_one_of_the_three(item):
    """실제 사고(교보생명 홀수분기 5건)는 **세 줄에 동시에** 왔다. item48 만 걸면 나머지
    둘은 그대로 사각이다."""
    found = _findings(_mk(_base({item: BASE[item] * 100})))
    assert found[CENSUS]["status"] == STATUS_RED
    assert "TIER2_SCALE" in found[CENSUS]["detail"]
    assert f"item{item}" in found[CENSUS]["detail"]


def test_millionfold_is_red():
    """DB생명 2026.1Q 실측: item48 = 7,437,557,437.55 (기대 7,437.50, 배율 100만)."""
    pre = _base({14: 14_875.0, 48: 7_437_557_437.55})
    assert _status(_mk(pre), CENSUS) == STATUS_RED


def test_census_is_blocking_on_the_post_column_too():
    """완전성·부호·자릿수는 스코프 논쟁과 무관하다 → 적용후도 RED 로 막는다."""
    found = _findings(_mk(BASE, {47: 10_258.0, 48: 16_193.0, 49: 20_126.0 * 100}))
    assert found[CENSUS]["status"] == STATUS_GREEN
    assert found[CENSUS_POST]["status"] == STATUS_RED
    assert "TIER2_SCALE" in found[CENSUS_POST]["detail"]


def test_legit_ratio_above_one_is_not_flagged():
    """KB손해 2025.1Q 실측: item47 = 66,274.84 / item14 = 63,515.44 = 1.043.

    한도 적용 전은 SCR 을 넘을 수 있다 — 상한을 1 이나 2 로 잡으면 정상 필링을 오탐한다."""
    pre = {2: 1.0, 3: 1.0, 4: 1.0, 12: 0.0, 13: 0.0, 14: 63_515.44,
           47: 66_274.84, 48: 31_757.72, 49: 51_879.15}
    assert _status(_mk(pre), CENSUS) == STATUS_GREEN


def test_scale_ceiling_sits_between_observed_max_and_the_defect():
    """임계가 조용히 느슨해지는 것을 막는다 — 100 이상으로 올리면 이 시험이 실패한다."""
    assert 1.04 < TIER2_SCALE_CEILING < 100.0
    assert TIER2_LIMIT_RATIO == 0.5


# ---------------------------------------------------------------------------
# 4. 한도 축 — 로더가 강제하므로 **통과가 증거가 아니다**
# ---------------------------------------------------------------------------
def test_limit_axis_is_not_blocking_because_the_loader_enforces_it():
    """parser 가 스케일 배율(÷1 vs ÷100)을 `item48 ≈ item14 × 50%` 로 골라 저장한다.
    그러므로 이 축의 GREEN 은 추출 정확성의 증거가 아니다 — blocking 으로 세면
    게이트 전체의 RED=0 이 오염된다."""
    found = _findings(_mk(_base({48: 16_193.0 * 100})))
    assert found[LIMIT]["status"] == STATUS_YELLOW, "증거력 없는 축이 blocking 이 됐다"
    assert "LOADER_ENFORCED" in found[LIMIT]["detail"]
    # 같은 결함을 **blocking 으로 잡는 것은 census 축**이라는 분업을 못 박는다
    assert found[CENSUS]["status"] == STATUS_RED


def test_limit_post_uses_the_pre_transition_scr_as_denominator():
    """**분모를 틀리면 241칸이 전부 오탐이 된다.**

    `(1)공통적용 경과조치` 표의 한도는 TFI 단독 스코프라 그 표의 SCR 을 안 움직인다.
    원문(한화손해 2023.1Q p9): 그 표의 `지급여력기준금액 32,387 / 32,387` 이 두 컬럼
    동일하고 한도는 `16,193 / 16,193`. 마스터 item14_적용후(22,492)는 선택 경과조치까지
    합친 전체결합 스코프라 개념이 다르다.

    전수 실측: item14 가 전≠후인 216칸에서 item48_적용후가 `item14_전×50%` 와 맞는 것이
    215칸, `item14_후×50%` 와 맞는 것이 **0칸**."""
    found = _findings(_mk(BASE, {14: 22_492.0, 47: 6_023.0, 48: 16_193.0, 49: 20_126.0}))
    assert found[LIMIT_POST]["status"] == STATUS_GREEN, (
        "적용후 한도를 item14_적용후로 나눴다 — 실측 215:0 으로 반증된 기준이다")
    # 분모가 적용전임을 값으로 확인 (32,387 × 0.5 = 16,193.5)
    assert abs(found[LIMIT_POST]["expected"] - 16_193.5) < 0.01


# ---------------------------------------------------------------------------
# 5. 갈래(branch)별 변이시험 — **갈래를 나눈 것이 면제가 되지 않았음을 증명한다**
#
# 2026-08-22. `3_tier2_composition` RED 27건을 전수 분류한 결과, 그중 12건은 발행사가
# TFI(공통적용 경과조치) 표에 세 행을 전부 0 으로 인쇄한 회사였다 — 한도 항등식의 입력이
# 아예 없는 상태다. 갈래를 나누는 것 자체는 옳지만, **나누기만 하면 그건 검사가 아니라
# 분류다.** 이 저장소는 바로 전날 `48_tier2_limit` 이 로더 강제라 무의미해진 전례를 겪었고
# `LOADER_ENFORCED` 로 표시해 뒀다. 그래서 새 갈래마다 "그 갈래 안에서도 RED 가 난다" 를
# 기계로 증명한다. 증명이 없는 갈래는 면제와 구별되지 않는다.
# ---------------------------------------------------------------------------

# 메트라이프생명(KR0095) 2023.1Q 실측. raw p11 이 세 행을 0 으로 인쇄한다
# (바로 아래 "(기발행 신종자본증권) 0" · "(기발행 후순위채무) 0" 이 결정적 증거).
# item48 = 0 인데 SCR = 15,642 > 0 이므로 **item48 은 한도가 아니다**(SCR x 50% = 7,821).
# 그 상태에서 보완자본은 전액 재분류항목이어야 한다: item3 8,081 == item13 8,081.
TFI_NA = {2: 40_676.0, 3: 8_081.0, 4: 48_760.0, 12: 4.0, 13: 8_081.0,
          14: 15_642.0, 47: 0.0, 48: 0.0, 49: 0.0}


def _base_of(src: dict, over: dict) -> dict:
    d = dict(src)
    d.update(over)
    return d


def test_tfi_na_branch_reproduces_the_real_metlife_filing():
    """대조군 — 실제 필링이 새 갈래로 통과하고, 그 사실이 detail 에 남는다."""
    found = _findings(_mk(TFI_NA))
    assert found[COMP]["status"] == STATUS_GREEN
    assert "TFI_NA_OK" in found[COMP]["detail"]
    # 통과했다는 사실만 남기면 다음 사람이 '무검사'와 구별하지 못한다 — 대체 항등식을 밝힌다
    assert "item13" in found[COMP]["detail"]
    assert found[COMP]["expected"] == TFI_NA[13]


@pytest.mark.parametrize("item", [3, 13])
def test_tfi_na_branch_is_a_check_not_an_exemption(item):
    """**핵심 시험.** 이 갈래 안에서도 값을 흔들면 RED 가 나야 한다.

    갈래를 나눴더니 그 갈래의 모든 칸이 자동 통과한다면 그건 검사가 아니라 면제다.
    대체 항등식 `item3 == item13` 의 두 입력을 각각 흔든다."""
    found = _findings(_mk(_base_of(TFI_NA, {item: TFI_NA[item] + 500.0})))
    assert found[COMP]["status"] == STATUS_RED, (
        f"TFI_NA 갈래에서 item{item} 을 500 흔들었는데 통과했다 — 갈래가 면제가 됐다")
    assert "COMPOSITION_TFI_NA_RECLASS_BREAK" in found[COMP]["detail"]


def test_tfi_na_needs_all_three_rows_zero():
    """세 행 중 하나라도 값이 있으면 표는 기재된 것이다 → 원래 한도 항등식으로 돌아간다.

    갈래 판정이 느슨해지면 '한도 항등식이 안 맞는 회사'가 전부 이리로 새어 들어온다."""
    found = _findings(_mk(_base_of(TFI_NA, {47: 100.0})))
    assert found[COMP]["status"] == STATUS_RED
    assert "COMPOSITION_NEITHER" in found[COMP]["detail"], (
        "세 행 중 하나가 0 이 아닌데도 TFI_NA 갈래로 빠졌다")


def test_tfi_na_needs_a_positive_scr():
    """SCR 이 0 이면 한도가 0 인 것이 정상이라 '한도가 아니다' 라고 말할 근거가 없다.

    이 갈래의 판정 근거는 오직 하나 — **item48 = 0 인데 SCR > 0 이면 item48 은 SCR x 50%
    가 될 수 없다** 는 산술적 모순이다. SCR 이 0 이면 그 모순이 사라지므로 갈래도 사라진다."""
    found = _findings(_mk(_base_of(TFI_NA, {14: 0.0})))
    assert "TFI_NA" not in found[COMP]["detail"]


def test_tfi_na_branch_does_not_leak_an_excess_into_the_bridge():
    """한도 메커니즘이 없으면 한도초과액도 없다 — 다리는 순수 I-II-III 로 닫혀야 한다.

    실측 메트라이프 2023.1Q: 48,760 − 4 − 8,081 = 40,675 vs 공시 40,676 → 잔차 1
    (억원 정수 반올림 범위, YELLOW). 초과항이 새어 들어오면 여기가 RED 가 된다."""
    found = _findings(_mk(TFI_NA))
    assert found[BRIDGE]["status"] != STATUS_RED
    assert abs(found[BRIDGE]["diff"]) <= 2.0
    assert "한도초과=0" in found[BRIDGE]["detail"]


# ---------------------------------------------------------------------------
# 6. 다리의 구조적 상한 — 한도초과액 <= 불인정항목(item12)
# ---------------------------------------------------------------------------

# 케이디비생명(KR0072) 2024.3Q 실측. item12 = 0(배당예정액이 없는 회사)인데
# 근사치 max(0, 47-48) = 913.29 이라, 클램프가 없으면 다리가 913.29 만큼 과잉보정된다.
# 클램프하면 4,393 - 0 - 6,716 = -2,323 = 공시 기본자본 **정확히 일치**.
KDB = {2: -2_323.0, 3: 11_406.0, 4: 4_393.0, 12: 0.0, 13: 6_716.0,
       14: 13_697.0, 47: 7_761.53, 48: 6_848.24, 49: 4_557.65}


def test_bridge_clamps_the_excess_to_item12_and_closes_the_zero_case():
    """근거는 발행사 각주다(미래에셋생명 2023.2Q p11 주2): 기본자본은 순자산에서
    "지급여력금액 불인정 항목(단, **보완자본 한도를 초과한 금액을 제외**)" 을 차감한다.
    한도초과액은 불인정항목 **안의 구성요소**라 그보다 클 수 없다.

    허용오차를 키운 게 아니라 불가능한 값을 잘라낸 것이다 — 실측 461/16 -> 467/10."""
    found = _findings(_mk(KDB))
    assert found[COMP]["status"] == STATUS_GREEN            # CAPPED 로 분류되고
    assert found[BRIDGE]["status"] == STATUS_GREEN          # 클램프 덕에 다리가 닫힌다
    assert "클램프" in found[BRIDGE]["detail"]


def test_bridge_clamp_still_fails_when_the_residual_survives():
    """**클램프는 실패를 지우지 않는다.** 한화생명 2025.2Q 실측 — 근사치(70,821.29)가
    item12(30,921)의 2.3배라 클램프가 세게 걸리는데, 그래도 다리가 30,095 어긋난 채
    RED 로 남는다. 클램프가 '안 닫히는 칸을 닫아 주는 장치'가 아님을 못 박는다."""
    hanwha = {2: 82_506.0, 3: 139_303.0, 4: 213_475.0, 12: 30_921.0, 13: 100_874.0,
              14: 138_614.0, 47: 140_128.28, 48: 69_306.99, 49: 69_995.55}
    found = _findings(_mk(hanwha))
    assert found[COMP]["status"] == STATUS_GREEN            # 구성은 CAPPED 로 닫히는데
    assert found[BRIDGE]["status"] == STATUS_RED            # 다리는 그대로 RED
    assert abs(found[BRIDGE]["diff"] + 30_095.0) < 1.0


def test_bridge_clamp_does_not_blind_item12_when_it_does_not_bind():
    """클램프가 안 걸리는 대다수 칸(실측 CAPPED 349칸 중 339칸)에서는 item12 가 그대로
    검사돼야 한다 — 클램프를 넣느라 입력 하나를 통째로 사각으로 만들지 않았음을 확인한다."""
    # 한화손해 2023.1Q: 근사치 max(0, 10,258 - 16,193) = 0 -> 클램프 무관
    assert _status(_mk(_base({12: BASE[12] + 500.0})), BRIDGE) == STATUS_RED


# ---------------------------------------------------------------------------
# 7. census 신설분 — 중복행 · 전기 한도 잔존
# ---------------------------------------------------------------------------

def test_duplicate_row_47_equals_48_is_red():
    """item48 은 SCR x 50% 라는 **공식값**이고 item47 은 독립 합계다. 소수 둘째자리까지
    우연히 같을 수 없다 -> 같은 셀을 두 번 읽은 지문.

    실측 4칸(BNP카디프 2024.3Q·2024.4Q·2025.1Q · 동양생명 2025.2Q)이고 넷 다 이미
    다리나 구성 축에서 깨져 있었다 — 이 검사는 새 오탐을 만들지 않고 진단만 정확하게 한다."""
    bnp = {2: 1_738.0, 3: 331.0, 4: 2_098.0, 12: 44.0, 13: 331.0,
           14: 632.0, 47: 316.14, 48: 316.14, 49: 235.84}
    found = _findings(_mk(bnp))
    assert found[CENSUS]["status"] == STATUS_RED
    assert "TIER2_DUPLICATE_ROW" in found[CENSUS]["detail"]


def test_duplicate_row_ignores_all_zero_rows():
    """0 == 0 은 중복이 아니라 미기재다 — TFI_NA 갈래 24칸을 오탐하면 안 된다."""
    found = _findings(_mk(TFI_NA))
    assert "TIER2_DUPLICATE_ROW" not in found[CENSUS]["detail"]
    assert found[CENSUS]["status"] == STATUS_GREEN


def test_item47_equal_to_item49_is_not_flagged():
    """**오탐 방향 대조군.** item47 == item49 는 정당하다 — 한도적용전 총액이 전부
    해약환급금 초과분인 회사가 실재한다(BNP카디프 2023.1Q 82.68/82.68, 공시 보완자본 83).
    실측 9칸이 이 형태이고 대부분 정상 통과한다. 중복 판정을 47-48 에만 거는 이유다."""
    bnp = {2: 2_237.0, 3: 83.0, 4: 2_320.0, 12: 0.0, 13: 83.0,
           14: 645.0, 47: 82.68, 48: 322.56, 49: 82.68}
    found = _findings(_mk(bnp))
    assert found[CENSUS]["status"] == STATUS_GREEN
    assert found[COMP]["status"] == STATUS_GREEN


# 롯데손해(KR0003) 2025.4Q -> 2026.1Q 실측. 2026.1Q 의 47/48/49 적용전 3칸이 2025.4Q 와
# 바이트까지 동일하고, item48(10,335.34)은 **2025.4Q** SCR x 50%(20,671 x 0.5 = 10,335.5)와
# 맞는다. 당분기 SCR x 50%(20,432 x 0.5 = 10,216)와는 119.34 어긋난다.
_LOTTE_PREV = {2: -3_875.0, 3: 29_934.0, 4: 18_185.0, 12: 19.0, 13: 22_040.0,
               14: 20_671.0, 47: 8_366.25, 48: 10_335.34, 49: 21_567.39}
_LOTTE_CUR = {2: -3_962.0, 3: 30_918.0, 4: 19_208.0, 12: 23.0, 13: 23_147.0,
              14: 20_432.0, 47: 8_366.25, 48: 10_335.34, 49: 21_567.39}


def test_stale_limit_from_the_previous_quarter_is_red():
    """산수는 맞는데 **소스가 직전분기**인 false-green. 이 저장소의 반복 사고형태라
    한 칸 단위로 잡는다."""
    recs = _mk(_LOTTE_PREV, quarter="2025.4Q") + _mk(_LOTTE_CUR, quarter="2026.1Q")
    found = _findings_q(recs, "2026.1Q")
    assert found[CENSUS]["status"] == STATUS_RED
    assert "TIER2_LIMIT_STALE" in found[CENSUS]["detail"]
    # 직전분기 자신은 깨끗해야 한다 — 잔존을 앞뒤로 번지게 하면 진단이 무의미해진다
    assert _findings_q(recs, "2025.4Q")[CENSUS]["status"] == STATUS_GREEN


def test_stale_limit_needs_the_scr_to_have_actually_moved():
    """SCR 이 안 움직인 분기에서는 '당분기 한도'와 '전분기 한도'가 구별되지 않는다.
    구별 못 하는 것을 위반이라 부르면 오탐이므로, 그때는 아예 판정하지 않는다."""
    prev = dict(_LOTTE_PREV)
    cur = _base_of(_LOTTE_CUR, {14: _LOTTE_PREV[14]})   # SCR 동일
    recs = _mk(prev, quarter="2025.4Q") + _mk(cur, quarter="2026.1Q")
    assert "TIER2_LIMIT_STALE" not in _findings_q(recs, "2026.1Q")[CENSUS]["detail"]


def test_stale_limit_also_checked_on_the_post_column():
    """적용전만 배선하고 끝내지 않는다 — 적용후 한도의 분모도 item14_적용전이다."""
    recs = (_mk(_LOTTE_PREV, _LOTTE_PREV, quarter="2025.4Q")
            + _mk(_LOTTE_CUR, _LOTTE_CUR, quarter="2026.1Q"))
    found = _findings_q(recs, "2026.1Q")
    assert found[CENSUS_POST]["status"] == STATUS_RED
    assert "TIER2_LIMIT_STALE" in found[CENSUS_POST]["detail"]


# ---------------------------------------------------------------------------
# 8. 부재 판정은 **적용여부 실측**으로 한다 — 추론이 아니라 (2026-08-22 iter-5 재배선)
#
# 그 전 기준은 "같은 회사가 다른 분기엔 공시했나"(INTERMITTENT -> RED)였다. **틀린
# 기준이었다.** 47/48/49 는 [지급여력비율의 경과조치 적용에 관한 사항] (1)공통적용
# 경과조치 표의 행이고, TFI 는 그 자본증권이 상환·만기되면 적용이 끝난다 — 분기마다
# 켜졌다 꺼지는 것이 정상이다. 원문으로 확인했다: 교보라이프플래닛 2023.1Q(TFI=O) MD 에
# `보완자본 한도` 3회 + 표 존재, 2023.2Q 이후(TFI=X) 같은 키워드 **0회**. 옛 기준은 그
# 12버킷 × 2컬럼 = 24칸을 추출갭으로 오판하고 있었다.
#
# 아래 세 시험이 이 룰의 뼈대다. 하나라도 빠지면 룰이 "파일 못 읽으면 조용히 통과"로
# 퇴화한다 — 이 저장소가 반복해서 당한 형태다.
# ---------------------------------------------------------------------------

_ABSENT = {2: 100.0, 3: 50.0, 4: 200.0, 12: 0.0, 13: 50.0, 14: 300.0}


def test_absent_is_red_when_the_issuer_actually_applied_tfi():
    """**TFI=O 인데 47/48/49 가 없다 → RED.**

    발행사가 공통적용 경과조치를 적용했으면 (1)공통적용 경과조치 표가 실제 숫자와 함께
    존재해야 한다. 그런데 우리 마스터에 한 칸도 없다면 원천부재가 아니라 **추출갭**이다.
    실측 1버킷(미래에셋생명 2023.3Q)이 여기 해당하고 parser 발주 대상이다."""
    f = _findings(_mk(_ABSENT), tfi={(CODE, QUARTER): "O"})[CENSUS]
    assert f["status"] == STATUS_RED, (
        "TFI=O 는 표가 존재해야 한다는 뜻인데 부재가 blocking 이 아니다 — "
        "추출갭이 조용히 통과한다")
    assert "TIER2_TABLE_ABSENT_BUT_TFI_APPLIED" in f["detail"]


def test_absent_is_not_red_when_the_issuer_did_not_apply_tfi():
    """**TFI=X 인데 47/48/49 가 없다 → RED 가 아니다.**

    적용하지 않으면 발행사가 근거표를 안 그린다. 우리 결함이 아니므로 blocking 으로 세면
    고칠 방법이 없는 RED 로 게이트를 영구히 막게 된다. 다만 GREEN 도 아니다 — 값을
    검산한 것이 아니라 '부재가 정상'이라고 판정한 것뿐이라 **사유를 붙여 SKIP** 한다."""
    f = _findings(_mk(_ABSENT), tfi={(CODE, QUARTER): "X"})[CENSUS]
    assert f["status"] == STATUS_SKIP, "정상 부재를 RED 로 세면 안 된다"
    assert "TIER2_TABLE_ABSENT_TFI_NOT_APPLIED" in f["detail"]
    assert f["status"] != STATUS_GREEN, "검산한 적이 없으므로 GREEN 을 주면 안 된다"


@pytest.mark.parametrize(
    "tfi, why",
    [
        (None, "사이드카 파일 자체가 없다(로더가 빈 맵을 돌려준 상태)"),
        ({}, "사이드카는 읽혔는데 (회사,분기) 키가 없다"),
        ({(CODE, QUARTER): "UNKNOWN"}, "적용여부표를 우리가 못 읽었다"),
        ({(CODE, QUARTER): "NA"}, "원문이 `-` 를 인쇄했다 — 미적용의 진술이 아니라 진술의 부재"),
    ],
)
def test_absent_without_evidence_is_review_never_a_pass(tfi, why):
    """**근거가 없으면 통과가 아니다 — review 로 인쇄하고 센다.**

    이 시험이 이 룰의 안전장치다. 사이드카가 사라지거나 스키마가 바뀌면 부재 RED 가
    조용히 0 이 되는 게 아니라 review 카운트가 튀어야 한다. `NA` 를 `X` 와 같게 보지
    않는 것도 여기서 못 박는다 — `-` 는 "적용 안 함" 이 아니라 "안 적었음" 이고, 모르는
    값을 X 로 추정하는 순간 이 룰은 검사가 아니라 면제 발급기가 된다."""
    f = _findings(_mk(_ABSENT), tfi=tfi)[CENSUS]
    assert f["status"] == STATUS_YELLOW, f"{why} → review 여야 하는데 {f['status']} 다"
    assert f["status"] not in (STATUS_GREEN, STATUS_SKIP), (
        f"{why} 인데 통과 취급됐다 — 근거 없는 통과가 이 저장소의 false-green 형태다")
    assert "TIER2_TABLE_ABSENT_APPLICABILITY_UNKNOWN" in f["detail"]


def test_tfi_x_is_not_a_blanket_amnesty_when_the_issuer_prints_it_anyway():
    """**TFI=X 를 무조건 면죄부로 쓰지 않는다.**

    전수 실측: TFI=X 108버킷 중 **93버킷이 47/48/49 를 갖고 있다**(P(부재|X)=13.9%).
    즉 X 는 "표를 안 그린다"를 함의하지 않는다 — 하나손해는 13분기 전부 X 인데 12분기가
    표를 인쇄한다(2023.2Q raw: "해당사항 없음" 문장 **뒤에** 적용전 컬럼만 채운 표를
    그린다). 그런 발행사에서는 X 가 이 분기의 부재를 설명하지 못하므로 SKIP 이 아니라
    review 로 내려간다. 이 가지가 없으면 X 하나로 26칸이 통째로 사면된다."""
    recs = _mk(BASE, quarter="2025.4Q") + _mk(_ABSENT, quarter="2026.1Q")
    tfi = {(CODE, "2025.4Q"): "X", (CODE, "2026.1Q"): "X"}
    f = _findings_q(recs, "2026.1Q", tfi=tfi)[CENSUS]
    assert f["status"] == STATUS_YELLOW, (
        "같은 회사가 다른 TFI=X 분기에는 표를 인쇄하는데 이 분기 부재를 정상으로 단정했다")
    assert "TIER2_TABLE_ABSENT_TFI_X_INCONSISTENT" in f["detail"]

    # 반례: 그 회사가 X 분기에 한 번도 표를 안 그렸으면 그냥 정상 부재다.
    recs2 = _mk(_ABSENT, quarter="2025.4Q") + _mk(_ABSENT, quarter="2026.1Q")
    f2 = _findings_q(recs2, "2026.1Q", tfi=tfi)[CENSUS]
    assert f2["status"] == STATUS_SKIP
    assert "TIER2_TABLE_ABSENT_TFI_NOT_APPLIED" in f2["detail"]


def test_absence_verdict_is_applied_to_the_post_column_too():
    """적용후 컬럼도 **같은 판정**을 받는다. 적용후가 이 저장소의 최대 검증 사각이었다."""
    for tfi_val, expect in (("O", STATUS_RED), ("X", STATUS_SKIP),
                            ("UNKNOWN", STATUS_YELLOW)):
        f = _findings(_mk(_ABSENT, _ABSENT), tfi={(CODE, QUARTER): tfi_val})[CENSUS_POST]
        assert f["status"] == expect, (
            f"적용후 TFI={tfi_val} 판정이 {f['status']} 다 — 적용전과 갈라지면 "
            "한 컬럼만 검사하는 옛 사각으로 되돌아간다")


# ---------------------------------------------------------------------------
# 9. TFI 표 자신의 기본자본/보완자본(50/51) 축 — 2026-08-22 설계결손 2건 수정분
#
# 이 두 축은 2026-08-22 에 코리안리 7버킷만 보고 설계됐다. parser 가 431버킷을 백필하자
# 적용전 67 · 적용후 60 = **127칸이 RED** 로 터졌는데, 전수 분해 결과 데이터 오염은 0건이고
# 전부 룰 커버리지 결손이었다:
#
#   ① 축 F 가 min(47,48)+49 만 무조건 검사했다 — 형제 룰 `3_tier2_composition` 이 **이미
#      갖고 있던** CAPPED/UNCAPPED/TFI_NA 갈래를 안 가져왔다. 코리안리 7버킷이 우연히 전부
#      CAPPED 계열이라 설계 당시엔 안 보였다. (67 -> 5)
#   ② 축 E 적용후가 50후+51후 == item1_적용후 를 검사했다 — item1_적용후는 선택 경과조치까지
#      합친 전체결합 스코프다. `48_tier2_limit` 이 하루 전 겪은 것과 같은 스코프 실수다. (60 -> 5)
#
# ②의 수정 방향은 **orchestrator 가 예측한 것과 다르다.** "item1_적용전으로 바꿔라"는
# 지시였는데, 원문이 그것도 반증했다 — IBK연금 FY2026_Q1 p17 은 TFI 표 자신의 지급여력금액
# 행이 857,997 / 938,740 으로 **움직인다**고 인쇄한다. "재분류라 합계 불변"은 코리안리
# 한 회사에서만 참이었다. 그래서 없는 값(item52)을 대신 채우지 않고 범위검사를 건다.
# ---------------------------------------------------------------------------

# 갈래별 대표 (회사,분기) — 전부 실제 필링. item51 을 대상으로 `_tier2_branch` 를 돌린
# 결과이고, 같은 47/48/49 로 item3 을 돌려도 같은 갈래가 나오도록 세 행을 공유한다.
TFI_BRANCH_CASES = {
    # 메리츠화재 2023.1Q — min(16,229, 28,473) + 62,604 = 78,833 == item51 78,834
    "CAPPED": {1: 115_146.0, 2: 36_312.0, 3: 78_834.0, 4: 102_196.0, 12: 257.0,
               13: 65_626.0, 14: 56_947.0, 47: 16_229.0, 48: 28_473.0, 49: 62_604.0,
               50: 36_312.0, 51: 78_834.0},
    # 예별손해 2023.1Q — item51 2,390.38 == item47 그대로(한도로 안 잘림).
    # **2026-08-24: 갈래 이름이 `UNCAPPED` → `I49_IN_I47_UNCAPPED` 로 바뀌었다.** 이 필링은
    # item47(2,390.38) 이 item49(1,506.13) 를 **포함**해서 인쇄된 것이고(채무성 884.25 가
    # 한도 5,209.97 에 안 걸린다), 스코프 인식 전에는 그 사실이 `UNCAPPED` 라는 이름 아래
    # 뭉개져 있었다. 값은 한 자리도 안 바꿨다 — 같은 원문을 정확한 이름으로 부를 뿐이다.
    "I49_IN_I47_UNCAPPED": {
        1: 6_774.0, 2: 4_384.0, 3: 2_390.0, 4: 5_890.0, 12: 0.0,
        13: 1_506.0, 14: 10_420.0, 47: 2_390.38, 48: 5_209.97, 49: 1_506.13,
        50: 4_383.5, 51: 2_390.38},
    # 삼성생명 2023.4Q — item51 70,685.30 == item47 인데 **INCL 읽기도 성립하지 않는다**
    # (채무성 50,930.02 < 한도 121,948.24 라 INCL 은 70,685.30 을 내지만, 이 회사는 자기
    # 다른 분기들이 EXCL 로 갈려 CONFLICT → 종전 관행 EXCL 로 판정된다). 그래서 순수
    # `UNCAPPED` 갈래가 실데이터에 살아 있다. 이 케이스가 사라지면 갈래가 죽은 것이므로
    # 아래 falsifiability 시험이 그 사실을 드러낸다.
    "UNCAPPED": {1: 533_725.0, 2: 463_040.0, 3: 70_685.0, 4: 503_744.0, 12: 20_320.0,
                 13: 20_384.0, 14: 243_896.0, 47: 70_685.3, 48: 121_948.24,
                 49: 19_755.28, 50: 463_039.8, 51: 70_685.3},
    # 예별손해 2023.2Q — 초과액도 item49 도 0 이라 두 식이 같은 값을 낸다
    "BOTH": {1: 6_284.0, 2: 3_722.0, 3: 2_562.0, 4: 5_349.0, 12: 0.0,
             13: 1_627.0, 14: 10_120.0, 47: 2_561.95, 48: 5_060.0, 49: 0.0,
             50: 3_722.31, 51: 2_561.95},
    # 메트라이프 2023.1Q — 세 행이 전부 0(표 미기재). 대체 항등식 item51 8,080.59 == item13 8,081
    "TFI_NA_OK": {1: 48_757.0, 2: 40_676.0, 3: 8_081.0, 4: 48_760.0, 12: 4.0,
                  13: 8_081.0, 14: 15_642.0, 47: 0.0, 48: 0.0, 49: 0.0,
                  50: 40_676.29, 51: 8_080.59},
}

# 스코프 판정용 **형제 분기**. 갈래에 따라 같은 회사의 다른 분기가 있어야 재현되는 것이 있다.
#
# `_tier2_i47_scope_map` 은 회사별 투표라 **한 버킷만 넣으면 그 버킷이 곧 회사 관행**이 된다.
# 순수 `UNCAPPED`(= EXCL 관행인데 한도로 안 잘림)는 실데이터에서 CONFLICT 회사에만 남아
# 있으므로, 합성으로 재현하려면 같은 회사에 EXCL 표를 찍는 분기를 하나 같이 넣어야 한다.
# 그게 없으면 이 갈래는 `I49_IN_I47_UNCAPPED` 로 분류되고 시험은 자기가 뭘 검사하는지 모른 채
# 통과한다. **아래 값은 하나손해(KR0050) 2025.4Q 실제 필링이다** — min(1,019.98, 2,168.58)
# + 3,963.97 = 4,983.95 로 EXCL 읽기만 성립한다.
_EXCL_SIBLING_QUARTER = "2025.4Q"
_EXCL_SIBLING = {3: 4_984.0, 14: 4_337.0, 47: 1_019.98, 48: 2_168.58, 49: 3_963.97}
_NEEDS_EXCL_SIBLING = frozenset({"UNCAPPED"})


def _mk_branch_case(branch: str, over: dict | None = None) -> list[dict]:
    """갈래 대표 버킷 + (필요하면) 스코프를 정하는 형제 분기."""
    rows = _mk(_base_of(TFI_BRANCH_CASES[branch], over or {}))
    if branch in _NEEDS_EXCL_SIBLING:
        rows += _mk(_EXCL_SIBLING, quarter=_EXCL_SIBLING_QUARTER)
    return rows


def _branch_findings(branch: str, over: dict | None = None) -> dict[str, dict]:
    return _findings_q(_mk_branch_case(branch, over), QUARTER)


@pytest.mark.parametrize("branch", sorted(TFI_BRANCH_CASES))
def test_tfi_composition_reuses_the_sibling_branch_instead_of_flagging(branch):
    """이식 전에는 이 네 갈래 중 CAPPED/BOTH 만 통과했다 — 나머지 62칸이 오탐이었다.

    통과 사유에 갈래 이름이 박혀야 한다. 안 박히면 게이트 출력만 보고 '무검사'와 구별할 수 없다."""
    found = _branch_findings(branch)
    assert found[TCOMP]["status"] == STATUS_GREEN, (
        f"{branch} 갈래가 여전히 RED 다 — 갈래 이식이 축 F 에 안 걸렸다")
    # **정확 일치로 읽는다.** `"branch=CAPPED" in detail` 은 `branch=I49_IN_I47_CAPPED` 도
    # 참으로 만든다 — 부분문자열 판독이 두 갈래를 한 이름으로 뭉개는 함정이다.
    assert _branch_of(found[TCOMP]["detail"]) == branch, (
        f"갈래 이름이 {branch} 가 아니라 {_branch_of(found[TCOMP]['detail'])!r} 다")


@pytest.mark.parametrize("branch", sorted(TFI_BRANCH_CASES))
def test_every_tfi_composition_branch_is_falsifiable(branch):
    """**핵심 시험.** 갈래마다 item51 을 흔들면 그 갈래 안에서도 RED 가 나야 한다.

    이식했더니 전부 자동 통과한다면 그건 검사가 아니라 면제다. 어제 `48_tier2_limit` 이
    로더 강제라 증거력을 잃은 것과 같은 실패양식을 갈래 단위로 막는다."""
    found = _branch_findings(branch, {51: TFI_BRANCH_CASES[branch][51] + 9_999.0})
    assert found[TCOMP]["status"] == STATUS_RED, (
        f"{branch} 갈래에서 item51 을 9,999 흔들었는데 통과했다 — 갈래가 면제가 됐다")


@pytest.mark.parametrize("branch", sorted(TFI_BRANCH_CASES))
def test_tfi_composition_checks_its_own_inputs_not_only_the_target(branch):
    """대상 셀만 흔들어 보는 시험은 '입력이 검사된다'를 증명하지 못한다.

    TFI_NA 갈래는 47/48/49 가 전부 0 인 것이 갈래의 정의라 세 행을 흔들면 갈래 자체가
    바뀐다(그래도 통과하면 안 된다). 나머지 갈래는 47 을 흔들면 재현이 깨져야 한다."""
    found = _branch_findings(branch, {47: TFI_BRANCH_CASES[branch][47] + 9_999.0})
    assert found[TCOMP]["status"] == STATUS_RED


@pytest.mark.parametrize("branch", sorted(TFI_BRANCH_CASES))
def test_both_composition_axes_agree_on_the_branch_and_the_status(branch):
    """**두 축이 갈라지지 않는다는 것을 기계로 못 박는다.**

    47/48/49 를 공유하고 item3 == item51 로 맞추면 축 B 와 축 F 는 같은 갈래·같은 status 를
    내야 한다. 갈라지면 `_tier2_branch` 를 한쪽만 고쳤거나 status 매핑이 복제됐다는 뜻이다 —
    이름이 같은 갈래가 다른 뜻을 갖는 순간 실패시킨다."""
    found = _branch_findings(branch, {3: TFI_BRANCH_CASES[branch][51]})
    assert found[COMP]["status"] == found[TCOMP]["status"], (
        f"{branch}: axis B={found[COMP]['status']} vs axis F={found[TCOMP]['status']} 갈라졌다")
    # 갈래 이름도 정확 일치로 비교한다 — 접두사가 겹치는 이름끼리 뭉개지면 두 축이 다른
    # 갈래로 갔는데도 통과한다(2026-08-24 스코프 갈래 신설 때 실제로 밟을 뻔한 함정).
    assert _branch_of(found[COMP]["detail"]) == _branch_of(found[TCOMP]["detail"]), (
        f"axis B 는 {_branch_of(found[COMP]['detail'])!r} 인데 "
        f"axis F 는 {_branch_of(found[TCOMP]['detail'])!r} 로 갔다")


def test_tfi_composition_still_reds_the_issuer_inconsistent_cells():
    """갈래를 늘린 것이 면제가 아니라는 **실데이터 대조군.** 롯데손해 2024.4Q 는 표 자신의
    보완자본 28,030.38 이 min(8,699.48, 10,846.63) + 19,333.91 = 28,033.39 도, item47 도
    재현하지 못한다 — 갈래 이식 후에도 RED 로 남는 5칸 중 하나다."""
    lotte = {1: 27_301.0, 2: -730.0, 3: 28_030.0, 4: 19_095.0, 12: 19.0, 13: 19_806.0,
             14: 21_693.0, 47: 8_699.48, 48: 10_846.63, 49: 19_333.91,
             50: -729.57, 51: 28_030.38}
    found = _findings(_mk(lotte))
    assert found[TCOMP]["status"] == STATUS_RED
    assert "TFI_COMPOSITION_NEITHER" in found[TCOMP]["detail"]


# --- 축 E 적용후: 등식이 아니라 범위검사 -------------------------------------

# IBK연금 FY2026_Q1. raw p17 "1) 공통적용 경과조치 관련"(백만원):
#     지급여력금액   857,997 / 938,740   <- **표 자신의 합계 행이 움직인다**
#       기본자본     157,463 / 157,463
#       보완자본     700,535 / 781,277
#     지급여력기준금액 719,585 / 719,585  <- 요구자본은 안 움직인다(축 D 의 근거)
# 마스터 item1 은 8,580(전) / 10,526(후). 후자는 선택 경과조치까지 합친 전체결합이라
# TFI 단독 합계 9,387.40 과 다른 것이 **정상**이다.
IBK_PRE = {1: 8_580.0, 2: 1_575.0, 3: 7_005.0, 4: 6_386.0, 12: 811.0, 13: 4_214.0,
           14: 7_196.0, 47: 4_405.35, 48: 3_597.92, 49: 3_407.42,
           50: 1_574.63, 51: 7_005.35}
IBK_POST = {1: 10_526.0, 47: 2_800.56, 48: 3_597.92, 49: 3_407.42,
            50: 1_574.63, 51: 7_812.77}


def test_post_split_does_not_red_a_legitimate_tfi_mover():
    """**결손 ② 의 대조군.** 이전 식(50후+51후 == item1_적용후)에서 이 버킷은 RED 였고,
    orchestrator 가 지시한 대체식(== item1_적용전)에서도 RED 다(9,387.40 vs 8,580).
    둘 다 원문에 반증된다 — 위 raw 가 표 자신의 합계 행이 움직인다고 인쇄한다."""
    found = _findings(_mk(IBK_PRE, IBK_POST))
    assert found[SPLIT_POST]["status"] != STATUS_RED
    # 그렇다고 GREEN 도 아니다 — 등식의 비교 대상(item52)이 없어 약한 검사만 통과했다
    assert found[SPLIT_POST]["status"] == STATUS_YELLOW
    assert "TFI_TIER_SPLIT_RANGE_ONLY" in found[SPLIT_POST]["detail"]
    assert "item52" in found[SPLIT_POST]["detail"], "발주 대상이 detail 에 안 남으면 잊힌다"


@pytest.mark.parametrize("delta", [+9_999.0, -9_999.0])
def test_post_split_range_is_not_vacuous(delta):
    """범위검사가 검사인지 확인한다 — 범위 밖으로 밀면 RED 여야 한다.
    범위가 아무리 넓어도 '무엇을 넣어도 통과'면 그건 면제다."""
    mutated = _base_of(IBK_POST, {50: IBK_POST[50] + delta})
    found = _findings(_mk(IBK_PRE, mutated))
    assert found[SPLIT_POST]["status"] == STATUS_RED
    assert "TFI_TIER_SPLIT_OUT_OF_RANGE" in found[SPLIT_POST]["detail"]


def test_post_split_collapses_to_an_equality_when_item1_does_not_move():
    """경과조치 효과가 헤드라인에 안 나타나는 버킷(실측 362칸, 84%)에서는 범위가 한 점으로
    붕괴해 **등식과 같은 강도**로 검사된다. 범위검사가 전면 완화가 아님을 못 박는다.

    코리안리 2023.2Q 실측: item1 37,414(전) / 37,413.58(후), 50후+51후 = 37,413.58."""
    pre = {1: 37_414.0, 2: 32_204.0, 3: 5_209.0, 4: 37_414.0, 12: 0.0, 13: 5_209.0,
           14: 19_665.0, 47: 6_167.44, 48: 9_832.38, 49: 24.99,
           50: 31_221.14, 51: 6_192.43}
    post = {1: 37_413.58, 47: 581.39, 48: 9_832.38, 49: 24.99,
            50: 32_204.38, 51: 5_209.20}
    found = _findings(_mk(pre, post))
    assert found[SPLIT_POST]["status"] == STATUS_GREEN
    assert "한 점으로 붕괴" in found[SPLIT_POST]["detail"]
    # 붕괴한 상태에서 흔들면 RED — 등식과 같은 강도임을 증명한다
    shaken = _findings(_mk(pre, _base_of(post, {51: post[51] + 5.0})))
    assert shaken[SPLIT_POST]["status"] == STATUS_RED


def test_post_split_reds_the_real_kyobo_defect():
    """교보생명 2023.3Q 실측 — item51_적용후 가 0.10 으로 읽혔다(적용전은 41,915.04 이고
    같은 컬럼 47/48/49 로 재현해도 41,915.04). item1 이 전=후 라 범위가 붕괴하고 RED 다.

    범위검사로 바꾼 뒤에도 **진짜 결함은 그대로 잡힌다** — 이 축이 면제가 되지 않았다는 증거."""
    pre = {1: 147_914.0, 2: 105_999.0, 3: 41_915.0, 4: 108_350.0, 12: 2_351.0,
           13: 41_915.0, 14: 80_727.0, 47: 27_623.07, 48: 40_363.63, 49: 14_291.97,
           50: 105_998.86, 51: 41_915.04}
    post = {1: 147_914.0, 47: 27_623.07, 48: 40_363.63, 49: 14_291.97,
            50: 105_998.86, 51: 0.10}
    found = _findings(_mk(pre, post))
    assert found[SPLIT_POST]["status"] == STATUS_RED
    assert "TFI_TIER_SPLIT_OUT_OF_RANGE" in found[SPLIT_POST]["detail"]


def test_post_split_skips_with_a_reason_when_the_range_bound_is_missing():
    """범위의 하한은 item1_적용전이다. 없으면 **폴백하지 않고** 사유를 붙여 SKIP 한다 —
    적용후 값으로 하한을 메우면 범위가 한 점이 되어 통과도 실패도 무의미해진다."""
    pre_no_i1 = {k: v for k, v in IBK_PRE.items() if k != 1}
    found = _findings(_mk(pre_no_i1, IBK_POST))
    assert found[SPLIT_POST]["status"] == STATUS_SKIP
    assert "TFI_TIER_SPLIT_INPUT_MISSING" in found[SPLIT_POST]["detail"]


def test_pre_split_stays_an_equality_and_is_still_falsifiable():
    """적용전은 범위가 아니라 **등식**이다(실측 429/431). 완화는 적용후에만 했다."""
    assert _findings(_mk(IBK_PRE))[SPLIT]["status"] == STATUS_GREEN
    assert _status(_mk(_base_of(IBK_PRE, {50: IBK_PRE[50] + 5.0})), SPLIT) == STATUS_RED
    assert _status(_mk(_base_of(IBK_PRE, {51: IBK_PRE[51] + 5.0})), SPLIT) == STATUS_RED
    assert _status(_mk(_base_of(IBK_PRE, {1: IBK_PRE[1] + 5.0})), SPLIT) == STATUS_RED


def test_pre_split_records_that_the_loader_shares_this_formula():
    """통과가 절반만 증거라는 사실을 detail 에 남긴다. parser 백필이 배율을 이 식의 2% 밴드로
    고르고 잔차가 max(5%, 5.0억) 을 넘으면 아예 안 싣는다 — 다음 사람이 GREEN 을 완전한
    증거로 읽지 않게 그 한계를 게이트 출력에 박아 둔다."""
    assert "LOADER_ENFORCED" in _findings(_mk(IBK_PRE))[SPLIT]["detail"]
