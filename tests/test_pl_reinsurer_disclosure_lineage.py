# -*- coding: utf-8 -*-
"""경영공시 요약 PL 계보 reference_only(17/20/21) 허용(`PL_DISCLOSURE_REINSURER_LINEAGE`, owner 2026-10-12)의 **변이시험**.

배경: 순수 재보사(KR1101~KR1107)·마이브라운(KR1108)은 DART 사업보고서가 없어 PL 의 원천이 경영공시 요약 포괄손익계산서 하나뿐이다.
reference_only(17/20/21)가 막히는 이유(같은 시계열에 DART 개념과 경영공시 개념이 섞임)가 이 회사들에는 없으므로
`validate_data_contract` §3d 가 **좁게** 푼다: DART 계보 셀이 없는 회사 · income_statement · 등재 how · 쪽 · 항목별 인쇄값.

"좁게 열었다" 는 주장은 **양쪽 변이**로만 증명된다 -- 허용을 넓히는 변이(조건 하나를 뺀다)와 허용을 없애는 변이를 게이트 소스에
걸어 selftest 케이스(Q11 가족)가 그 변이를 **잡는지** 본다. 변이 소스는 원본 경로로 컴파일하고 디스크는 건드리지 않는다.
"""
from __future__ import annotations

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

DC_PATH = ROOT / "scripts" / "validate_data_contract.py"

