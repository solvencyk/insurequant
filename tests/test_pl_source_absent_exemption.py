# -*- coding: utf-8 -*-
"""PL_breakdown 원천부재 등재 `_PL_SOURCE_ABSENT` 의 **변이시험** (owner 승인 2026-10-11, 하노버 2025.3Q 한 칸).

배경: K-ICS 쪽 `_CENSUS_SOURCE_ABSENT[("KR1104","2025.3Q")]`(NOT_POSTED)는 K-ICS census 만 덮는다. 같은 문서가
게시되지 않은 사실로 PL_breakdown 에도 `MASTER_HOLE`(통째) 1버킷이 남아 push 를 막았다. PL 쪽에 별도 등재부를 두되
**K-ICS 와 같은 재검산 함수**(`_census_source_absent`)를 부르고, 읽는 쪽(lookup 분기)은 `coverage_holes(source_absent=)`
한 곳이다. 등재부만 쓰고 읽는 분기가 없으면 다음 라운드에 샌다 -- 그래서 이 파일은 **쓰는 쪽(재검산)과 읽는 쪽(hole
제외)을 각각 변이**시킨다.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import _data_contract_selftest as ST  # noqa: E402
import validate_data_contract as DC  # noqa: E402
import validate_kics_disclosure as K  # noqa: E402
import validate_master_tables as VM  # noqa: E402

KEY = ("KR1104", "2025.3Q")
LEDGER_PATH = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"


def _ledger():
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _present_without_key():
    # 하노버의 다른 분기 버킷만 있고 2025.3Q 는 없다(= 실제 마스터의 모양)
    return {("KR1104", "2025.2Q"), ("KR1104", "2025.4Q")}


NAMES = {"KR1104": "하노버재보험"}


def _run(ledger=None, registry=None, present=None, root=None):
    # 이 파일은 하노버 한 칸을 시험한다 -- 서울보증(2026-10-12 등재)은 test_pl_source_absent_site_rolled_off.py 가 시험한다.
    if registry is None:
        registry = {KEY: K._PL_SOURCE_ABSENT[KEY]}
    return K.pl_source_absent_exemptions(
        present if present is not None else _present_without_key(), NAMES,
        registry=registry, ledger=ledger if ledger is not None else _ledger(), root=root)


def _ledger_with(mutator):
    led = _ledger()
    for e in led["entries"]:
        if e.get("registry") == "_PL_SOURCE_ABSENT":
            mutator(e)
    return led


# ---------------------------------------------------------------------------------------------------
# 등재 범위 = owner 승인 (하노버 2025.3Q 한 칸), 원장·레지스트리 일치
# ---------------------------------------------------------------------------------------------------
SGI_KEYS = {("KR0150", "2024.2Q"), ("KR0150", "2024.3Q")}   # owner 승인 2026-10-12 (서울보증, tests/test_pl_source_absent_site_rolled_off.py 가 따로 변이시험)


def test_registry_is_pinned_to_owner_approval_and_ledger_agrees():
    assert set(K._PL_SOURCE_ABSENT) == {KEY} | SGI_KEYS,         f"등재 범위가 owner 승인(2026-10-11 하노버 1칸 + 2026-10-12 서울보증 2칸)과 다르다: {sorted(K._PL_SOURCE_ABSENT)}"
    spec = K._PL_SOURCE_ABSENT[KEY]
    assert spec["kind"] == "NOT_POSTED" and spec["raw"] == {} and "2026-10-11" in spec["approved"]
    led = {(e["company"], e["quarter"]): e for e in _ledger()["entries"] if e.get("registry") == "_PL_SOURCE_ABSENT"}
    assert set(led) == {KEY} | SGI_KEYS
    assert led[KEY]["status"] == "VERIFIED" and led[KEY]["claim_kind"] == "NOT_POSTED"
    assert K._exemption_registries()["_PL_SOURCE_ABSENT"] == frozenset(K._PL_SOURCE_ABSENT)


def test_live_reverification_passes_and_pl_master_really_has_no_bucket():
    names, ok, red = VM.pl_source_absent_for_coverage()
    assert not red, red
    assert KEY in ok and ("하노버재보험", "2025.3Q") in names
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    assert not [r for r in rows if r["원보험사코드"] == KEY[0] and r["공시분기"] == KEY[1]]


# ---------------------------------------------------------------------------------------------------
# 읽는 쪽 -- coverage_holes 가 재검산 통과 칸을 「통째」 hole 에서 뺀다 (라이브 PL 마스터)
# ---------------------------------------------------------------------------------------------------
def _live_holes(**kw):
    pl = VM.load_long(VM.PL_PATH)
    keys = ["보험손익", "생명장기손익", "당기순이익"]
    src = VM.pl_cell_source_ids()
    return VM.coverage_holes(pl, keys, na_registry=VM.LOB_LEG_NA, key_items_for=VM.pl_key_items_for(src, keys), **kw)


def test_reader_removes_only_the_registered_whole_bucket_hole():
    names, _ok, _red = VM.pl_source_absent_for_coverage()
    real0, _k0, _s0 = _live_holes()
    hit: list = []
    real1, _k1, _s1 = _live_holes(source_absent=names, absent_out=hit)
    removed = [("서울보증보험", "2024.2Q", "통째"), ("서울보증보험", "2024.3Q", "통째"), ("하노버재보험", "2025.3Q", "통째")]
    for r in removed:
        assert r in real0 and r not in real1
    assert sorted(hit) == [("서울보증보험", "2024.2Q"), ("서울보증보험", "2024.3Q"), ("하노버재보험", "2025.3Q")]
    # 등재 3칸 말고는 아무것도 안 바뀐다
    assert sorted(set(real0) - set(real1)) == removed
    assert not (set(real1) - set(real0))


def test_reader_does_not_remove_a_hole_with_a_different_key():
    real0, _k, _s = _live_holes()
    real1, _k1, _s1 = _live_holes(source_absent={("하노버재보험", "2025.2Q"): ("NOT_POSTED", "x")})
    assert real1 == real0


# ---------------------------------------------------------------------------------------------------
# 쓰는 쪽 -- 재검산(①~⑤)이 깨지면 면제가 없고 장치 RED 가 난다
# ---------------------------------------------------------------------------------------------------
def test_baseline_passes():
    ok, red = _run()
    assert KEY in ok and not red


def _assert_broken(rule_suffix, **kw):
    ok, red = _run(**kw)
    assert KEY not in ok, "깨진 등재가 면제를 줬다"
    rules = {r["rule"] for r in red}
    assert f"PL_SOURCE_ABSENT_{rule_suffix}" in rules, (rule_suffix, red)


def test_ledger_record_missing_breaks_it():
    led = _ledger()
    led["entries"] = [e for e in led["entries"] if e.get("registry") != "_PL_SOURCE_ABSENT"]
    _assert_broken("LEDGER_DISAGREE", ledger=led)


def test_k_ics_ledger_record_does_not_cover_pl():
    """K-ICS 등재의 원장 기록(`_CENSUS_SOURCE_ABSENT`)만 있고 PL 기록이 없으면 PL 면제는 없다 -- 덮어쓰기 금지."""
    led = _ledger()
    assert [e for e in led["entries"] if e.get("registry") == "_CENSUS_SOURCE_ABSENT" and (e["company"], e["quarter"]) == KEY]
    led["entries"] = [e for e in led["entries"] if e.get("registry") != "_PL_SOURCE_ABSENT"]
    _assert_broken("LEDGER_DISAGREE", ledger=led)


def test_ledger_claim_kind_mismatch_breaks_it():
    _assert_broken("LEDGER_DISAGREE", ledger=_ledger_with(lambda e: e.update(claim_kind="DOCUMENT_PENDING_NOTICE")))


def test_ledger_status_not_verified_breaks_it():
    _assert_broken("LEDGER_DISAGREE", ledger=_ledger_with(lambda e: e.update(status="UNVERIFIED")))


def test_ledger_marker_contradicted_breaks_it():
    """인용 원천(다운로더 매니페스트)에 근거 문구가 사라지면(= 사이트가 3Q 를 게시했다고 매니페스트가 바뀌면) 면제가 무효다."""
    def mut(e):
        v = copy.deepcopy(e["verify"])
        v["present_markers"] = list(v["present_markers"]) + ["이 문구는 원천에 없다 zz-not-in-manifest"]
        e["verify"] = v
    _assert_broken("LEDGER_DISAGREE", ledger=_ledger_with(mut))


def test_ledger_without_markers_breaks_it():
    def mut(e):
        e["verify"] = {"file": e["verify"]["file"]}
    _assert_broken("LEDGER_DISAGREE", ledger=_ledger_with(mut))


def test_bucket_appearing_in_master_makes_it_inert_red():
    ok, red = _run(present=_present_without_key() | {KEY})
    assert KEY not in ok and {r["rule"] for r in red} == {"PL_SOURCE_ABSENT_INERT"}


@pytest.mark.parametrize("spec", [
    {"kind": "NO_SUCH_KIND", "approved": "owner 2026-10-11", "raw": {}},
    {"kind": "NOT_POSTED", "approved": "", "raw": {}},
    {"kind": "NOT_POSTED", "approved": "owner 2026-10-11", "raw": {"data/x.pdf": "00"}},
])
def test_malformed_registration_is_red(spec):
    _assert_broken("MALFORMED", registry={KEY: spec})


def test_unreadable_ledger_breaks_it():
    ok, red = _run(ledger={"_unreadable": True})
    assert KEY not in ok and "PL_SOURCE_ABSENT_LEDGER_DISAGREE" in {r["rule"] for r in red}


def test_empty_registry_is_noop():
    assert _run(registry={}) == ({}, [])


def _tmp_root(tmp_path, manifest_status=None, add_raw=False):
    """다운로더 매니페스트·raw 폴더만 흉내 낸 임시 루트(원장 인용 원천은 실제 ROOT 의 것을 쓴다)."""
    meta = tmp_path / "data" / "disclosure" / "_meta"
    meta.mkdir(parents=True)
    m = json.loads((ROOT / "data/disclosure/_meta/reinsurer_KR1104_manifest.json").read_text(encoding="utf-8"))
    if manifest_status:
        for p in m["periods"]:
            if p["period"] == KEY[1]:
                p["status"] = manifest_status
    (meta / "reinsurer_KR1104_manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    raw = tmp_path / "data" / "disclosure" / "FY2025_Q3" / "raw"
    raw.mkdir(parents=True)
    if add_raw:
        (raw / "KR1104_하노버재보험.pdf").write_bytes(b"%PDF-1.4 fake")
    return tmp_path


def test_tmp_root_baseline_passes(tmp_path):
    ok, red = _run(root=_tmp_root(tmp_path))
    assert KEY in ok and not red


def test_a_new_raw_document_for_that_quarter_breaks_it(tmp_path):
    """사이트가 3Q 를 게시해 raw 가 들어오면(= 원천이 생겼다) 면제 무효 -- parser 가 적재하고 등재를 풀 차례다."""
    _assert_broken("RAW_CHANGED", root=_tmp_root(tmp_path, add_raw=True))


def test_manifest_status_drift_breaks_it(tmp_path):
    _assert_broken("MANIFEST_DRIFT", root=_tmp_root(tmp_path, manifest_status="ok"))


# ---------------------------------------------------------------------------------------------------
# 읽는 쪽/등록 쪽 소스 변이 -- 읽는 분기를 지우거나 원장 등록을 빼면 시험이 깨져야 한다
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


def test_mutant_reader_branch_removed_leaves_the_hole():
    mod = _mutant(ROOT / "scripts" / "validate_master_tables.py", "_mut_vm_reader",
                  [("if source_absent and (co, q) in source_absent:", "if False and source_absent:")])
    try:
        pl = mod.load_long(mod.PL_PATH)
        keys = ["보험손익", "생명장기손익", "당기순이익"]
        src = mod.pl_cell_source_ids()
        names, _ok, _red = VM.pl_source_absent_for_coverage()
        real, _k, _s = mod.coverage_holes(pl, keys, na_registry=mod.LOB_LEG_NA,
                                          key_items_for=mod.pl_key_items_for(src, keys), source_absent=names)
    finally:
        sys.modules.pop("_mut_vm_reader", None)
    assert ("하노버재보험", "2025.3Q", "통째") in real, "읽는 분기를 지웠는데도 hole 이 사라졌다 -- 시험이 무력하다"


def test_mutant_gate_ignores_the_exemption_stays_red():
    """데이터계약 게이트의 1c 가 재검산 결과를 안 읽게 변이하면 Q10b(면제 정상) 가 깨진다."""
    mod = _mutant(ROOT / "scripts" / "validate_data_contract.py", "_mut_dc_reader",
                  [('if master == "PL_breakdown" else {})\n', 'if False else {})\n')])
    try:
        res = mod.run_gate(mod.Env(inject=ST.f_pl_hole_exempted_when_absent_verified()))
    finally:
        sys.modules.pop("_mut_dc_reader", None)
    assert any(f.rule == "MASTER_HOLE" and f.severity == "RED" for f in res.findings), \
        "게이트가 면제를 읽지 않게 변이했는데 hole RED 가 안 나왔다"


def test_mutant_registry_not_registered_for_provenance():
    """`_exemption_registries()` 에서 `_PL_SOURCE_ABSENT` 를 빼면 원장 기록 부재가 안 잡힌다 -- 등록이 있어야 막힌다."""
    regs = K._exemption_registries()
    assert "_PL_SOURCE_ABSENT" in regs
    led = _ledger()
    led["entries"] = [e for e in led["entries"] if e.get("registry") != "_PL_SOURCE_ABSENT"]
    red, _review = K._exemption_provenance_findings(regs, led)
    assert any(r["rule"] == "EXEMPTION_PROVENANCE_MISSING" and r["registry"] == "_PL_SOURCE_ABSENT" for r in red)
    no_reg = {k: v for k, v in regs.items() if k != "_PL_SOURCE_ABSENT"}
    red2, _r2 = K._exemption_provenance_findings(no_reg, led)
    assert not any(r["registry"] == "_PL_SOURCE_ABSENT" for r in red2)   # 등록을 빼면 침묵 = 등록이 방어선


def test_data_contract_selftest_family_passes():
    for fn, expect in (("f_pl_hole_whole_bucket_is_red", {"MASTER_HOLE"}),
                       ("f_pl_hole_exempted_when_absent_verified", set()),
                       ("f_pl_hole_exemption_for_other_cell_does_not_cover", {"MASTER_HOLE"}),
                       ("f_pl_hole_broken_exemption_stays_red", {"MASTER_HOLE", "PL_SOURCE_ABSENT_LEDGER_DISAGREE"}),
                       ("f_pl_partial_hole_is_not_exempted", {"MASTER_HOLE"})):
        res = DC.run_gate(DC.Env(inject=getattr(ST, fn)()))
        assert {f.rule for f in res.red} == expect, (fn, [(f.rule, f.severity) for f in res.findings])
