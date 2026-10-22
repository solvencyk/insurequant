---
from: orchestrator
to: parser
created: 20261022T0900Z
status: open
route: reparse
lane: ifrs17
company: MULTI (KR0082 KR0032 KR0104 KR0087 KR0070 KR0083 KR0005)
period: 2023.3Q-2024.3Q
iter: 1
---

## 미결 (sender 작성)

owner 결정(2026-10-22, 「그럼 걔네도 바꿔라」): 교보생명(KR0073)과 같은 방침(최신 비교열 우선 · 별도 기준 · 블록이 닫힐 때만)으로 **다른 회사 19버킷의 PL_breakdown Tier-1 항목**을 후속 공시의 전기(비교) 열로 갱신한다. 대상 판정표는 `data/_derived/remaining_20261022/d_census/d_census_table.csv` 의 `disposition = OWNER_DECISION` 19행(요약 `INDEX.txt`·`d11_summary.txt`).

| 코드 | 회사 | 분기 | 다른 PL 항목(census) | 비고(census) |
|---|---|---|---|---|
| KR0082 | DB생명 | 2023.3Q | 1,16,17,18 | 인접 2023.1Q·2Q 는 옛 판(이음매 단일분기 공란) |
| KR0032 | NH농협손보 | 2023.4Q · 2024.1Q · 2024.2Q · 2024.3Q | 17,19,20,22,23,24,25,27 | FSS Q&A: 보험금융손익 체계적 배분 변경(순이익 → OCI) |
| KR0104 | 농협생명 | 2023.3Q | 17,18,20,22,23,24,28,31 | 오류 정정(K-IFRS 1109 분류); 인접 2023.1Q·2Q 는 옛 판 |
| KR0087 | 동양생명 | 2023.4Q · 2024.1Q · 2024.2Q · 2024.3Q | 17,19,20,22,23,24,25,27(+31) | 같은 블록 gold 있음(2023.4Q 9~12, 2024.2Q·3Q 4·7; 바뀔 칸과 겹치지 않음) |
| KR0070 | ABL생명 | 2024.1Q · 2024.2Q · 2024.3Q | 17,19,20,22,23,24,25,27 | 같은 블록 gold 4·7 (겹치지 않음) |
| KR0083 | 푸본현대생명 | 2024.1Q · 2024.2Q | 17,19,20,22,23,24,25,27 | 인접 2024.3Q·4Q 는 옛 판 |
| KR0005 | 흥국화재 | 2023.3Q · 2023.4Q · 2024.1Q · 2024.2Q | 17,18,(19),20,22,23,24,25,26,28,31,(32) | 오류 정정(FVOCI 외화채 예상만기); 같은 블록 gold 16 (겹치지 않음) |

### 범위와 원칙
- **범위는 이 19버킷의 Tier-1 PL 항목뿐**이다. CSM 워터폴(19버킷 모두 변동 없음)과 census 의 나머지 32(STAY)·부속 53버킷(`d_census_addl.csv`)은 이번에 안 건드린다. 재보사·마이브라운 범위 밖.
- 전부 별도(OFS) 기준 · 후속 공시의 전기 누적 열. census 는 FS-API 캐시 + XML 85/95 표본 점검이라 **적재 전 필링 XML 줄 번호 전수 재독이 필수**다(census 자체의 단서). 단위(백만원 ↔ 억)와 부호(18·19 항목 부호 정의)를 칸마다 확인.
- 닫힘은 **gold 칸과 채택칸을 합친 최종 벡터**로 본다(25 = 부분합, 31 = 24+25, 20 = 1+17, |22−24| = |23|, LOB 가교 항목 1 = 다리합 + 15 − 16). 닫히지 않는 버킷은 그대로 두고 사유를 적는다. **owner gold 칸을 바꾸지 않는다**(겹치면 그 버킷만 보류).
- 인접 분기가 옛 판으로 남아 단일분기(`값_당분기`)가 두 판에 걸치면 교보 선례대로 공시가 인쇄한 3개월 열이 있으면 `set_dangi`, 없으면 `null_dangi`(빈 칸이 틀린 값보다 낫다). 박제 · 잔차 끼워 맞추기 · 게이트 예외 등재 없음.
- 예상 반응: `PL_OCI_VS_BS_AOCI`(YELLOW) 23 → 26 안팎(BS AOCI 는 원 공시 기준, 이번에 안 건드림), xlsx `손익분해PL` 드리프트, `test_master_tables_golden` SUMMARY(pl_bridge 등) 이동, 화면 순이익·투자손익이 순이익 ↔ OCI 이동만큼 변한다(총포괄손익은 대체로 불변).

### 하면 되는 일
교보 OCI 티켓(`inbox/_resolved/20261021T1556Z__orchestrator__KR0073_2024.4Q-2025.2Q__oci_latest_comparative.md`)의 절차와 같다: gold `user_pl_cells.json` 등재(`was`·`note` 에 근거) → 실제 `build_pl()` 사본 산출로 셀 단위 반영 → `scripts/emit_pl_provenance.py` 샌드박스 사본 산출(**import 금지**) → `GOLD_OVERLAY_CENSUS` PL 튜플 갱신 → 게이트 전후(`validate_master_tables --no-build` · `validate_data_contract` · `validate_csm_continuity`) + `RUN_PL_GOLDEN=1 tests/test_pl_breakdown_golden.py`(보고만, `--update` 금지). 재사용 하네스 `data/_derived/remaining_20261022/a_oci/apply_kr0073_oci.py`. 후보 셀은 census 의 `cand_pl_cells.json`(37버킷 후보 중 19버킷분만) 을 출발점으로 하되 XML 로 다시 확인한 값만 적재한다.

## 답변 (recipient 작성 — 처리 후)
