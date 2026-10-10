# -*- coding: utf-8 -*-
"""`_IDENT_ISSUER_INCONSISTENT` (평문 항등식 룰 2·4·5·6 발행사 자기모순 면제) 의 **변이시험**.

## 왜 이 파일이 있나

2026-10-10 재보사 적재(KR1101~KR1108) 단계 8 에서 owner 가 발행사 자기모순 21건의 등재를 승인했다.
그중 17건이 룰 2(순자산합)·4(기본요구자본 R4)·5(기준금액)·6(분산효과) 인데 이 넷에는 잔차 박제
장치가 없었다. 새 장치는 `_TIER2_ISSUER_INCONSISTENT` 와 같은 **두 겹 박제**다:

  ① `cells`    — 그 항등식의 입력 셀. 움직이면 `IDENT_EXEMPTION_INPUT_DRIFT`, 결측이면 `..._INPUT_MISSING`.
  ② `findings` — "룰|적용전" 은 룰엔진 finding 의 diff, "룰|적용후" 는 거울 축
                 (R2후·R5후·R6후·mmult15후)과 같은 식으로 다시 잰 잔차. 움직이면 `..._RESIDUAL_DRIFT`,
                 그 축이 더는 안 깨지면 `..._INERT`(review).

면제는 '끄기' 가 아니다 — "박제값을 흔들면 RED 가 돌아온다" 를 여기서 셀마다 증명한다.
합성 버킷이 아니라 **라이브 마스터**를 쓴다(등재분이 실제로 재검산되는지가 요점이다).
마스터는 사본도 안 만든다 — 한 칸을 제자리에서 바꾸고 `finally` 로 되돌린다(29k 행 deepcopy 회피).
"""
from __future__ import annotations

import contextlib
import json
import re
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
REG = gate._IDENT_ISSUER_INCONSISTENT

# owner 승인 2026-10-10 범위 그대로 (handoff §7-10 ①, 재보사 단계 6 표 A 의 룰 2·4·5·6 17건).
APPROVED = {
    ("KR1103", "2026.2Q"): {"4", "5", "6"},
    ("KR1104", "2026.2Q"): {"2"},
    ("KR1105", "2025.1Q"): {"2"}, ("KR1105", "2026.1Q"): {"2"}, ("KR1105", "2026.2Q"): {"2"},
    **{("KR1106", q): {"6"} for q in ("2023.1Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q",
                                      "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q")},
}


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


@contextlib.contextmanager
def _cell(records, code, quarter, item, col, new):
    """마스터 한 칸을 제자리에서 바꾸고 반드시 되돌린다. `new=None` 이면 결측."""
    key = COL_KEY[col]
    for r in records:
        if r.get(KEY_CODE) == code and r.get(KEY_QUARTER) == quarter:
            try:
                if int(r.get(KEY_ITEM)) != item:
                    continue
            except (TypeError, ValueError):
                continue
            had, old = key in r, r.get(key)
            if new is None:
                r.pop(key, None)
            else:
                r[key] = new
            try:
                yield
            finally:
                if had:
                    r[key] = old
                else:
                    r.pop(key, None)
            return
    raise AssertionError(f"셀을 못 찾았다: {code} {quarter} item{item} [{col}]")


def _run(recs, finds):
    return gate._ident_issuer_inconsistent(recs, finds)


# ---------------------------------------------------------------------------
# 0. 평시엔 조용하고, 정확히 승인 범위만 면제한다
# ---------------------------------------------------------------------------
def test_registry_is_exactly_the_owner_approved_scope():
    """면제가 **넓어지지 않았다**를 기계로 못 박는다 — 키·룰이 승인 범위와 정확히 같아야 한다.
    늘리려면 owner 승인과 원장(`kics_exemption_provenance.json`) 근거를 같이 고쳐라."""
    got = {k: {key.split("|")[0] for key in spec["findings"]} for k, spec in REG.items()}
    assert got == APPROVED
    assert all(c.startswith("KR11") for c, _q in REG), "기존 39사 버킷이 이 장치에 들어왔다"


def test_every_pin_matches_on_the_live_master(records, findings):
    accepted, red, review, detail = _run(records, findings)
    assert red == [], f"면제 전제가 깨졌다: {red}"
    assert review == [], f"무용해진 면제가 있다: {review}"
    n_pre = sum(1 for s in REG.values() for k in s["findings"] if k.endswith("|적용전"))
    assert len(accepted) == n_pre == 17
    assert all(f.get("status") == "RED" for f in accepted), "면제가 RED 아닌 finding 을 깎는다"
    assert len(detail) == sum(len(s["findings"]) for s in REG.values())


def test_pin_tolerance_stays_tight():
    assert gate.AFTER_IDENT_PIN_TOL <= 0.01


def test_cells_cover_every_input_of_every_pinned_axis():
    """박제 셀이 그 항등식의 입력을 다 덮지 않으면 '데이터가 움직였는가' 를 반쯤만 본다."""
    for (c, q), spec in REG.items():
        for key in spec["findings"]:
            rule, _, col = key.partition("|")
            colkey = "값" if col == "적용전" else "값_적용후"
            for it in gate._IDENT_RULE_INPUTS[rule]:
                assert colkey in spec["cells"].get(it, {}), f"{c} {q} {key}: item{it} [{colkey}] 미박제"


