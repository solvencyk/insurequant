# -*- coding: utf-8 -*-
"""부재형 면제 = **셀 단위 부재 박제** + 원장↔코드 박제 대조 + 마커 행 귀속 (2026-08-24 신설).

## 이 파일이 막는 사고

`docs/postmortems/PM-2026-08-24_absence_exemption_blinded_axis.md` 의 재발 방지다.

종전 `_AFTER_SUBRISK_NOT_DISCLOSED` 는 `(회사,분기)` 집합이었고 `_transition_mmult_after` 가
**부모 조회 전에** `continue` 했다. 그래서 하나생명 2024.4Q 는 mmult 3축(15·17·19)과
부모-자식 census · 분산효과 적용후가 통째로 순회 대상이 아니었고, 그 사각에서 `item33후`·
`item34후` 가 직전분기 값 복사(stale)로 앉아 있었다. 실측 증거: 그 4셀을 정정 전 값으로
되돌린 마스터로 게이트를 돌려도 출력이 **바이트 동일**했다 = 값이 바뀌어도 게이트가 모른다.

여기서 시험하는 명제는 셋이다:

  ① 면제는 축을 순회에서 빼지 않는다 — 박제된 셀이 **채워지면** 축이 되살아나 검산한다.
  ② 박제 그룹이 **부분충전**이면 RED 다 — 섞인 상태는 항등식을 입력결측 SKIP 으로 만들어
     채워진 값이 아무 검사도 안 받게 한다(이 사고가 정확히 그 상태였다).
  ③ 원장의 박제 숫자는 **코드 박제의 사본**이고, 어긋나면 RED 다. 그 전까지 원장
     `expected_residual` 을 읽는 코드가 하나도 없어서 원장은 장식이었다.

## 합성이 아니라 라이브 마스터·라이브 원장을 쓴다

면제는 실제 등재분에 대해서만 의미가 있다. 합성 픽스처로 시험하면 "코드가 돈다" 만 보이고
"등재된 버킷이 실제로 재검산된다" 는 안 보인다 — 그 구분이 정확히 false-green 의 자리다.
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
    KEY_VALUE_POST,
)


@pytest.fixture(scope="module")
def records():
    raw = json.loads(MASTER.read_text(encoding="utf-8"))
    return raw["records"] if isinstance(raw, dict) else raw


@pytest.fixture(scope="module")
def ledger():
    return gate._load_exemption_ledger()


def _drop_post(records, code, quarter, items):
    out = copy.deepcopy(records)
    hit = 0
    for r in out:
        if r.get(KEY_CODE) != code or r.get(KEY_QUARTER) != quarter:
            continue
        try:
            it = int(r.get(KEY_ITEM))
        except (TypeError, ValueError):
            continue
        if it in items:
            r.pop(KEY_VALUE_POST, None)
            hit += 1
    assert hit == len(items), f"{code} {quarter} 에서 {items} 를 다 못 찾았다 (찾은 것 {hit})"
    return out


def _set_post(records, code, quarter, item, value):
    out = copy.deepcopy(records)
    for r in out:
        if r.get(KEY_CODE) != code or r.get(KEY_QUARTER) != quarter:
            continue
        try:
            if int(r.get(KEY_ITEM)) != item:
                continue
        except (TypeError, ValueError):
            continue
        r[KEY_VALUE_POST] = value
        return out
    raise AssertionError(f"셀을 못 찾았다: {code} {quarter} item{item}")


# ---------------------------------------------------------------------------
# 0. 평시 — 라이브 마스터에서 조용해야 한다
# ---------------------------------------------------------------------------
def test_the_absence_pins_are_quiet_on_the_live_master(records):
    _detail, red, _review = gate._absence_pin_census(records)
    assert red == [], f"평시에 부재 박제 RED 가 있으면 등재의 전제가 이미 깨진 것이다: {red}"


def test_the_ledger_agrees_with_the_code_pins_on_the_live_repo():
    red = gate._pin_ledger_agreement_findings()
    assert red == [], (
        "원장과 코드 박제가 어긋난다. 원장 숫자는 코드 박제의 사본이고 둘이 어긋나면 "
        f"원장이 장식이 된다: {red}")


# ---------------------------------------------------------------------------
# 1. **면제가 축을 눈감기지 않는다** — 이 라운드의 수용기준
# ---------------------------------------------------------------------------
def test_a_pinned_absent_cell_that_carries_a_value_is_checked_not_skipped(records):
    """하나생명 2024.4Q 의 29~35후는 원장이 '원천 부재' 라고 하지만 실제로는 파생값이 있다.
    그 값이 있는 한 mmult 축 17 은 **반드시 검산돼야 한다** — 안 그러면 이 사고가 재발한다."""
    mismatch, _sub_missing, skipped, _unver = gate._transition_mmult_after(records)
    exempt_tags = [k for k in skipped if "DOCUMENTED_EXEMPT" in k]
    assert not exempt_tags, (
        "축을 통째로 빼는 면제 태그가 살아 있다 — 부재 박제는 셀 단위여야 한다: " + str(exempt_tags))
    # 값이 완비된 축 17 은 평가돼야 하고(= skipped 에 안 잡히고), 실제로 닫혀야 한다.
    assert not any(k.startswith("item17:SOURCE_ABSENT_PINNED") for k in skipped), (
        "item29~35후가 전부 채워져 있는데 축 17 이 부재 박제로 미판정 처리됐다")
    assert not any(c == "KR0097" and q == "2024.4Q" and p == 17
                   for c, q, _n, p, *_ in mismatch), "정정 후에는 축 17 이 닫혀야 한다"


def test_the_stale_values_that_caused_the_incident_would_now_be_caught(records):
    """사고 재현: item33후·item34후에 직전분기 값이 복사되고 item30후·item35후가 결측이던 상태.

    이건 '부분충전' 이라 mmult 는 여전히 SKIP 이지만 **부재 박제 census 가 RED 를 낸다.**
    종전에는 이 상태에서 게이트 출력이 정상과 바이트 동일했다."""
    bad = _drop_post(records, "KR0097", "2024.4Q", {30, 35})
    bad = _set_post(bad, "KR0097", "2024.4Q", 33, "942.86")
    bad = _set_post(bad, "KR0097", "2024.4Q", 34, "896.15")
    _detail, red, _review = gate._absence_pin_census(bad)
    rules = {r["rule"] for r in red}
    assert "EXEMPTION_ABSENCE_PIN_PARTIAL_FILL" in rules, (
        "사고 당시 상태(박제 7셀 중 5셀만 채워짐)가 RED 로 안 잡힌다 — 게이트가 여전히 눈감는다")
    hit = [r for r in red if r["rule"] == "EXEMPTION_ABSENCE_PIN_PARTIAL_FILL"]
    assert any(r["code"] == "KR0097" and r["quarter"] == "2024.4Q" for r in hit)
    assert any("item30후" in r["detail"] and "item35후" in r["detail"] for r in hit)


def test_a_fully_empty_pinned_group_is_not_red(records):
    """전부 결측 = 원장의 명제 그대로다. 부분충전만 RED 이고 완전부재는 정상이다."""
    ok = _drop_post(records, "KR0097", "2024.4Q", set(range(29, 36)))
    _detail, red, _review = gate._absence_pin_census(ok)
    assert not [r for r in red if r["code"] == "KR0097"], (
        "박제 그룹이 통째로 비어 있는 것은 면제가 지키는 바로 그 상태다 — RED 가 아니다")


def test_the_census_prints_every_pinned_cell_one_by_one(records):
    """조용한 미순회 금지 — 박제된 셀은 결측이든 값이 있든 **한 줄씩** 나와야 한다."""
    detail, _red, _review = gate._absence_pin_census(records)
    cells = {(c, q, it) for _r, c, q, it, *_ in detail}
    for (c, q), items in gate._AFTER_SOURCE_ABSENT_CELLS.items():
        for it in items:
            assert (c, q, it) in cells, f"{c} {q} item{it} 가 census 에 안 나온다"
    for (c, q), items in gate._POST_PARENT_SOURCE_ABSENT_CELLS.items():
        for it in items:
            assert (c, q, it) in cells, f"{c} {q} item{it} 가 census 에 안 나온다"


def test_a_value_appearing_where_the_ledger_says_absent_is_reported(records):
    _detail, _red, review = gate._absence_pin_census(records)
    rules = {r["rule"] for r in review}
    assert "EXEMPTION_ABSENCE_PIN_VALUE_PRESENT" in rules, (
        "원장이 '원천 부재' 라는 셀에 값이 있으면 그 사실 자체가 보고돼야 한다(파생값)")


def test_the_scope_is_cell_level_not_bucket_level():
    """축 15(기본요구자본)는 하나생명 원문 p281 에 여섯 값이 다 있고 실제로 닫힌다.
    (회사,분기) 통째 면제는 그 축까지 근거 없이 사각으로 넣었다(감사 H8)."""
    cells = gate._AFTER_SOURCE_ABSENT_CELLS[("KR0097", "2024.4Q")]
    axis15_inputs = set(range(17, 22))
    assert not (cells & axis15_inputs), (
        "축 15 의 입력(item17~21후)이 부재 박제에 들어가 있다 — 원문이 공시하는 축을 면제하면 안 된다")


# ---------------------------------------------------------------------------
# 2. 원장 ↔ 코드 박제 대조 (변이시험)
# ---------------------------------------------------------------------------
def _ledger_copy(ledger):
    return copy.deepcopy(ledger)


def _entry(led, reg, c, q):
    for e in led["entries"]:
        if (e.get("registry"), e.get("company"), e.get("quarter")) == (reg, c, q) \
                and e.get("status") != "CONTRADICTED":
            return e
    raise AssertionError(f"원장 항목 없음: {reg} {c} {q}")


def test_editing_only_the_ledger_number_is_red(ledger):
    """원장 숫자만 바꿔도 아무 일이 없던 것이 이 라운드 이전 상태였다."""
    led = _ledger_copy(ledger)
    e = _entry(led, "_TIER2_ISSUER_INCONSISTENT", "KR1000", "2023.2Q")
    e["expected_residual"]["3_tier2_composition|적용전"] = -1.0
    red = gate._pin_ledger_agreement_findings(ledger=led)
    assert any(r["rule"] == "EXEMPTION_PIN_LEDGER_DISAGREE" and r["code"] == "KR1000"
               for r in red), "원장 잔차를 흔들었는데 아무 일도 안 일어난다"


def test_dropping_an_axis_from_the_ledger_is_red(ledger):
    """H3 회귀 증거 — KR0075 3분기에서 실제로 어긋나 있던 것이 **축 목록**이었다."""
    led = _ledger_copy(ledger)
    e = _entry(led, "_TIER2_ISSUER_INCONSISTENT", "KR0075", "2024.3Q")
    e["expected_residual"].pop("47_tier2_census_post|적용후")
    red = gate._pin_ledger_agreement_findings(ledger=led)
    assert any(r["code"] == "KR0075" and r["quarter"] == "2024.3Q" and "축 목록" in r["detail"]
               for r in red)


def test_the_historical_h3_key_typo_is_caught(ledger):
    """2026-08-24 이전 원장에 실제로 들어 있던 오탈(`_post` 접미사 누락)을 재현한다."""
    led = _ledger_copy(ledger)
    e = _entry(led, "_TIER2_ISSUER_INCONSISTENT", "KR0075", "2024.3Q")
    er = e["expected_residual"]
    er.pop("47_tier2_census_post|적용후")
    er["47_tier2_census|적용후"] = None          # 존재하지 않는 축 이름
    red = gate._pin_ledger_agreement_findings(ledger=led)
    det = " ".join(r["detail"] for r in red if r["code"] == "KR0075")
    assert "47_tier2_census_post|적용후" in det and "47_tier2_census|적용후" in det, (
        "코드에만/원장에만 있는 축이 양쪽 다 인쇄돼야 어느 쪽이 오탈인지 보인다")


def test_dropping_absent_cells_from_the_ledger_is_red(ledger):
    led = _ledger_copy(ledger)
    e = _entry(led, "_AFTER_SUBRISK_NOT_DISCLOSED", "KR0097", "2024.4Q")
    e.pop("absent_cells")
    red = gate._pin_ledger_agreement_findings(ledger=led)
    assert any("absent_cells" in r["detail"] for r in red), (
        "부재형 면제는 '어느 셀이 원천에 없는가' 가 명제 자체다 — 원장에 없으면 RED")


def test_changing_the_absent_cell_set_is_red(ledger):
    led = _ledger_copy(ledger)
    e = _entry(led, "_POST_PARENT_NOT_DISCLOSED", "KR0049", "2024.3Q")
    e["absent_cells"] = list(range(1, 30))       # claim 보다 넓힌다
    red = gate._pin_ledger_agreement_findings(ledger=led)
    assert any(r["code"] == "KR0049" and "셀집합 불일치" in r["detail"] for r in red)


def test_every_code_pin_is_mapped_for_ledger_comparison():
    """새 박제형 레지스트리를 만들고 `_code_pin_map` 에 안 넣으면 원장 대조를 안 받는다 —
    `_exemption_registries` 와 같은 계약이다."""
    mapped = {reg for reg, _c, _q in gate._code_pin_map()}
    pinned_registries = {
        "_TIER2_ISSUER_INCONSISTENT", "_LIFE8_ISSUER_INCONSISTENT",
        "IRR_DERIVE_ISSUER_INCONSISTENT",
        "_AFTER_SUBRISK_NOT_DISCLOSED", "_POST_PARENT_NOT_DISCLOSED",
    }
    assert pinned_registries <= mapped, f"원장 대조에서 빠진 레지스트리: {pinned_registries - mapped}"


# ---------------------------------------------------------------------------
# 3. 해제된 박제가 조용히 되살아나는 경로 (tripwire)
# ---------------------------------------------------------------------------
def test_a_released_pin_cannot_be_re_registered_silently(ledger):
    """KR0087 2025.2Q `2_tier1_bridge` 는 **우리 룰 결함**으로 해제됐다.
    다시 등재하면 즉시 RED — 한화생명 status=CONTRADICTED tripwire 의 축 단위 판이다."""
    e = _entry(ledger, "_TIER2_ISSUER_INCONSISTENT", "KR0087", "2025.2Q")
    assert "2_tier1_bridge|적용전" in (e.get("contradicted_pins") or {}), (
        "해제 기록이 원장에 없으면 다음 세션이 같은 박제를 다시 넣는다")
    spec = copy.deepcopy(gate._TIER2_ISSUER_INCONSISTENT[("KR0087", "2025.2Q")])
    spec["findings"]["2_tier1_bridge"] = {"flag": "item2 ==", "residual": 1188.0}
    orig = gate._TIER2_ISSUER_INCONSISTENT[("KR0087", "2025.2Q")]
    gate._TIER2_ISSUER_INCONSISTENT[("KR0087", "2025.2Q")] = spec
    try:
        red = gate._pin_ledger_agreement_findings()
    finally:
        gate._TIER2_ISSUER_INCONSISTENT[("KR0087", "2025.2Q")] = orig
    assert any(r["rule"] == "EXEMPTION_PIN_RE_REGISTERED" for r in red), (
        "반증돼 해제된 박제가 코드에 다시 들어와도 아무 일이 안 일어난다")


# ---------------------------------------------------------------------------
# 4. 마커 행 귀속 (verify.present_rows)
# ---------------------------------------------------------------------------
# 캘리브레이션 케이스 — 참 9 / 음성대조 6. 밴드 3.0pt 에서 실측 참 최대 Δ 0.21pt ·
# 거짓 최소 Δ 8.87pt (여유 약 40배). 이 표가 깨지면 밴드를 바꾸기 전에 원인을 먼저 밝혀라.
_Q3_75 = "data/disclosure/FY2024_Q3/raw/KR0075_비엔피파리바카디프생명보험_amended.pdf"
_ANCHOR_CASES = [
    (True, "data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16],
     "보완자본 한도 적용 전", "1,210,705"),
    (True, "data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16],
     "보완자본 한도", "1,210,705"),
    (True, _Q3_75, [15, 16], "보완자본 한도 적용 전", "31,614"),
    (True, _Q3_75, [15, 16], "보완자본", "33,067"),
    (True, "data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf", [16, 17],
     "기본자본", "△165,099"),
    (True, "data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf", [16, 17],
     "지급여력금액", "△165,099"),
    (True, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "기본자본", "8,034"),
    (True, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10],
     "지급여력금액", "25,846"),
    (True, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10],
     "보완자본 한도", "9,385"),
    # --- 음성 대조군: 거짓 귀속 주장은 반증돼야 한다 ---
    (False, "data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16],
     "해약환급금", "1,210,705"),
    (False, _Q3_75, [15, 16], "보완자본 한도", "33,067"),
    (False, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10], "보완자본", "8,034"),
    (False, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10],
     "지급여력금액", "8,034"),
    (False, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10],
     "기본자본", "25,846"),
    (False, "data/disclosure/FY2023_Q1/raw/KR0003_롯데손해보험.pdf", [9, 10],
     "해약환급금", "9,385"),
]


@pytest.mark.parametrize("expect,pdf,pages,row,value", _ANCHOR_CASES)
def test_row_anchor_checker_is_calibrated(expect, pdf, pages, row, value):
    p = ROOT / pdf
    if not p.exists():
        pytest.skip(f"원천 부재: {pdf}")
    hit, delta = gate._row_anchor_check(p, pages, row, value)
    assert hit is expect, (
        f"'{row}' <- {value} : 기대 {expect} / 실제 {hit} (최소Δ {delta}, "
        f"band {gate._ROW_ANCHOR_BAND})")


def test_a_word_run_never_spans_two_rows():
    """최초 구현의 버그 — 버퍼가 행 경계를 넘어 누적되면 서로 다른 행의 조각이 한 라벨로
    '발견' 되고 그 run 의 평균 y 가 행 사이 아무 데나 찍힌다. 실제로 롯데손해 2023.1Q 에서
    `8,034` 를 세 행에 동시 귀속시켰다."""
    words = [(0.0, 100.0, 20.0, 110.0, "보완", 0, 0, 0),
             (0.0, 130.0, 20.0, 140.0, "자본", 0, 1, 0)]
    assert gate._word_runs(words, "보완자본") == [], (
        "30pt 떨어진 두 단어가 한 라벨로 매칭됐다 — 행 제약이 없다")


def test_a_lying_row_marker_is_a_contradiction(ledger):
    """행 귀속 마커에 거짓을 적으면 `EXEMPTION_CITATION_CONTRADICTED` 가 나야 한다."""
    led = _ledger_copy(ledger)
    e = _entry(led, "_TIER2_ISSUER_INCONSISTENT", "KR0087", "2025.2Q")
    if not (ROOT / e["verify"]["file"]).exists():
        pytest.skip("원천 부재")
    e["verify"]["present_rows"] = [{"row": "해약환급금", "value": "1,210,705"}]
    red, _review = gate._exemption_provenance_findings(ledger=led)
    assert any(r["rule"] == "EXEMPTION_CITATION_CONTRADICTED" and r["code"] == "KR0087"
               for r in red), "거짓 행 귀속 주장이 반증되지 않는다"


def test_the_push_blocking_gate_lifts_these_rules_too():
    """**'게이트에 배선했다' 와 '실제로 push 를 막는다' 는 다른 말이다.**

    `validate_kics_disclosure.py` 에만 배선한 룰은 push 를 못 막는다 — 차단 회계의 정본은
    `validate_data_contract.py` 다(`.githooks/pre-push` → `prepush_check.py`). 이 저장소는
    같은 실수를 이미 두 번 했다(CLAUDE.md '게이트는 honor-system 이었다' 절).
    **재구현이 아니라 같은 함수를 위임**하는지도 같이 강제한다 — 두 벌이 되면 한쪽만 깨진다."""
    src = (ROOT / "scripts" / "validate_data_contract.py").read_text(encoding="utf-8")
    assert "_absence_pin_census" in src, "부재 박제 census 가 push 차단 게이트에 없다"
    assert "_pin_ledger_agreement_findings" in src, "원장↔코드 박제 대조가 push 차단 게이트에 없다"
    assert "_AFTER_SOURCE_ABSENT_CELLS" not in src, "부재 박제 레지스트리를 복사했다 — 위임해야 한다"
    assert "_POST_PARENT_SOURCE_ABSENT_CELLS" not in src, "부재 박제 레지스트리를 복사했다"


def test_ambiguous_markers_are_reported_every_run():
    """남은 숫자-only 다중출현 마커는 조용해지면 안 된다 — 무엇이 미검사인지가 사라진다."""
    detail, review = gate._marker_grade_census()
    assert detail, "마커 등급 census 가 비어 있다"
    tot = {k: sum(len(g[k]) for *_x, g in detail)
           for k in ("ANCHORED", "LABELLED", "UNIQUE", "AMBIGUOUS")}
    assert tot["ANCHORED"] > 0, "행 귀속 마커가 하나도 없다"
    if tot["AMBIGUOUS"]:
        assert any(r["rule"] == "EXEMPTION_MARKER_UNANCHORED" for r in review), (
            "AMBIGUOUS 마커가 남아 있는데 review 로 인쇄되지 않는다")
