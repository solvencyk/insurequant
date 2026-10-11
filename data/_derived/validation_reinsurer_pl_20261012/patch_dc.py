# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/scripts/validate_data_contract.py")
s = p.read_text(encoding="utf-8")
assert not s.startswith("\ufeff")

# 1) constants + helpers after _pl_fs_note_exempt_items
anchor = '''        out |= {int(i) for i in (sf.get("items") or []) if str(i).isdigit()} & allowed
    return out
'''
assert s.count(anchor) == 1
new_block = anchor + '''

# 경영공시 요약 포괄손익계산서(§2-1) 계보 PL 셀 중 **DART 사업보고서가 없는 회사**(재보사 KR1101~KR1107 +
# 마이브라운 KR1108)의 reference_only 항목 허용(owner 2026-10-12 「재보사 투자손익·영업외 공란 채우기」).
# {사이드카 `how`: 허용 항목번호}. #17/#20/#21 이 reference_only 인 이유는 **같은 회사 시계열에서 DART 개념(일반회계)과
# 경영공시 개념(감독회계)이 섞이기 때문**이다. 이 회사들은 원천이 경영공시 하나뿐이라 섞일 DART 칸이 없다 --
# 그래서 이 허용은 면제 등재가 아니라 계보 규칙의 정당한 확장이고, 아래 네 조건이 **전부** 맞을 때만 연다:
#   ① 회사의 사이드카 셀이 전부 DISCLOSURE 계보 + 마스터가 발행한 블록이 전부 사이드카에 있다(데이터 조건, 코드 목록 아님)
#   ② 블록이 income_statement 이고 entry `how` 가 이 표에 등재돼 있다 (`resolution` 은 기본 적재 라벨이라 비교하지 않는다)
#   ③ entry 가 쪽(page/pages)을 갖고 ④ **항목마다** 인쇄값(printed[str(항목)])이 비어 있지 않다
# 허용은 그 entry 의 items ∩ 등재 항목 **한 칸씩**만 뺀다. 항목을 늘리려면 이 상수 + selftest Q11 + 변이시험
# (`tests/test_pl_reinsurer_disclosure_lineage.py`)을 같이 고쳐야 한다. 상수는 사이드카 실사용분과 시험이 대조한다.
PL_DISCLOSURE_REINSURER_LINEAGE: dict[str, frozenset] = {
    "disclosure_summary_pl_reinsurer": frozenset({17, 20, 21})}


def _pl_dartless_companies(cells: list, published_keys) -> set:
    """DART 계보 PL 셀이 하나도 없는 회사 집합(fail-closed).

    회사의 사이드카 셀이 1개 이상이고 **전부** source_id·source_file 경로 계보가 DISCLOSURE 이며, 마스터가 값을
    발행한 (회사,분기,블록) 이 전부 사이드카에 있어야 들어온다. 셀 하나라도 DART·미등록·결측이면 제외된다."""
    ok: dict = {}
    for c in cells or []:
        co = c.get("company_code")
        if not co:
            continue
        good = (c.get("source_id") == PL_DISCLOSURE_SOURCE_ID
                and source_id_for_lineage(c.get("source_file")) == PL_DISCLOSURE_SOURCE_ID)
        ok[co] = ok.get(co, True) and good
    side_keys = {(c.get("company_code"), c.get("quarter"), c.get("item_block")) for c in cells or []}
    for k in published_keys or ():
        if k not in side_keys:
            ok[k[0]] = False
    return {co for co, v in ok.items() if v}


def _pl_reinsurer_exempt_items(cell: dict, dartless: set) -> set:
    """이 PL 사이드카 셀에서 `PL_DISCLOSURE_REINSURER_LINEAGE` 가 §3d 제한에서 빼주는 항목번호 집합(fail-closed).

    DART 없는 회사 · income_statement 블록 · 등재 how · DISCLOSURE 경로 · 쪽 · **항목별** 인쇄값이 모두 있을 때만
    그 entry 의 `items` 중 등재 항목을 돌려준다."""
    if cell.get("company_code") not in dartless or cell.get("item_block") != "income_statement":
        return set()
    out: set = set()
    for sf in cell.get("source_files") or []:
        allowed = PL_DISCLOSURE_REINSURER_LINEAGE.get(sf.get("how"))
        if allowed is None or source_id_for_lineage(sf.get("file")) != PL_DISCLOSURE_SOURCE_ID:
            continue
        printed = sf.get("printed")
        if not (sf.get("page") or sf.get("pages")) or not isinstance(printed, dict):
            continue
        out |= {int(i) for i in (sf.get("items") or [])
                if str(i).isdigit() and int(i) in allowed and printed.get(str(i)) not in (None, "")}
    return out
'''
s = s.replace(anchor, new_block)

# 2) use in check_cross_source
a2 = '''    _pl_fs_note_cells = _pl_fs_note_items = 0
    for _c in _pl_side.get("cells") or []:'''
assert s.count(a2) == 1
s = s.replace(a2, '''    _pl_fs_note_cells = _pl_fs_note_items = 0
    _pl_rein_cells = _pl_rein_items = 0
    _pl_dartless = _pl_dartless_companies(_pl_side.get("cells") or [], env.pl_published_cells)
    _pl_rein_cos: set = set()
    for _c in _pl_side.get("cells") or []:''')

a3 = '''        _disc -= _fs_note
        _disc &= _pub
'''
assert s.count(a3) == 1
s = s.replace(a3, '''        _disc -= _fs_note
        # 경영공시 요약 PL 계보의 reference_only 항목 허용 -- DART 없는 회사 한정(owner 2026-10-12). 위 상수 주석 참조.
        _rein = _pl_reinsurer_exempt_items(_c, _pl_dartless)
        if _rein:
            _pl_rein_cells += 1
            _pl_rein_items += len(_disc & _rein & _pub)
            _pl_rein_cos.add(_key[0])
        _disc -= _rein
        _disc &= _pub
''')

a4 = '''f"{ {k: sorted(v) for k, v in PL_FS_NOTE_LINEAGE.items()} } · 그 항목 값은 워터폴과 별도 대조(PL_CSM_AMORT_VS_WATERFALL)")
'''
assert s.count(a4) == 1
s = s.replace(a4, a4 + '''    res.notes.append(
        f"cross_source guard (경영공시 요약 PL 계보 reference_only 허용, DART 없는 회사 한정): {_pl_rein_cells}셀 / "
        f"{_pl_rein_items}값 제외 · 회사 {sorted(_pl_rein_cos)} (DART 계보 없는 회사 {len(_pl_dartless)}곳) · 허용 {{how: 항목}} = "
        f"{ {k: sorted(v) for k, v in PL_DISCLOSURE_REINSURER_LINEAGE.items()} } · 인쇄값·쪽 없는 항목은 계속 RED")
''')
p.write_text(s, encoding="utf-8", newline="")
print("ok")
