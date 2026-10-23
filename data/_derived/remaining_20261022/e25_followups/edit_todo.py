# -*- coding: utf-8 -*-
"""Edit TODO_parser_ifrs17.md (UTF-8, LF): add the 22nd Status entry on top, update the open items that this batch resolved, add the two new decisions.  Anchors must match exactly once."""
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/TODO_parser_ifrs17.md")
s = p.read_bytes().decode("utf-8")
assert "\r\n" not in s
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
rep("> 갱신 2026-10-23 · 프롬프트", "> 갱신 2026-10-24 · 프롬프트")
NEW = """- **2026-10-24 22차: 후속 티켓 4건 + CSM 단일분기 빈칸 장치 — PL 값 32칸(신규 29 · 제자리 교체 1[ABL 2023.1Q 항목 7] · KB손보 손입력 2칸 제거) + CSM `값_당분기` 3칸 (티켓 `1130Z` · `1210Z` · `0600Z` · `20261024T0100Z` · `1215Z` 건 2, 미커밋)** — 박제·핀·잔차·예외 0, 칸마다 필링 줄 번호 독립 재독 227 checks 문제 0.
  KB라이프 2023.1Q 항목 9·11·12(2Q 단일분기 -1,118/-27/763) · ABL FY2023 항목 5·6·7·9·10(2023.1Q 항목 5 = 272 는 재보험 표 오추출 → 3,593; 항목 7 gold 낡음 → -1,328.36) · 농협생명 2024.1Q·2Q 항목 17·18·20·21(2024.3Q 이음매 닫힘) · KB손보 항목 16 의 60,900/33,300 = 경영공시 요약 PL 행(다른 개념)을 1차 백백필이 손입력한 값 → 빈칸.
  CSM `null_dangi` 장치(`build_root_masters._csm_null_dangi_keys`) 신설 + 롯데 2023.4Q 항목 3·4·5 단일분기 빈칸(항목 2·1·6 은 안 섞여 유지). 게이트: pl_bridge 3783P → 3787P/18F/0NEW 외 SUMMARY 불변 · data_contract RED 0 → 2(xlsx 드리프트 `손익분해PL` 66 + `CSM워터폴` 3 = 바뀐 칸 수) · 골든 `--update` 2줄(SUMMARY · 입력 지문) · PL 골든 · viz 2종 통과.
  남은 것: KB손보 항목 16 원문 6칸(2024.3Q~2025.4Q) 복원 = 새 박제 6건 필요 → 결정 / ABL 2024.1Q~3Q 항목 5 오추출 · FY2023 항목 11·12 / publishing = xlsx 2시트 · panel. 근거·재현 `data/_derived/remaining_20261022/e25_followups/`(`INDEX.txt` · `x01_verify_e25.py`) · changelog 22차.
"""
rep("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + NEW)
# open items
rep("  - ② 롯데 CSM 2023.4Q 단일분기 항목 3·4·5 +105.5억: CSM 빌더에 칸 단위 빈칸 장치(PL `null_dangi` 같은 것)가 없다. 설계 + `GOLD_OVERLAY_CENSUS` · 변이시험이 따르고, 미루면 알려진 한계(`1215Z` 건 2). KB라이프 2023.4Q 단일분기 14칸은 같은 판끼리의 차이라 `null_dangi` 가 필요 없다(`1215Z` 건 1, validation 판정).",
    "  - ② (22차 해소) 롯데 CSM 2023.4Q 단일분기 항목 3·4·5 +105.5억: CSM `null_dangi` 장치를 신설해 3칸을 비웠다(`1215Z` 건 2, answered). KB라이프 2023.4Q 단일분기 14칸은 같은 판끼리의 차이라 `null_dangi` 가 필요 없다(`1215Z` 건 1, validation 판정).")
rep("  - ③ 옛 판 하위항목(헤드라인 불변, 단일분기만 이상): KB라이프 2023.1Q 항목 9·11·12(`1130Z`) · ABL 항목 5·9·10 + 2023.1Q 항목 5 오추출 272(HEAD 에도 있던 오류) + 항목 7 gold 재검산(`1210Z`) · KDB 항목 5·6·9·10·11(`1255Z`, ① 과 같은 라운드).",
    "  - ③ 옛 판 하위항목(헤드라인 불변, 단일분기만 이상): KB라이프 `1130Z` · ABL `1210Z`(FY2023 항목 5·6·7·9·10) 는 22차에서 적재(answered). 남은 것 = KDB 항목 5·6·9·10·11(`1255Z`, ① 과 같은 라운드).")
rep("  - ⑥ publishing: xlsx `CSM워터폴` 124 · `손익분해PL` 466칸 · `NB_CSM_multiple`", "  - ⑥ publishing: (22차 몫 추가 = xlsx `손익분해PL` 66칸 · `CSM워터폴` 3칸, 농협생명·KB라이프·ABL·KB손보·롯데 CSM) · xlsx `CSM워터폴` 124 · `손익분해PL` 466칸 · `NB_CSM_multiple`")
NEWITEMS = """  - ⑦ **결정(owner/오케스트레이터): KB손보 KR0010 항목 16 원문 6칸 복원** — 2024.3Q 284,474 · 2024.4Q 380,949 · 2025.1Q 91,927 · 2025.2Q 190,741 · 2025.3Q 283,832 · 2025.4Q 388,289(DART 별도 행 재독, 줄 번호 `kr0010_kbsonbo/k01_item16_series.txt`). `_zero_other_expense` 가 이 회사 항목 16 을 매 분기 지우고 gold 가 2023.1Q~2024.2Q · 2026.1Q·2Q 에만 있다. 값이 빌더 소스와 같아 gold 로 실으면 마스크 칸 → 새 박제 6건(선례: 같은 항목 박제 6건 2026-08-30) 필요해 이번엔 싣지 않았다(티켓 `20261024T0100Z`). 대안 = `_zero_other_expense` 변경(PL 골든·전 회사 영향).
  - ⑧ (발견, 범위 밖) ABL 2024.1Q~3Q 항목 5 = 196/369/578 은 재보험 RA 오추출(원수 3,275/6,556/9,661), 2024.4Q 항목 5 12,282 ≠ 주석·롤포워드 13,655 · 항목 10 -785 ≠ -793, 2024.1Q~3Q 항목 9·10 빈칸(-2,249/-4,437/-6,746 · -196/-373/-583), 2024.1Q~3Q 항목 7 gold 는 오추출 5 로 계산, FY2023 항목 11(874/1,793/3,129/2,993)·12 미적재. 같은 읽기로 닫히는 값이 `kr0070_abl/a01_read_abl_fy2023.txt` · `a02_control_current_cols.txt` 에 있다.
"""
rep("  - ⑥ publishing:", "  - ⑥ publishing:")  # anchor check
i = s.index("  - ⑥ publishing:")
j = s.index("\n", i) + 1
s = s[:j] + NEWITEMS + s[j:]
p.write_bytes(s.encode("utf-8"))
print("ok")
