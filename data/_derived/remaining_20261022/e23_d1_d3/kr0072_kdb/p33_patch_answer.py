# -*- coding: utf-8 -*-
"""wording fixes of the Korean answer (asserted single-hit replacements)"""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "answers" / "kr0072_kdb.md"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60])
    s = s.replace(a, b)


rep("(`c05_drift_evidence.txt`가 아니라 `drift_before.json`의 KR0072 49칸 참조)", "(근거 `c05_drift_evidence.txt`, 이 회사의 손 수정 칸 전체 49칸은 `drift_before.json`)")
rep("KDB는 NB 마스터 14행에 있고 2023.1Q~3Q 연누계가 0.9~3.2억 낡게 되지만 게이트 허용 안이다(publishing NB 재빌드 대상)",
    "KDB는 NB 마스터 14행에 있고 2023.1Q~3Q 신계약 CSM 연누계가 0.9~3.2억 낡게 되지만 게이트 허용 기준(차이 ≤ max(1억, 1%)) 안이라 RED가 안 난다(publishing NB 재빌드 대상)")
rep("FY2025 사업보고서의 제36기 열은 FY2024 전기 열과 값이 모두 같아 재재작성이 없다(이름만 바뀐 줄 포함).",
    "FY2025 사업보고서의 제36기 열은 FY2024 전기 열 69줄과 값이 모두 같아 재재작성이 없다(같은 이름 55줄, 이름만 바뀐 6줄, 폐기된 항목명의 0 값 8줄, 불일치 0).")
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