# ---------------------------------------------------------------------------
# 1. 겹 ① — 박제한 셀을 **하나씩 전부** 흔들면 RED 가 돌아온다 (전수 변이)
# ---------------------------------------------------------------------------
_ALL_CELLS = [(c, q, it, col) for (c, q), spec in REG.items()
              for it, cols in spec["cells"].items() for col in cols]


@pytest.mark.parametrize("code,quarter,item,col", _ALL_CELLS)
def test_every_pinned_cell_drift_revives_red(records, findings, code, quarter, item, col):
    pin = REG[(code, quarter)]["cells"][item][col]
    with _cell(records, code, quarter, item, col, pin + 0.02):
        accepted, red, _rev, _det = _run(records, findings)
    assert any(r["rule"] == "IDENT_EXEMPTION_INPUT_DRIFT" and r["code"] == code
               and r["quarter"] == quarter and r.get("item") == item for r in red)
    assert not any(f.get(KEY_CODE) == code and f.get(KEY_QUARTER) == quarter for f in accepted), \
        "전제가 깨진 버킷이 여전히 면제되고 있다"


@pytest.mark.parametrize("code,quarter,item,col", [
    ("KR1103", "2026.2Q", 22, "값"), ("KR1105", "2025.1Q", 4, "값_적용후"), ("KR1106", "2024.4Q", 16, "값")])
def test_a_missing_input_is_red_not_skip(records, findings, code, quarter, item, col):
    with _cell(records, code, quarter, item, col, None):
        _acc, red, _rev, _det = _run(records, findings)
    assert any(r["rule"] == "IDENT_EXEMPTION_INPUT_MISSING" for r in red)


def test_the_whole_bucket_vanishing_is_red(records, findings):
    code, quarter = "KR1104", "2026.2Q"
    kept = [r for r in records if not (r.get(KEY_CODE) == code and r.get(KEY_QUARTER) == quarter)]
    _acc, red, _rev, _det = _run(kept, findings)
    assert any(r["rule"] == "IDENT_EXEMPTION_INPUT_MISSING" and r["code"] == code for r in red)


# ---------------------------------------------------------------------------
# 2. 겹 ② — 잔차가 박제와 다르면 RED (박제 잔차 ≠ 실측이면 면제 무효)
# ---------------------------------------------------------------------------
_ALL_PINS = [(c, q, key) for (c, q), spec in REG.items() for key in spec["findings"]]


@pytest.mark.parametrize("code,quarter,key", _ALL_PINS)
def test_every_pinned_residual_drift_revives_red(records, findings, code, quarter, key):
    """박제값을 tol 보다 조금 더 옮겨 놓으면(= 실측이 박제와 다르면) 그 축은 면제가 깨진다."""
    orig = REG[(code, quarter)]["findings"][key]
    REG[(code, quarter)]["findings"][key] = orig + 0.02
    try:
        accepted, red, _rev, _det = _run(records, findings)
    finally:
        REG[(code, quarter)]["findings"][key] = orig
    assert any(r["rule"] == "IDENT_EXEMPTION_RESIDUAL_DRIFT" and r.get("axis") == key
               and r["code"] == code and r["quarter"] == quarter for r in red)
    if key.endswith("|적용전"):
        rule = key.split("|")[0]
        assert not any(f.get(KEY_CODE) == code and f.get(KEY_QUARTER) == quarter
                       and str(f.get("rule")) == rule for f in accepted)


def test_inert_when_the_axis_stops_failing(records, findings):
    """룰엔진이 그 RED 를 더 안 내면 '등재를 풀어라' 가 나와야 한다(죽은 핀 방지)."""
    code, quarter = "KR1106", "2025.3Q"
    finds = [f for f in findings
             if not (f.get(KEY_CODE) == code and f.get(KEY_QUARTER) == quarter
                     and str(f.get("rule")) == "6")]
    _acc, _red, review, _det = _run(records, finds)
    assert any(r["rule"] == "IDENT_EXEMPTION_INERT" and r["code"] == code for r in review)


def test_malformed_rule_key_is_red(records, findings):
    key = ("KR1104", "2026.2Q")
    REG[key]["findings"]["1|적용전"] = 0.0
    try:
        _acc, red, _rev, _det = _run(records, findings)
    finally:
        del REG[key]["findings"]["1|적용전"]
    assert any(r["rule"] == "IDENT_EXEMPTION_MALFORMED" for r in red)


# ---------------------------------------------------------------------------
# 3. 적용후 거울 축이 박제를 **직접** 대조한다 — 흔들면 그 축 자체가 RED 를 낸다
# ---------------------------------------------------------------------------
def _after_rows(records):
    fails, _sk, pinned = gate._transition_identities_after(records)
    mm, _sub, _sk2, _unv = gate._transition_mmult_after(records, readability={})
    return fails, pinned, mm


