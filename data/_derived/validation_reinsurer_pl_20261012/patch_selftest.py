# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/scripts/_data_contract_selftest.py")
s = p.read_text(encoding="utf-8")

fix = '''

# --- Q11: 경영공시 요약 PL 계보 reference_only(17/20/21) 허용 -- DART 없는 회사 한정(owner 2026-10-12) ---------
REIN_HOW = "disclosure_summary_pl_reinsurer"


def _rein_cell(items, *, company="KR9004", how=REIN_HOW, page=58, printed="auto", block="income_statement"):
    """재보사형 셀: 경영공시 PDF 경로 + 재보사 how + (쪽, 항목별 인쇄값 dict)."""
    entry = {"file": DISCLOSURE_SOURCE, "how": how, "items": items}
    if page:
        entry["page"] = page
    if printed == "auto":
        printed = {str(i): "12" for i in items}
    if printed is not None:
        entry["printed"] = printed
    return {"company_code": company, "quarter": LATEST, "item_block": block,
            "source_id": "DISCLOSURE", "source_file": DISCLOSURE_SOURCE,
            "source_files": [entry], "resolution": "disclosure_summary_pl"}


def _rein_inject(items, *, published=None, with_dart=False, **kw):
    company = kw.get("company", "KR9004")
    block = kw.get("block", "income_statement")
    cells = [_rein_cell(items, **kw), *_pl_base_cells()]
    pub = dict(base_pl_cells()["pl_published_items"])
    pub[(company, LATEST, block)] = list(published or items)
    if with_dart:    # 같은 회사에 DART 계보 셀이 하나라도 있으면 시계열이 섞인다 -> 허용 없음
        cells.append({"company_code": company, "quarter": "2025.4Q", "item_block": "income_statement",
                      "source_id": "DART", "source_file": PL_SOURCE,
                      "source_files": [{"file": PL_SOURCE, "how": "fs_api_tier1", "items": [1, 24]}]})
        pub[(company, "2025.4Q", "income_statement")] = [1, 24]
    return base_inject(provenance_sidecars=_pl_sidecar(cells),
                       pl_published_items=pub, pl_published_cells=sorted(pub),
                       pl_builder_derived_cells=base_pl_cells()["pl_builder_derived_cells"])


def f_pl_rein_item17_20_21_is_clean():
    """오탐 금지: DART 없는 회사 + 재보사 how + 쪽 + 항목별 인쇄값이 있는 17/20/21 은 정상이다."""
    return _rein_inject([17, 20, 21])


def f_pl_rein_company_has_dart_cell():
    """같은 회사에 DART 계보 셀이 있으면(시계열이 섞인다) 증거가 완전해도 RED."""
    return _rein_inject([17, 20, 21], with_dart=True)


def f_pl_rein_unregistered_how():
    return _rein_inject([17, 20, 21], how="disclosure_summary_pl")


def f_pl_rein_item_without_printed():
    """항목 21 의 인쇄값이 없으면 21 만 RED -- 허용은 항목별 증거다."""
    return _rein_inject([17, 20, 21], printed={"17": "12", "20": "445"})


def f_pl_rein_printed_not_dict():
    return _rein_inject([17, 20, 21], printed="12")


def f_pl_rein_without_page():
    return _rein_inject([17, 20, 21], page=None)


def f_pl_rein_item_not_registered():
    """등재 밖 항목 18(투자이익)은 같은 entry 에 실려도 못 빠진다."""
    return _rein_inject([17, 18])


def f_pl_rein_published_beyond_entry_items():
    """마스터가 17 도 발행하는데 entry 의 items 에는 [20, 21] 뿐 -> 17 은 증거 없는 DISCLOSURE 값이라 RED."""
    return _rein_inject([20, 21], published=[17, 20, 21])


def f_pl_rein_wrong_block():
    return _rein_inject([17], block="contract_notes")
'''
anchor = '''def f_pl_missing_sidecar():'''
assert s.count(anchor) == 1
s = s.replace(anchor, fix.lstrip("\n") + "\n\n" + anchor)

cases_anchor = '''    ("Q6 PL MISSING_PROVENANCE_SIDECAR (부재 = RED)", f_pl_missing_sidecar,'''
assert s.count(cases_anchor) == 1
cases = '''    # Q11: 경영공시 요약 PL 계보 reference_only(17/20/21) 허용 -- DART 없는 회사 한정, 양방향.
    ("Q11  DART 없는 회사의 17/20/21 (재보사 how+쪽+항목별 인쇄값) 는 정상 -- finding 0",
     f_pl_rein_item17_20_21_is_clean, set()),
    ("Q11b 같은 회사에 DART 계보 셀이 있으면 RED", f_pl_rein_company_has_dart_cell,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q11c 등재 안 된 how 는 RED", f_pl_rein_unregistered_how, {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q11d 항목별 인쇄값이 없는 항목은 RED", f_pl_rein_item_without_printed,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q11e 인쇄값이 dict 가 아니면 RED", f_pl_rein_printed_not_dict, {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q11f 쪽이 없으면 RED", f_pl_rein_without_page, {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q11g 등재 밖 항목(18)은 RED", f_pl_rein_item_not_registered, {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q11h entry 가 안 싣는 발행 항목(17)은 RED", f_pl_rein_published_beyond_entry_items,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q11i contract_notes 블록은 RED", f_pl_rein_wrong_block, {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
'''
s = s.replace(cases_anchor, cases + cases_anchor)
p.write_text(s, encoding="utf-8", newline="")
print("ok")
