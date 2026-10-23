# -*- coding: utf-8 -*-
"""second wording / accuracy pass of the Korean answer (asserted single-hit replacements)"""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "answers" / "kr0072_kdb.md"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:70])
    s = s.replace(a, b)


rep("### 케이디비생명보험 KR0072 · D3 (시나리오 N5_KDB_FY2023) — 보류(held), 트리는 적재 전 상태로 복구했다",
    "### 케이디비생명보험 KR0072 · D3 (시나리오 N5_KDB_FY2023): 보류(held), 트리는 적재 전 상태로 복구했다")
rep("지시(새 RED/FAIL이 생기면 그 회사를 통째로 되돌리고 보류)에 따라 8개 파일을 백업에서 복구했다.",
    "지시(새 RED/FAIL이 생기면 그 회사를 통째로 되돌리고 보류)에 따라 적재한 8개 파일과 테스트가 덮어쓴 부수 산출 2개를 백업에서 복구했다(원인 확인용으로 한 번 더 적용했다가 다시 복구했다).")
rep("매니페스트(검사 범위 선언표)가 항목 23을 「좁은 커버리지」로 선언한 이유는 이 항목을 알아채는 유일한 길이 KDB 2023.2Q의 우연이기 때문이다.",
    "매니페스트(검사 범위 선언표)가 항목 23을 「좁은 커버리지」로 선언한 이유는 이 항목을 알아채는 길이 「다시 계산한 값이 우연히 정확히 0.0이 되는 칸」뿐이기 때문이고, 지금까지 그 칸은 KDB 2023.2Q였다(매니페스트의 2026-09-12 기록과 후보 칸 분석).")
rep("그래서 화면의 보험손익 +51.6억은 정의 보정 +53.5억과 재작성 효과 +105.1억이 섞인 값이다.",
    "그래서 화면의 보험손익 +51.6억은 같은 정의 기준 재작성 효과 +105.1억에서 옛 값이 기타사업비용 53.5억을 안 뺐던 정의 차이를 뺀 값이다.")
rep("계산기가 모호하다며 보류해 둔 항목 15·17·18은", "빌더의 손입력표(`_GOLD_CELL_OVERRIDE`) 주석이 옛 양식 매핑이 모호하다며 보류해 둔 항목 15·17·18은")
rep("라이브 마스터의 2023.2Q·3Q 항목 7, 12, 2023.2Q 항목 16은 2026-10-11 A2 정정 때 손으로 고친 값이라 gold에 없고, 새로 빌드하면 되돌아간다",
    "라이브 마스터의 2023.2Q·3Q 항목 7·12는 2026-10-11 A2 레그 정정 뒤 직접 고친 식 값이고 2023.2Q 항목 16은 경영공시 PDF 값(5,400)을 직접 넣은 칸이라 gold에 없고, 새로 빌드하면 되돌아간다")
rep("CSM ⓐ 5칸은 원 인쇄값과 0.05억 이내로 같다(2023.2Q 항목 4만 −685.55 대 인쇄 −685.51).",
    "CSM ⓐ 5칸은 원 인쇄값과의 차이가 모두 0.05억 이내이다(2023.1Q 항목 4는 −833.3 대 −833.33, 2023.2Q 항목 4는 −685.55 대 −685.51).")
rep("master_tables_golden은 예상한 SUMMARY 필드(pl_bridge · qoq_warn · oci_vs_bs_aoci) 때문에 실패했고 `--update`는 보류 중이라 안 돌렸다. 입력 지문 점검은 viz_ifrs17_panels 한 줄이 RED(예상, CSM_waterfall 입력 변경).",
    "master_tables_golden은 예상한 SUMMARY 필드(pl_bridge · qoq_warn · oci_vs_bs_aoci) 때문에 실패했다(예상). 입력 지문 점검은 viz_ifrs17_panels 한 줄이 RED이다(예상, CSM_waterfall 입력 변경). 보류라서 두 fixture의 `--update`는 하지 않았다.")
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