def test_after_mirrors_are_pinned_on_the_live_master(records):
    fails, pinned, mm = _after_rows(records)
    # 축 17후(8_life 거울)는 `_LIFE8_ISSUER_INCONSISTENT` 소관 — 두 게이트가 같은 필터로 뺀다.
    mm, _ex = gate._mmult_after_life8_exempt(mm, gate._life8_issuer_inconsistent(records)[0])
    ri = lambda rows: [r for r in rows if str(r[0]).startswith("KR11")]  # noqa: E731
    assert ri(fails) == [] and ri(mm) == []
    got = {(r[0], r[1], r[3]) for r in pinned}
    want = {(c, q, gate._IDENT_RULE_AFTER_AXIS[k.split("|")[0]])
            for (c, q), s in REG.items() for k in s["findings"]
            if k.endswith("|적용후") and k.split("|")[0] != "4"}
    assert want <= got


@pytest.mark.parametrize("code,quarter,item,axis", [
    ("KR1103", "2026.2Q", 16, "R6_item16"),
    ("KR1103", "2026.2Q", 14, "R5_기준금액"),
    ("KR1104", "2026.2Q", 7, "R2_순자산합"),
    ("KR1105", "2026.1Q", 4, "R2_순자산합"),
])
def test_after_identity_drift_is_red_in_the_axis(records, code, quarter, item, axis):
    pin = REG[(code, quarter)]["cells"][item]["값_적용후"]
    with _cell(records, code, quarter, item, "값_적용후", pin + 5.0):
        fails, _pinned, _mm = _after_rows(records)
    assert any(r[0] == code and r[1] == quarter and r[3] == axis for r in fails)


def test_after_mmult15_drift_is_red_in_the_axis(records):
    code, quarter = "KR1103", "2026.2Q"
    pin = REG[(code, quarter)]["cells"][17]["값_적용후"]
    with _cell(records, code, quarter, 17, "값_적용후", pin + 5.0):
        _f, _p, mm = _after_rows(records)
    assert any(r[0] == code and r[1] == quarter and r[3] == 15 for r in mm)


# ---------------------------------------------------------------------------
# 4. 배선 — 근거 원장 · 두 게이트 · 차단 회계
# ---------------------------------------------------------------------------
def test_registry_is_wired_into_provenance_and_ledger_comparison():
    assert "_IDENT_ISSUER_INCONSISTENT" in gate._exemption_registries()
    mapped = {(reg, c, q) for reg, c, q in gate._code_pin_map()}
    for c, q in REG:
        assert ("_IDENT_ISSUER_INCONSISTENT", c, q) in mapped


def test_every_registered_bucket_has_a_verified_ledger_entry():
    ledger = json.loads((ROOT / "data" / "_gold" / "kics_exemption_provenance.json")
                        .read_text(encoding="utf-8"))
    have = {(e.get("company"), e.get("quarter")): e for e in ledger["entries"]
            if e.get("registry") == "_IDENT_ISSUER_INCONSISTENT"}
    for key, spec in REG.items():
        e = have.get(key)
        assert e is not None, f"{key} 원장 기록이 없다"
        assert e.get("status") == "VERIFIED"
        v = e.get("verify") or {}
        assert v.get("file") and (v.get("present_rows") or v.get("present_markers"))
        assert e.get("expected_residual") == spec["findings"], f"{key}: 원장 박제 ≠ 코드 박제"


def test_both_gates_call_the_same_function():
    """데이터계약 게이트가 면제를 재구현하지 않고 같은 함수를 부른다(두 게이트가 같은 대답)."""
    src = (ROOT / "scripts" / "validate_data_contract.py").read_text(encoding="utf-8")
    assert "_ident_issuer_inconsistent(" in src
    assert "_mmult_after_life8_exempt(" in src
    # `AFTER_IDENT_ISSUER_INCONSISTENT`(다른 장치, 주석에 등장) 와 구분한다.
    assert not re.search(r"(?<![A-Z])_IDENT_ISSUER_INCONSISTENT", src), \
        "레지스트리를 복사했다 — 위임해야 한다"
    gsrc = (ROOT / "scripts" / "validate_kics_disclosure.py").read_text(encoding="utf-8")
    assign = gsrc.index('report["ident_issuer_inconsistent_exception"]')
    assert gsrc.index("out_path.write_text", assign) > assign, "면제 기록이 아티팩트에 안 남는다"
    assert "or ident_red" in gsrc, "면제가 깨졌을 때 exit code 에 안 들어간다"


def test_life8_mmult17_filter_is_shared(records):
    """축 17후 면제는 두 게이트가 같은 함수로 뺀다 — KR1103 2025.2Q 가 실제로 빠지는지 본다."""
    mm, _sub, _sk, _unv = gate._transition_mmult_after(records, readability={})
    ok, _r, _rv, _d = gate._life8_issuer_inconsistent(records)
    kept, exempted = gate._mmult_after_life8_exempt(mm, ok)
    assert any(r[0] == "KR1103" and r[1] == "2025.2Q" and r[3] == 17 for r in exempted)
    assert not any(r[3] == 17 and (r[0], r[1]) in ok for r in kept)
