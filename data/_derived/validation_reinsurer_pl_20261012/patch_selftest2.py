# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/scripts/_data_contract_selftest.py")
s = p.read_text(encoding="utf-8")
a = '''def f_pl_rein_wrong_block():
    return _rein_inject([17], block="contract_notes")
'''
assert s.count(a) == 1
s = s.replace(a, a + '''

def f_pl_rein_published_block_missing_from_sidecar():
    """마스터가 값을 발행하는 다른 블록(contract_notes)이 사이드카에 없으면 그 회사는 「DART 없는 회사」로 못 센다
    (계보를 확인 못 한 블록이 있는 회사는 허용 대상이 아니다 -- fail-closed)."""
    inj = _rein_inject([17, 20, 21])
    pub = dict(inj["pl_published_items"])
    pub[("KR9004", LATEST, "contract_notes")] = [5]
    inj["pl_published_items"] = pub
    inj["pl_published_cells"] = sorted(pub)
    return inj
''')
c = '''    ("Q11i contract_notes 블록은 RED", f_pl_rein_wrong_block, {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
'''
assert s.count(c) == 1
s = s.replace(c, c + '''    ("Q11j 계보 미확인 발행 블록이 있는 회사는 허용 대상 아님", f_pl_rein_published_block_missing_from_sidecar,
     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART", "MISSING_PROVENANCE"}),
''')
p.write_text(s, encoding="utf-8", newline="")