# selftest Q11 가족: (함수 이름) -> 기대 RED 규칙 집합
FAMILY = {
    "f_pl_rein_item17_20_21_is_clean": set(),
    "f_pl_rein_company_has_dart_cell": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_rein_unregistered_how": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_rein_item_without_printed": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_rein_printed_not_dict": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_rein_without_page": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_rein_item_not_registered": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_rein_published_beyond_entry_items": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_rein_wrong_block": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
    "f_pl_rein_published_block_missing_from_sidecar": {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"},
}


def _mutant(name: str, repl: list[tuple[str, str]]):
    src = DC_PATH.read_text(encoding="utf-8")
    for old, new in repl:
        assert src.count(old) == 1, f"변이 앵커가 소스에 정확히 1번 있어야 한다: {old!r} ({src.count(old)}회)"
        src = src.replace(old, new)
    mod = types.ModuleType(name)
    mod.__file__ = str(DC_PATH)
    sys.modules[name] = mod
    try:
        exec(compile(src, str(DC_PATH), "exec"), mod.__dict__)  # noqa: S102
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return mod


def _failures(mod) -> set[str]:
    bad = set()
    for fn_name, expect in FAMILY.items():
        try:
            res = mod.run_gate(mod.Env(inject=getattr(ST, fn_name)()))
        except Exception:  # noqa: BLE001  (변이가 게이트를 깨뜨린 것도 「잡혔다」 로 센다)
            bad.add(fn_name)
            continue
        if {f.rule for f in res.red} != expect:
            bad.add(fn_name)
    return bad


# ---------------------------------------------------------------------------------------------------
# 현행 게이트는 가족 케이스를 전부 통과한다(대조군) + 허용 범위가 owner 지시대로 박제돼 있다
# ---------------------------------------------------------------------------------------------------
def test_live_gate_passes_the_family():
    assert _failures(DC) == set()


def test_allowance_scope_is_pinned():
    assert {k: set(v) for k, v in DC.PL_DISCLOSURE_REINSURER_LINEAGE.items()} == {
        "disclosure_summary_pl_reinsurer": {17, 20, 21}}
    # 이 허용은 reference_only 안에서만 움직인다(5개 동일개념 항목과 별개) -- 그 밖 항목이 들어오면 시험이 깨진다.
    ref = set(DC.CONCEPT_REGISTRY["pl_disclosure_vs_dart"]["reference_only_items"])
    assert set().union(*DC.PL_DISCLOSURE_REINSURER_LINEAGE.values()) <= ref
    # 항목 4 주석 허용과 섞이지 않는다
    assert not (set().union(*DC.PL_DISCLOSURE_REINSURER_LINEAGE.values())
                & set().union(*DC.PL_FS_NOTE_LINEAGE.values()))


# ---------------------------------------------------------------------------------------------------
# 변이 -- 하나씩 걸면 해당 selftest 케이스가 깨져야 한다
# ---------------------------------------------------------------------------------------------------
_PRINTED_ITEM = ' and printed.get(str(i)) not in (None, "")}'
_COMPANY_BLOCK = 'if cell.get("company_code") not in dartless or cell.get("item_block") != "income_statement":'
MUTANTS = {
    # 허용을 없앤다 -> 「정상」 케이스가 깨져야 한다
    "allowance_removed": ([('PL_DISCLOSURE_REINSURER_LINEAGE: dict[str, frozenset] = {\n'
                            '    "disclosure_summary_pl_reinsurer": frozenset({17, 20, 21})}',
                            'PL_DISCLOSURE_REINSURER_LINEAGE: dict[str, frozenset] = {}')],
                          {"f_pl_rein_item17_20_21_is_clean"}),
    # 허용 항목을 넓힌다(18) -> 등재 밖 항목 케이스가 깨져야 한다
    "allowance_widened_items": ([('"disclosure_summary_pl_reinsurer": frozenset({17, 20, 21})}',
                                  '"disclosure_summary_pl_reinsurer": frozenset({17, 18, 20, 21})}')],
                                {"f_pl_rein_item_not_registered"}),
    # 등재 안 된 how 도 통과시킨다
    "how_check_removed": ([('allowed = PL_DISCLOSURE_REINSURER_LINEAGE.get(sf.get("how"))\n        if allowed is None or',
                            'allowed = PL_DISCLOSURE_REINSURER_LINEAGE.get(sf.get("how")) or frozenset({17, 20, 21})\n'
                            '        if allowed is None or')],
                          {"f_pl_rein_unregistered_how"}),
    # 항목별 인쇄값 조건을 뺀다
    "per_item_printed_removed": ([(_PRINTED_ITEM, '}')], {"f_pl_rein_item_without_printed"}),
    # 인쇄값 dict 조건을 뺀다(문자열도 통과) + 항목별 조건도 같이 뺀다
    "printed_type_removed": ([('or not isinstance(printed, dict):', 'or printed is None:'),
                              (_PRINTED_ITEM, '}')],
                             {"f_pl_rein_printed_not_dict", "f_pl_rein_item_without_printed"}),
    # 쪽 조건을 뺀다
    "page_check_removed": ([('if not (sf.get("page") or sf.get("pages")) or not isinstance(printed, dict):',
                             'if not isinstance(printed, dict):')],
                           {"f_pl_rein_without_page"}),
    # income_statement 블록 조건을 뺀다
    "block_check_removed": ([(_COMPANY_BLOCK, 'if cell.get("company_code") not in dartless:')],
                            {"f_pl_rein_wrong_block"}),
    # DART 없는 회사 조건을 뺀다 (가장 위험한 변이: 모든 회사에 연다)
    "company_condition_removed": ([(_COMPANY_BLOCK, 'if cell.get("item_block") != "income_statement":')],
                                  {"f_pl_rein_company_has_dart_cell"}),
    # DART 없는 회사 판정을 「하나라도 DISCLOSURE 면」 으로 느슨하게(AND -> OR)
    "dartless_and_to_or": ([('ok[co] = ok.get(co, True) and good', 'ok[co] = ok.get(co, True) or good')],
                           {"f_pl_rein_company_has_dart_cell"}),
    # 사이드카에 없는 발행 블록 검사를 뺀다
    "published_keys_check_removed": ([('            ok[k[0]] = False\n', '            pass\n')],
                                     {"f_pl_rein_published_block_missing_from_sidecar"}),
    # 항목 단위가 아니라 17/20/21 전부를 빼 버린다(entry 가 안 싣는 발행 항목까지)
    "exempt_all_three_whenever_any": ([('        _disc -= _rein\n',
                                        '        _disc -= ({17, 20, 21} if _rein else set())\n')],
                                      {"f_pl_rein_published_beyond_entry_items"}),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_mutants_are_caught(name):
    repl, must_fail = MUTANTS[name]
    mod = _mutant(f"_mut_rein_{name}", repl)
    try:
        failed = _failures(mod)
    finally:
        sys.modules.pop(f"_mut_rein_{name}", None)
    assert must_fail <= failed, (
        f"변이 {name} 이 selftest 에 안 잡혔다 -- 잡혀야 할 케이스 {sorted(must_fail - failed)} 가 통과했다. "
        f"실제로 깨진 케이스: {sorted(failed)}")


# ---------------------------------------------------------------------------------------------------
# 데이터 쪽: 라이브 사이드카에서 이 how 를 쓰는 셀이 허용 범위를 벗어나지 않는다
# ---------------------------------------------------------------------------------------------------
def _live():
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
    return side["cells"], pub


def test_live_sidecar_uses_the_how_only_inside_the_allowance():
    cells, pub = _live()
    dartless = DC._pl_dartless_companies(cells, pub)
    used_items: set = set()
    users: set = set()
    n = 0
    for c in cells:
        for sf in c.get("source_files") or []:
            how = sf.get("how")
            if how not in DC.PL_DISCLOSURE_REINSURER_LINEAGE:
                continue
            n += 1
            key = (c["company_code"], c["quarter"], c["item_block"])
            users.add(c["company_code"])
            assert c["company_code"] in dartless, f"{key}: DART 계보 셀이 있는 회사가 재보사 how 를 쓴다"
            assert c["item_block"] == "income_statement", key
            assert sf.get("page") or sf.get("pages"), key
            assert isinstance(sf.get("printed"), dict), key
            for i in sf.get("items") or []:
                assert str(i) in sf["printed"] and sf["printed"][str(i)] not in (None, ""), (key, i)
            used_items |= set(sf.get("items") or [])
            ok_items = set(DC.PL_DISCLOSURE_ITEM_NOS) | DC.PL_DISCLOSURE_REINSURER_LINEAGE[how]
            # 이 how 의 항목, 그리고 이 how 를 단 블록이 발행하는 항목은 (동일개념 5항목 + 등재 항목) 안이어야 한다
            assert set(sf.get("items") or []) <= ok_items, key
            assert pub.get(key, set()) <= ok_items, (key, sorted(pub.get(key, set())))
    assert n >= 1
    # 상수는 실사용분과 같다(쓰지 않는 항목을 미리 열어 두지 않는다)
    assert used_items & {17, 20, 21} == set(DC.PL_DISCLOSURE_REINSURER_LINEAGE["disclosure_summary_pl_reinsurer"])
    # 트립와이어: 이 허용의 수혜 회사는 owner 지시 범위(재보사 7곳 + 마이브라운)이다. 다른 회사가 들어오면 사람이 보게 한다.
    assert users == {f"KR110{i}" for i in range(1, 9)}
