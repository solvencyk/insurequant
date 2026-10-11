p = "scripts/_data_contract_selftest.py"
s = open(p, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
print("newline", repr(nl))
s = s.replace("\r\n", "\n")

# 1) fixtures after f_pl_concept_allowed_is_clean
anchor = "def f_pl_missing_sidecar():"
new_fx = '''def _fs_note_cell(items, *, how="fs_note_csm_amort", resolution="fs_note_csm_amort",
                  evidence=True, block="contract_notes"):
    """재무제표·감사보고서 주석 계보 셀(2026-10-11, PL_FS_NOTE_LINEAGE) -- 경영공시 PDF 경로 + 주석 how."""
    entry = {"file": DISCLOSURE_SOURCE, "how": how, "items": items}
    if evidence:
        entry.update({"page": 58, "printed": "(15,847,454,365)", "unit": "원"})
    return [{"company_code": "KR9003", "quarter": LATEST, "item_block": block,
             "source_id": "DISCLOSURE", "source_file": DISCLOSURE_SOURCE,
             "source_files": [entry], "resolution": resolution},
            *_pl_base_cells()]


def _fs_note_inject(items, published=None, **kw):
    pub = dict(base_pl_cells()["pl_published_items"])
    pub[("KR9003", LATEST, kw.get("block", "contract_notes"))] = list(published or items)
    return base_inject(provenance_sidecars=_pl_sidecar(_fs_note_cell(items, **kw)),
                       pl_published_items=pub, pl_published_cells=sorted(pub),
                       pl_builder_derived_cells=base_pl_cells()["pl_builder_derived_cells"])


def f_pl_fs_note_item4_is_clean():
    """오탐 금지: how=fs_note_csm_amort + 쪽·인쇄값이 있는 **항목 4** 는 경영공시 PDF 경로여도 정상이다
    (재무제표·감사보고서 주석 계보, owner 2026-10-11)."""
    return _fs_note_inject([4])


def f_pl_fs_note_without_evidence():
    """근거 필드(쪽·인쇄값) 없는 how 는 허용하지 않는다 -- how 문자열만 달아 빠져나가는 경로 차단."""
    return _fs_note_inject([4], evidence=False)


def f_pl_fs_note_item4_wrong_how():
    """등재 안 된 how(`disclosure_pdf`) 의 항목 4 는 종전대로 RED."""
    return _fs_note_inject([4], how="disclosure_pdf", resolution="disclosure_pdf")


def f_pl_fs_note_how_resolution_mismatch():
    """entry how 와 셀 resolution 이 다르면(= 한쪽만 고쳐 단 것) 허용하지 않는다."""
    return _fs_note_inject([4], resolution="disclosure_summary_pl")


def f_pl_fs_note_reference_only_item():
    """how 가 fs_note 여도 reference_only 항목 17(투자손익)은 못 빠진다 -- 허용은 항목 4 한 개다."""
    return _fs_note_inject([17])


def f_pl_fs_note_mixed_with_item17():
    """한 블록에 4 와 17 이 같이 있으면 4 만 빠지고 17 은 RED 로 남는다."""
    return _fs_note_inject([4, 17])


def f_pl_fs_note_other_contract_note_item():
    """contract_notes 블록의 다른 항목(5=원수 위험조정변동)도 못 빠진다 -- 항목 단위 허용."""
    return _fs_note_inject([5])


def f_pl_fs_note_wrong_block():
    """income_statement 블록에 단 fs_note 는 허용하지 않는다(주석 계보는 contract_notes 블록 한정)."""
    return _fs_note_inject([4], block="income_statement")


'''
assert anchor in s
s = s.replace(anchor, new_fx + anchor, 1)

# 2) CASES rows after Q5b
anchor_case = '''    ("Q6 PL MISSING_PROVENANCE_SIDECAR (부재 = RED)", f_pl_missing_sidecar,'''
new_cases = '''    # Q9: 재무제표·감사보고서 주석 계보 허용(PL_FS_NOTE_LINEAGE, owner 2026-10-11) -- 항목 4 한정, 양방향.
    ("Q9  주석 계보 항목 4 (how+쪽+인쇄값) 는 정상 -- finding 0", f_pl_fs_note_item4_is_clean, set()),
    ("Q9b 쪽·인쇄값 없는 how 는 허용 안 함 (CONCEPT_MIXED)", f_pl_fs_note_without_evidence,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q9c 등재 안 된 how 의 항목 4 는 RED", f_pl_fs_note_item4_wrong_how,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q9d how 와 resolution 불일치는 RED", f_pl_fs_note_how_resolution_mismatch,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q9e how 가 있어도 reference_only 항목 17 은 RED", f_pl_fs_note_reference_only_item,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q9f 한 블록의 4+17 은 17 때문에 RED", f_pl_fs_note_mixed_with_item17,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q9g contract_notes 의 다른 항목(5)도 RED -- 항목 단위 허용", f_pl_fs_note_other_contract_note_item,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
    ("Q9h income_statement 블록의 fs_note 는 RED", f_pl_fs_note_wrong_block,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
'''
assert anchor_case in s
s = s.replace(anchor_case, new_cases + anchor_case, 1)

# 3) MT cases
anchor_mt = '''    ("S6 DISCLOSURE 여도 추가 LOB(`2-N`) 가 있으면 검산한다",
     lambda: _mt(_MT_BARE, "DISCLOSURE", extra_lob=300.0),
     {"legcov_fail": 1, "zleg": 0, "na_legcov": 0, "na_zleg": 1}),
'''
new_mt = anchor_mt + '''    # S7~S10: 항목 4(원수CSM상각)는 「sub-leg 전부 결측」 판정에서 다리로 세지 않는다(owner 2026-10-11).
    # 재보사·라이나의 항목 4 는 §2-1 이 아니라 재무제표·감사보고서 주석 값이다.
    ("S7 DISCLOSURE + 항목 4 만 있으면 여전히 원천 미수록 (ZERO_LEGS 오발화 방지)",
     lambda: _mt(dict(_MT_BARE, 원수CSM상각=14903.6), "DISCLOSURE"),
     {"legcov_fail": 0, "zleg": 0, "na_legcov": 1, "na_zleg": 1}),
    ("S8 DISCLOSURE + 항목 4 + 다른 다리 0.0 이면 ZERO_LEGS 가 문다 (항목 4 가 면죄부가 아니다)",
     lambda: _mt(dict(_MT_BARE, 원수CSM상각=14903.6, 생명장기원수손익=0.0), "DISCLOSURE"),
     {"legcov_fail": 0, "zleg": 1, "na_legcov": 1, "na_zleg": 0}),
    ("S9 DISCLOSURE + 항목 4 + 다른 다리 실값이어도 ZERO_LEGS 가 문다",
     lambda: _mt(dict(_MT_BARE, 원수CSM상각=14903.6, 원수위험조정변동=-250.0), "DISCLOSURE"),
     {"legcov_fail": 0, "zleg": 1, "na_legcov": 1, "na_zleg": 0}),
    ("S10 DART 계보는 항목 4 만 있어도 종전대로 ZERO_LEGS (면제는 DISCLOSURE 한정)",
     lambda: _mt(dict(_MT_BARE, 원수CSM상각=14903.6), "DART"),
     {"legcov_fail": 1, "zleg": 1, "na_legcov": 0, "na_zleg": 0}),
'''
assert anchor_mt in s
s = s.replace(anchor_mt, new_mt, 1)
if nl == "\r\n":
    s = s.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(s)
