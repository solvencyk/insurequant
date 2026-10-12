# -*- coding: utf-8 -*-
"""`TIER2_STALE_FALSE_POSITIVE` (마이브라운 KR1108 2025.3Q, owner 승인 2026-10-12)의 **변이시험**.

`TIER2_LIMIT_STALE`(47_tier2_census, 전기 한도 잔존 지문)는 소액 초소형사의 원문 대시(0)를 재탕으로 오인한다 --
마이브라운 2025.3Q 원문 p16 이 보완자본·한도·신종·후순위를 전부 `-` 로 인쇄하는데 지급여력기준금액이 1.25억 -> 6.19억이라
0 이 직전분기 기대치(0.63억)와 허용오차(2.0억) 안에서 같다. 등재는 (회사,분기) 한 칸 박제이고 읽는 쪽은
`kics_json_rules._tier2_cross_bucket_context` 한 곳이다. 등재부만 있고 읽는 분기가 없으면 다음 라운드에 새므로 이 파일은
**읽는 쪽을 변이**시킨다. 해당 5칸(47/48/49/53/54)은 아직 마스터에 없다(parser-kics 적재 대기) -- 그래서 여기서는 인메모리로 적재를 가정한다.
"""
from __future__ import annotations

import copy
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import solvency.validation.kics_json_rules as R  # noqa: E402
import validate_kics_disclosure as K  # noqa: E402

KEY = ("KR1108", "2025.3Q")
MASTER = ROOT / "kics_disclosure.json"
LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"
REG = "TIER2_STALE_FALSE_POSITIVE"
NAMES = {47: "보완자본 한도 적용 전", 48: "보완자본 한도", 49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
         53: "(기발행 신종자본증권)", 54: "(기발행 후순위채무)"}


