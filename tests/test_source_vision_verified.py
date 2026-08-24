# -*- coding: utf-8 -*-
"""원천 육안판독 근거 원장(`kics_source_vision_verified.json`)의 **변이시험**.

## 왜 이 파일이 있나

`SOURCE_UNREADABLE_NOT_VERIFIED` 는 "raw 텍스트레이어가 깨져 판정 불가" 를 뜻하는 YELLOW 다.
2026-08-24 에 그 20칸 전부를 렌더링 육안으로 판독해 "발행사가 경과조치를 적용하지 않았다" 를
원문에서 확인했고, 그 판정을 원장에 등재해 게이트가 소비하게 했다.

**등재는 이 저장소에서 가장 위험한 코드다.** 한 번 등재되면 그 칸은 아무도 안 본다 — 그게
`docs/postmortems/` 가 반복해서 기록한 실패모드이고, 그래서 이 원장은 '끄기' 가 아니라
**주장 + 박제값의 매 실행 재검산**이다. 그 재검산이 실제로 도는지를 여기서 흔들어 증명한다.
증명이 없으면 등재는 blanket skip 과 구별되지 않는다.

흔드는 네 축:
  ① 필수 필드를 지우면 `SOURCE_VISION_RECORD_INCOMPLETE` RED
  ② 박제 셀이 마스터에서 사라지면 `SOURCE_VISION_INPUT_MISSING` RED (결측은 SKIP 이 아니다)
  ③ 등재 주장(적용후 = 적용전)이 깨지면 `SOURCE_VISION_CLAIM_REFUTED` RED
  ④ 박제값이 움직이면 `SOURCE_VISION_PIN_DRIFT` YELLOW (주장은 서 있으므로 비차단)
그리고 통과할 때도 **조용해지지 않는다** — `SOURCE_VISION_VERIFIED` review 로 판독자·판독일·
페이지·인쇄된 문구를 매 실행 인쇄한다.
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

import validate_data_contract as dc  # noqa: E402

MASTER = ROOT / "kics_disclosure.json"
LEDGER = ROOT / "data" / "_gold" / "kics_source_vision_verified.json"


@pytest.fixture(scope="module")
def records():
    raw = json.loads(MASTER.read_text(encoding="utf-8"))
    return raw["records"] if isinstance(raw, dict) else raw


@pytest.fixture(scope="module")
def ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _rules(out):
    return {r for _sev, r, _m in out}


def _entry(ledger, code, quarter):
    return copy.deepcopy(dc._source_vision_index(ledger)[(code, quarter)])


def test_the_ledger_exists_and_is_loaded_by_the_same_loader_the_gate_uses():
    """게이트가 읽는 것 = 내가 시험하는 것. 다르면 시험이 다른 파일을 보고 통과한다."""
    assert dc.SOURCE_VISION_LEDGER == LEDGER
    loaded = dc._load_source_vision_ledger()
    assert isinstance(loaded, dict) and loaded.get("entries"), "원장이 안 읽힌다"


def test_a_missing_ledger_falls_back_to_unverified_not_to_pass(tmp_path, monkeypatch):
    """**파일이 사라지면 조용히 통과가 아니라 조용히 미판독으로 돌아간다.**

    stale/소실 사이드카가 '검증됐다' 를 주장하는 경로가 이 저장소의 반복 사고형태다."""
    monkeypatch.setattr(dc, "SOURCE_VISION_LEDGER", tmp_path / "nope.json")
    assert dc._load_source_vision_ledger() is None
    assert dc._source_vision_index(None) == {}


def test_every_registered_entry_passes_on_the_live_master(records, ledger):
    """등재분 전건이 지금 마스터에서 재검산을 통과한다 — 통과 사유는 VERIFIED 하나뿐이다."""
    for (code, q), e in sorted(dc._source_vision_index(ledger).items()):
        out = dc._source_vision_findings(e, records, 17, "UNREADABLE")
        assert _rules(out) == {"SOURCE_VISION_VERIFIED"}, f"{code} {q}: {out}"


def test_a_verified_entry_never_goes_quiet(records, ledger):
    """통과해도 인쇄된다. 조용해지면 다음 세션이 '검사된 칸' 으로 오독한다.

    인쇄줄에는 **판독자·판독일·페이지·인쇄된 문구**가 다 들어가야 한다 — 하나라도 빠지면
    다음 사람이 근거를 다시 찾을 수 없다."""
    e = _entry(ledger, "KR0079", "2025.1Q")
    (sev, rule, msg), = dc._source_vision_findings(e, records, 17, "UNREADABLE")
    assert (sev, rule) == ("YELLOW", "SOURCE_VISION_VERIFIED")
    for token in (e["read_by"], e["read_date"], e["pdf"], str(e["pages_0idx"])):
        assert token in msg, f"인쇄줄에 {token!r} 가 없다: {msg}"
    assert e["printed_quote"][:30] in msg, "인쇄된 원문 문구가 리포트에 안 실린다"
    assert str(e.get("reproduced_by_sender")) in msg, (
        "판독 깊이(sender 재현 여부)가 안 찍힌다 — parser 판독만 있는 것과 원 sender 가 "
        "재현한 것은 근거 강도가 다르다")


@pytest.mark.parametrize("field", list(dc.SOURCE_VISION_REQUIRED))
def test_dropping_any_required_field_is_red(records, ledger, field):
    """판독자·판독일·본 페이지·인쇄된 문구가 없으면 '누군가 확인했다' 는 산문과 같다."""
    e = _entry(ledger, "KR0080", "2025.1Q")
    e.pop(field, None)
    out = dc._source_vision_findings(e, records, 19, "UNREADABLE")
    assert _rules(out) == {"SOURCE_VISION_RECORD_INCOMPLETE"}, f"{field}: {out}"
    assert all(sev == "RED" for sev, _r, _m in out)


@pytest.mark.parametrize("item", ["1", "14", "17", "19", "27"])
def test_breaking_the_claim_is_red(records, ledger, item):
    """등재 주장은 '경과조치 미적용 → 적용후 = 적용전' 이다.

    박제한 항목 중 **어느 하나라도** 전≠후가 되면 그 주장이 깨진 것이므로 RED 다.
    항목을 하나만 걸면 나머지가 조용히 오염될 수 있어 다섯 개를 각각 흔든다."""
    e = _entry(ledger, "KR0087", "2026.1Q")
    mutated = copy.deepcopy(records)
    hit = 0
    for r in mutated:
        if (r.get("원보험사코드") == "KR0087" and r.get("공시분기") == "2026.1Q"
                and str(r.get("항목번호")) == item):
            r["값_적용후"] = str(float(str(r["값"]).replace(",", "")) + 777.0)
            hit += 1
    assert hit, f"item{item} 셀을 못 찾았다"
    out = dc._source_vision_findings(e, mutated, 17, "UNREADABLE")
    assert "SOURCE_VISION_CLAIM_REFUTED" in _rules(out), out
    assert any(sev == "RED" and r == "SOURCE_VISION_CLAIM_REFUTED" for sev, r, _m in out)


def test_a_value_drift_that_keeps_the_claim_is_yellow_not_silent(records, ledger):
    """값이 움직였는데 전=후는 유지되는 경우 — 판독은 옛 숫자에 대해 한 것이라 재판독 대상이다.

    주장 자체가 깨진 것은 아니므로 차단하지 않는다(이 축은 원래 YELLOW 다). 그러나 **조용히
    통과시키지도 않는다** — 그러면 등재가 값 변화를 못 보는 blanket skip 이 된다."""
    e = _entry(ledger, "KR0010", "2025.3Q")
    mutated = copy.deepcopy(records)
    hit = 0
    for r in mutated:
        if (r.get("원보험사코드") == "KR0010" and r.get("공시분기") == "2025.3Q"
                and str(r.get("항목번호")) == "19"):
            new = str(float(str(r["값"]).replace(",", "")) + 500.0)
            r["값"], r["값_적용후"] = new, new      # 전=후는 유지한 채 값만 이동
            hit += 1
    assert hit, "item19 셀을 못 찾았다"
    out = dc._source_vision_findings(e, mutated, 19, "UNREADABLE")
    assert _rules(out) == {"SOURCE_VISION_PIN_DRIFT"}, out
    assert all(sev == "YELLOW" for sev, _r, _m in out)


def test_a_missing_pinned_cell_is_red_not_skip(records, ledger):
    """결측은 SKIP 이 아니다 — 판독 근거가 가리키는 값이 없으면 등재는 무효다."""
    e = _entry(ledger, "KR0080", "2025.3Q")
    mutated = [r for r in records
               if not (r.get("원보험사코드") == "KR0080" and r.get("공시분기") == "2025.3Q"
                       and str(r.get("항목번호")) == "27")]
    out = dc._source_vision_findings(e, mutated, 17, "UNREADABLE")
    assert "SOURCE_VISION_INPUT_MISSING" in _rules(out), out
    assert any(sev == "RED" and r == "SOURCE_VISION_INPUT_MISSING" for sev, r, _m in out)


def test_the_axis_is_actually_wired_not_only_defined():
    """**'배선했다' 와 '실제로 강제된다' 는 다른 말이다** (이 저장소의 명문화된 교훈).

    위 시험들은 전부 순수함수를 부른다 — 게이트 본문이 그 함수를 안 부르면 전부 통과하면서도
    아무것도 검사되지 않는다. 그래서 호출 지점 자체를 소스에서 확인한다."""
    src = (ROOT / "scripts" / "validate_data_contract.py").read_text(encoding="utf-8")
    assert "_source_vision_findings(entry, kd_records" in src, (
        "SOURCE_UNREADABLE_NOT_VERIFIED 축이 원장을 소비하지 않는다 — 원장이 죽은 파일이다")
    assert "SOURCE_VISION_INERT" in src, (
        "죽은 핀 감지(INERT)가 사라졌다 — 무용해진 등재가 조용히 남는다")


def test_the_ledger_records_how_deeply_each_entry_was_read(ledger):
    """판독 깊이를 뭉개지 않는다.

    `VERIFIED` / `VERIFIED_BY_IMAGE` / `VERIFIED_BY_OWNER` 를 갈라 놓은 것과 같은 이유다 —
    한 단어 아래 서로 다른 강도의 근거가 섞이면 다음 세션이 전부 같은 것으로 읽는다.
    등재분에는 **원 sender 가 직접 재현한 항목이 회사마다 최소 하나** 있어야 한다."""
    allowed = set(ledger["_reproduced_by_sender_values"])
    by_company: dict[str, set] = {}
    for e in ledger["entries"]:
        d = e.get("reproduced_by_sender")
        assert d in allowed, f"{e['company']} {e['quarter']}: 알 수 없는 판독 깊이 {d!r}"
        by_company.setdefault(e["company"], set()).add(d)
    for code, depths in sorted(by_company.items()):
        assert "yes" in depths, (
            f"{code}: 원 sender 가 직접 재현한 분기가 하나도 없다 — 회사마다 최소 한 분기는 "
            "직접 열어야 서식 추론이 근거를 대체하지 않는다")
