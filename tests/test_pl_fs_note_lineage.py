# -*- coding: utf-8 -*-
"""재무제표·감사보고서 주석 계보 허용(`PL_FS_NOTE_LINEAGE`, owner 2026-10-11)의 **변이시험**.

배경: 재보사 17버킷 + 라이나 3버킷의 PL 항목 4(원수CSM상각)는 경영공시 PDF 에 **붙은 감사보고서 주석**에서
읽은 값이다. 경로 계보(`data/disclosure/`)는 그것을 §2-1 요약 PL 과 못 가르므로 사이드카 `how`
(= `fs_note_csm_amort`)로 가르고, 두 게이트가 항목 4 만 좁게 푼다.
  (a) validate_data_contract §3d  CONCEPT_MIXED_DISCLOSURE_INTO_DART — 항목 4 를 허용 제한에서 뺀다.
  (b) validate_master_tables 2b   ZERO_LEGS — 「sub-leg 전부 결측」 판정에서 항목 4 를 다리로 세지 않는다.

"좁게 열었다" 는 주장은 **양쪽 변이**로만 증명된다 — 허용을 넓히는 변이(항목·how·근거 필드·블록 조건을
뺀다)와 허용을 없애는 변이를 각각 게이트 소스에 걸어, selftest 케이스가 그 변이를 **잡는지** 본다.
변이 소스는 원본 경로로 컴파일해 ROOT 해석을 보존하고 디스크는 건드리지 않는다.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import _data_contract_selftest as ST  # noqa: E402
import validate_data_contract as DC  # noqa: E402
import validate_master_tables as VM  # noqa: E402

DC_PATH = ROOT / "scripts" / "validate_data_contract.py"
VM_PATH = ROOT / "scripts" / "validate_master_tables.py"

# selftest 의 이 가족 케이스: (함수 이름) -> 기대 RED 규칙 집합
DC_CASES = {
    "f_pl_fs_note_item4_is_clean": set(),
    "f_pl_fs_note_without_evidence": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_fs_note_item4_wrong_how": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_fs_note_how_resolution_mismatch": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_fs_note_reference_only_item": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_fs_note_mixed_with_item17": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_fs_note_other_contract_note_item": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_fs_note_wrong_block": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
}
MT_NAMES = ("S7", "S8", "S9", "S10")


def _mutant(path: Path, name: str, repl: list[tuple[str, str]]):
    src = path.read_text(encoding="utf-8")
    for old, new in repl:
        assert src.count(old) == 1, f"변이 앵커가 소스에 정확히 1번 있어야 한다: {old!r} ({src.count(old)}회)"
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


def _dc_failures(mod) -> set[str]:
    """이 모듈로 DC_CASES 를 돌려 기대와 어긋난 케이스 이름 집합."""
    bad = set()
    for fn_name, expect in DC_CASES.items():
        res = mod.run_gate(mod.Env(inject=getattr(ST, fn_name)()))
        if {f.rule for f in res.red} != expect:
            bad.add(fn_name)
    return bad


def _mt_failures(V) -> set[str]:
    bad = set()
    for name, fixture, expect in ST.MT_CASES:
        if name.split()[0] not in MT_NAMES:
            continue
        pl, src, extra = fixture()
        na: dict = {}
        with contextlib.redirect_stdout(io.StringIO()):
            _p, pb_fail, _s, zleg_rows, _z0 = V._check_pl_bridge(pl, extra, [], {}, source_ids=src, src_na_out=na)
        got = {"legcov_fail": sum(1 for r in pb_fail if r[2] == "보험손익(leg-coverage)"),
               "zleg": len(zleg_rows), "na_legcov": na.get("legcov", 0), "na_zleg": na.get("zleg", 0)}
        if got != expect:
            bad.add(name.split()[0])
    return bad


# ---------------------------------------------------------------------------------------------------
# 현행 게이트는 이 가족 케이스를 전부 통과한다 (변이시험의 대조군)
# ---------------------------------------------------------------------------------------------------
def test_live_gates_pass_the_family():
    assert _dc_failures(DC) == set()
    assert _mt_failures(VM) == set()


def test_allowance_scope_is_pinned_to_owner_approval():
    """허용 목록은 owner 승인(2026-10-11)대로 `fs_note_csm_amort` -> {4} 한 줄이다. 늘리려면 여기·selftest·승인을 같이."""
    assert {k: set(v) for k, v in DC.PL_FS_NOTE_LINEAGE.items()} == {"fs_note_csm_amort": {4}}
    # reference_only(17/20/21)는 어떤 how 로도 못 들어온다
    ref = set(DC.CONCEPT_REGISTRY["pl_disclosure_vs_dart"]["reference_only_items"])
    assert not (ref & set().union(*DC.PL_FS_NOTE_LINEAGE.values()))


# ---------------------------------------------------------------------------------------------------
# (a) §3d — 변이를 걸면 selftest 케이스가 깨져야 한다
# ---------------------------------------------------------------------------------------------------
DC_MUTANTS = {
    # 허용을 없앤다 -> 「항목 4 는 정상」 케이스가 깨져야 한다
    "allowance_removed": ([('PL_FS_NOTE_LINEAGE: dict[str, frozenset] = {"fs_note_csm_amort": frozenset({4})}',
                            'PL_FS_NOTE_LINEAGE: dict[str, frozenset] = {}')],
                          {"f_pl_fs_note_item4_is_clean"}),
    # 허용 항목을 넓힌다(reference_only 17, 다른 contract_notes 항목 5) -> 둘 다 깨져야 한다
    "allowance_widened_items": ([('frozenset({4})}\n\n\ndef _pl_fs_note_exempt_items',
                                  'frozenset({4, 5, 17})}\n\n\ndef _pl_fs_note_exempt_items')],
                                {"f_pl_fs_note_reference_only_item", "f_pl_fs_note_mixed_with_item17",
                                 "f_pl_fs_note_other_contract_note_item"}),
    # 근거 필드(쪽·인쇄값) 조건을 뺀다
    "evidence_check_removed": ([('        if not (sf.get("page") or sf.get("pages")) or sf.get("printed") in (None, ""):\n            continue\n', '')],
                               {"f_pl_fs_note_without_evidence"}),
    # how == resolution 조건을 뺀다
    "resolution_check_removed": ([('if allowed is None or how != cell.get("resolution"):',
                                   'if allowed is None:')],
                                 {"f_pl_fs_note_how_resolution_mismatch"}),
    # contract_notes 블록 조건을 뺀다
    "block_check_removed": ([('    if cell.get("item_block") != "contract_notes":\n        return set()\n', '')],
                            {"f_pl_fs_note_wrong_block"}),
    # 항목을 가리지 않고 entry 의 items 전부를 빼 버린다(가장 흔한 과잉 허용: `& allowed` 누락)
    "entry_items_not_intersected": ([('out |= {int(i) for i in (sf.get("items") or []) if str(i).isdigit()} & allowed',
                                      'out |= {int(i) for i in (sf.get("items") or []) if str(i).isdigit()}')],
                                    {"f_pl_fs_note_reference_only_item", "f_pl_fs_note_mixed_with_item17",
                                     "f_pl_fs_note_other_contract_note_item"}),
}


@pytest.mark.parametrize("name", sorted(DC_MUTANTS))
def test_data_contract_mutants_are_caught(name):
    repl, must_fail = DC_MUTANTS[name]
    mod = _mutant(DC_PATH, f"_mut_dc_{name}", repl)
    try:
        failed = _dc_failures(mod)
    finally:
        sys.modules.pop(f"_mut_dc_{name}", None)
    assert must_fail <= failed, (
        f"변이 {name} 이 selftest 에 안 잡혔다 — 잡혀야 할 케이스 {sorted(must_fail - failed)} 가 통과했다. "
        f"실제로 깨진 케이스: {sorted(failed)}")


# ---------------------------------------------------------------------------------------------------
# (b) ZERO_LEGS — 변이
# ---------------------------------------------------------------------------------------------------
VM_MUTANTS = {
    # 항목 4 를 다시 다리로 센다(원래 버그) -> S7 이 깨져야 한다
    "item4_counted_again": ([('PL_ZLEG_NA_IGNORED_LEGS = frozenset({"원수CSM상각"})',
                              'PL_ZLEG_NA_IGNORED_LEGS = frozenset()')], {"S7"}),
    # 제외 다리를 넓힌다(항목 4 외 다리도 무시) -> 다른 다리에 값이 있는 버킷이 숨는다: S8/S9 가 깨져야 한다
    "ignored_legs_widened": ([('PL_ZLEG_NA_IGNORED_LEGS = frozenset({"원수CSM상각"})',
                               'PL_ZLEG_NA_IGNORED_LEGS = frozenset(PL_LEG_ITEMS)')], {"S8", "S9"}),
    # 계보 한정을 뺀다(모든 계보에서 항목 4 무시) -> DART 계보 S10 이 깨져야 한다
    "lineage_gate_removed": ([('        if (source_ids.get((co, q)) == PL_DISCLOSURE_SOURCE_ID\n                and all(m.get(k) is None for k in PL_LEG_ITEMS\n                        if k not in PL_ZLEG_NA_IGNORED_LEGS)):',
                               '        if (True\n                and all(m.get(k) is None for k in PL_LEG_ITEMS\n                        if k not in PL_ZLEG_NA_IGNORED_LEGS)):')], {"S10"}),
}


@pytest.mark.parametrize("name", sorted(VM_MUTANTS))
def test_master_tables_mutants_are_caught(name):
    repl, must_fail = VM_MUTANTS[name]
    mod = _mutant(VM_PATH, f"_mut_vm_{name}", repl)
    try:
        failed = _mt_failures(mod)
    finally:
        sys.modules.pop(f"_mut_vm_{name}", None)
    assert must_fail <= failed, (
        f"변이 {name} 이 selftest 에 안 잡혔다 — {sorted(must_fail - failed)} 가 통과했다. 깨진 케이스: {sorted(failed)}")


# ---------------------------------------------------------------------------------------------------
# 데이터 쪽: 라이브 사이드카에서 이 how 를 쓰는 셀이 허용 범위를 벗어나지 않는다
# ---------------------------------------------------------------------------------------------------
def test_live_sidecar_uses_the_how_only_for_item4_note_cells():
    side = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
    pub = {}
    for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")):
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        if r.get("값") is None:
            continue
        blk = "contract_notes" if it in DC._PL_CONTRACT_NOTE_ITEMS else "income_statement"
        pub.setdefault((r["원보험사코드"], r["공시분기"], blk), set()).add(it)
    n = 0
    for c in side["cells"]:
        for sf in c.get("source_files") or []:
            if sf.get("how") in DC.PL_FS_NOTE_LINEAGE:
                n += 1
                key = (c["company_code"], c["quarter"], c["item_block"])
                assert c["item_block"] == "contract_notes" and c.get("resolution") == sf["how"], key
                assert set(sf.get("items") or []) <= DC.PL_FS_NOTE_LINEAGE[sf["how"]], key
                assert pub.get(key, set()) <= DC.PL_FS_NOTE_LINEAGE[sf["how"]], (
                    f"{key}: 이 how 를 단 블록이 허용 항목 밖의 값도 발행한다 {sorted(pub.get(key, set()))}")
                assert sf.get("page") or sf.get("pages"), key
                assert sf.get("printed") not in (None, ""), key
    assert n >= 1