@pytest.fixture(scope="module")
def all_records():
    return json.loads(MASTER.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def kr1108(all_records):
    return [r for r in all_records if r["원보험사코드"] == "KR1108"]


def _run(records):
    return R.run_validation(records,
                            source_has_breakdown=K._scan_breakdown_presence(records),
                            tfi_applicability=K._load_tfi_applicability(),
                            life_subrisk_applicability=K._load_life_subrisk_applicability(),
                            life_subrisk_source_absent=K._load_life_subrisk_source_absent())


def _with_cells(records, vals, q="2025.3Q", code="KR1108"):
    out = list(records)
    tmpl = next(r for r in records if r["원보험사코드"] == code and r["공시분기"] == q)
    for item, v in vals.items():
        assert not any(r["원보험사코드"] == code and r["공시분기"] == q and int(r["항목번호"]) == item for r in records), item
        r = copy.deepcopy(tmpl)
        r["항목번호"] = item
        r["항목명"] = NAMES.get(item, str(item))
        r["값"] = str(v)
        r["값_적용후"] = str(v)
        out.append(r)
    return out


ZEROS = {47: 0, 48: 0, 49: 0, 53: 0, 54: 0}


def _stale_reds(report):
    return sorted((f["공시분기"], str(f["rule"])) for f in report["findings"]
                  if f.get("원보험사코드") == "KR1108" and f.get("status") == "RED" and "TIER2_LIMIT_STALE" in str(f.get("detail")))


# ---------------------------------------------------------------------------------------------------
# 등재 범위 = owner 승인 1칸, 원장·등록 일치
# ---------------------------------------------------------------------------------------------------
def test_registry_scope_ledger_and_registration():
    assert set(R.TIER2_STALE_FALSE_POSITIVE) == {KEY}, sorted(R.TIER2_STALE_FALSE_POSITIVE)
    spec = R.TIER2_STALE_FALSE_POSITIVE[KEY]
    assert spec["approved"] == "owner 2026-10-12" and spec["must_have"] == (47, 48, 49)
    assert set(spec["cells"].values()) == {0.0} and set(spec["cells"]) == {47, 48, 49, 53, 54}
    assert K._exemption_registries()[REG] == frozenset(R.TIER2_STALE_FALSE_POSITIVE)
    led = [e for e in json.loads(LEDGER.read_text(encoding="utf-8"))["entries"] if e.get("registry") == REG]
    assert [(e["company"], e["quarter"]) for e in led] == [KEY]
    assert led[0]["status"] == "VERIFIED" and led[0]["verify"]["pages"] == [16]


def test_live_provenance_has_no_red_for_this_registry():
    red, _review = K._exemption_provenance_findings(K._exemption_registries(), None)
    assert not [r for r in red if r["registry"] == REG], red


def test_live_state_is_dormant_and_engine_has_no_stale_red(kr1108):
    view = R.tier2_stale_false_positive_view(kr1108)
    assert view == [{"code": "KR1108", "quarter": "2025.3Q", "approved": "owner 2026-10-12",
                     "columns": {"값": "DORMANT", "값_적용후": "DORMANT"}}], view
    assert _stale_reds(_run(kr1108)) == []


# ---------------------------------------------------------------------------------------------------
# 읽는 쪽 -- 5칸을 적재(가정)하면 등재가 있을 때만 RED 가 안 난다
# ---------------------------------------------------------------------------------------------------
def test_loaded_zeros_are_exempt_with_registry(kr1108):
    recs = _with_cells(kr1108, ZEROS)
    assert _stale_reds(_run(recs)) == []
    assert R.tier2_stale_false_positive_view(recs)[0]["columns"] == {"값": "APPLIED", "값_적용후": "APPLIED"}


def test_loaded_zeros_are_red_without_registry(kr1108, monkeypatch):
    """대조군: 등재부가 비면 같은 적재가 정확히 RED 2(전·후) -- 위 시험이 「애초에 안 걸려서」 통과한 것이 아님을 보인다."""
    monkeypatch.setattr(R, "TIER2_STALE_FALSE_POSITIVE", {})
    reds = _stale_reds(_run(_with_cells(kr1108, ZEROS)))
    assert reds == [("2025.3Q", "47_tier2_census"), ("2025.3Q", "47_tier2_census_post")], reds


def test_registry_for_another_quarter_does_not_cover(kr1108, monkeypatch):
    monkeypatch.setattr(R, "TIER2_STALE_FALSE_POSITIVE", {("KR1108", "2025.2Q"): R.TIER2_STALE_FALSE_POSITIVE[KEY]})
    assert len(_stale_reds(_run(_with_cells(kr1108, ZEROS)))) == 2


def test_registry_for_another_company_does_not_cover(kr1108, monkeypatch):
    monkeypatch.setattr(R, "TIER2_STALE_FALSE_POSITIVE", {("KR1098", "2025.3Q"): R.TIER2_STALE_FALSE_POSITIVE[KEY]})
    assert len(_stale_reds(_run(_with_cells(kr1108, ZEROS)))) == 2


@pytest.mark.parametrize("bad", [
    {47: 0, 48: 0.3, 49: 0, 53: 0, 54: 0},       # 한도가 0 이 아니다 -- 박제 어긋남
    {47: 0, 48: 0, 49: 0, 53: 0.2, 54: 0},       # 메모행이 0 이 아니다
    {47: 1.0, 48: 0, 49: 0, 53: 0, 54: 0},       # 47 이 0 이 아니다
])
def test_pin_drift_revives_the_red(kr1108, bad):
    recs = _with_cells(kr1108, bad)
    view = R.tier2_stale_false_positive_view(recs)[0]["columns"]
    assert view == {"값": "DRIFT", "값_적용후": "DRIFT"}, view
    # 박제가 어긋나면 면제가 없어 지문(48 이 직전분기 기대치 근처)이 그대로 RED
    assert len(_stale_reds(_run(recs))) == 2


def test_missing_must_have_is_not_an_exemption(kr1108):
    """47/48/49 중 하나라도 결측이면 면제가 서지 않는다(결측은 면제가 아니다) -- 이 경우 DORMANT 가 아니라 DRIFT/부분결측."""
    recs = _with_cells(kr1108, {47: 0, 48: 0, 53: 0, 54: 0})          # 49 결측
    assert R.tier2_stale_false_positive_view(recs)[0]["columns"] == {"값": "DRIFT", "값_적용후": "DRIFT"}


def test_loading_the_cells_adds_only_the_expected_findings(all_records):
    """전수 시뮬레이션: 5칸 적재 + 등재 -> 라이브 대비 새 RED 0 (SKIP/YELLOW -> GREEN/YELLOW 전이만)."""
    base = _run(all_records)
    new = _run(_with_cells(all_records, ZEROS))

    def keys(rep):
        return {(f.get("원보험사코드"), f.get("공시분기"), str(f["rule"]), f["status"]) for f in rep["findings"]}
    appeared = keys(new) - keys(base)
    assert not [k for k in appeared if k[3] == "RED"], sorted(appeared)
    assert all(k[0] == "KR1108" and k[1] == "2025.3Q" for k in appeared | (keys(base) - keys(new)))


# ---------------------------------------------------------------------------------------------------
# 소스 변이 -- 읽는 분기를 지우면 시험이 깨져야 한다
# ---------------------------------------------------------------------------------------------------
def _mutant(path: Path, name: str, repl):
    src = path.read_text(encoding="utf-8")
    for old, new in repl:
        assert src.count(old) == 1, f"변이 앵커가 정확히 1번 있어야 한다: {old!r} ({src.count(old)}회)"
        src = src.replace(old, new)
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    sys.modules[name] = mod
    try:
        exec(compile(src, str(path), "exec"), mod.__dict__)  # noqa: S102
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return mod


def test_mutant_reader_branch_removed_leaves_the_red(kr1108):
    mod = _mutant(ROOT / "src" / "solvency" / "validation" / "kics_json_rules.py", "_mut_rules_stale_fp",
                  [("if fp is not None and _tier2_stale_fp_holds(fp, src):", "if False:")])
    try:
        recs = _with_cells(kr1108, ZEROS)
        rep = mod.run_validation(recs, source_has_breakdown=K._scan_breakdown_presence(recs),
                                 tfi_applicability=K._load_tfi_applicability(),
                                 life_subrisk_applicability=K._load_life_subrisk_applicability(),
                                 life_subrisk_source_absent=K._load_life_subrisk_source_absent())
    finally:
        sys.modules.pop("_mut_rules_stale_fp", None)
    assert len(_stale_reds(rep)) == 2, "읽는 분기를 지웠는데도 RED 가 안 돌아왔다 -- 시험이 무력하다"


def test_mutant_pin_check_loosened_would_exempt_drift(kr1108):
    """박제 비교를 지우면(항상 True) 박제 어긋난 값도 면제된다 -- 이 변이를 위 drift 시험이 잡아야 한다."""
    mod = _mutant(ROOT / "src" / "solvency" / "validation" / "kics_json_rules.py", "_mut_rules_stale_fp2",
                  [("        if v is not None and abs(v - pinned) > _TIER2_STALE_FP_EPS:\n            return False\n", "")])
    try:
        recs = _with_cells(kr1108, {47: 0, 48: 0.3, 49: 0, 53: 0, 54: 0})
        rep = mod.run_validation(recs, source_has_breakdown=K._scan_breakdown_presence(recs),
                                 tfi_applicability=K._load_tfi_applicability(),
                                 life_subrisk_applicability=K._load_life_subrisk_applicability(),
                                 life_subrisk_source_absent=K._load_life_subrisk_source_absent())
    finally:
        sys.modules.pop("_mut_rules_stale_fp2", None)
    assert _stale_reds(rep) == [], "박제 비교를 지운 변이가 면제를 넓히지 않는다 -- drift 시험이 이 비교를 못 본다"


# ---------------------------------------------------------------------------------------------------
# 근거 원장 -- 기록이 없거나 원문이 반증하면 RED
# ---------------------------------------------------------------------------------------------------
def _ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_ledger_record_missing_is_red():
    led = _ledger()
    led["entries"] = [e for e in led["entries"] if e.get("registry") != REG]
    red, _ = K._exemption_provenance_findings(K._exemption_registries(), led)
    assert any(r["rule"] == "EXEMPTION_PROVENANCE_MISSING" and r["registry"] == REG for r in red)


def test_ledger_marker_contradicted_is_red():
    led = _ledger()
    for e in led["entries"]:
        if e.get("registry") == REG:
            v = copy.deepcopy(e["verify"])
            v["present_markers"] = list(v["present_markers"]) + ["이 문구는 원문에 없다 zz-not-in-pdf"]
            e["verify"] = v
    red, _ = K._exemption_provenance_findings(K._exemption_registries(), led)
    assert any(r["rule"] == "EXEMPTION_CITATION_CONTRADICTED" and r["registry"] == REG for r in red)


def test_ledger_absent_marker_present_in_source_is_red():
    """원문이 대시가 아니라 숫자를 인쇄한다고 바뀌면(부재 마커 = 그 숫자가 실재) 면제가 무효다."""
    led = _ledger()
    for e in led["entries"]:
        if e.get("registry") == REG:
            v = copy.deepcopy(e["verify"])
            v["absent_markers"] = ["지급여력기준금액619"]            # 실제로 있는 문구 -> 반증으로 잡혀야 한다
            e["verify"] = v
    red, _ = K._exemption_provenance_findings(K._exemption_registries(), led)
    assert any(r["rule"] == "EXEMPTION_CITATION_CONTRADICTED" and r["registry"] == REG for r in red)


def test_registration_dropped_from_exemption_registries_is_silent():
    """`_exemption_registries()` 에서 빼면 원장 기록 부재가 안 잡힌다 -- 등록이 방어선이다."""
    regs = K._exemption_registries()
    assert REG in regs
    led = _ledger()
    led["entries"] = [e for e in led["entries"] if e.get("registry") != REG]
    assert any(r["registry"] == REG for r in K._exemption_provenance_findings(regs, led)[0])
    no_reg = {k: v for k, v in regs.items() if k != REG}
    assert not any(r["registry"] == REG for r in K._exemption_provenance_findings(no_reg, led)[0])
