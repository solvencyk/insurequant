# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/scripts/_data_contract_selftest.py")
s = p.read_text(encoding="utf-8")
old = '''     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART", "MISSING_PROVENANCE"}),
'''
new = '''     {"CONCEPT_MIXED_DISCLOSURE_INTO_DART"}),
'''
assert s.count(old) == 1
s = s.replace(old, new)
old2 = '''    (계보를 확인 못 한 블록이 있는 회사는 허용 대상이 아니다 -- fail-closed)."""
    inj = _rein_inject'''
new2 = '''    (계보를 확인 못 한 블록이 있는 회사는 허용 대상이 아니다 -- fail-closed). 참고: `verify_provenance_sidecar` 는 블록 불문
    (company, quarter) 폴백 매칭을 해서 이 결측은 MISSING_PROVENANCE 로 안 잡힌다 -- 그래서 허용 쪽이 정확 키로 따로 막는다."""
    inj = _rein_inject'''
assert s.count(old2) == 1
s = s.replace(old2, new2)
p.write_text(s, encoding="utf-8", newline="")
