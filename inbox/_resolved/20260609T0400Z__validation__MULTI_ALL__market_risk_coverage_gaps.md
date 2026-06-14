---
from: validation
to: parser
created: 20260609T0400Z
status: resolved
route: reparse
company: MULTI (ALL)
period: ALL
rule: 19_market, 36_irr
iter: 1
---

## 미결 (validation 작성)

시장위험 1차 적재 검증 통과(RED 0) 후, **미적재(SKIP) 분기 census**. 전체 머신리더블: `data/_derived/market_risk_coverage.json`.

### A. `19_market` 미적재 = 221 (item19 있는데 item36–40 전부 결측)

회사별 결손 분기 수 (**우선순위 = 대형사·다분기**):

| 결손 분기수 | 회사 |
|---|---|
| **12 (전분기)** | 삼성화재 · 삼성생명 · 라이나생명 · 신한이지손해 |
| **11** | 한화생명 · 현대해상 · KB손해 · KB라이프 · 신한라이프 · 악사손해 · 처브라이프 · DB생명 |
| **10** | DB손해 · NH농협손해 · 동양생명 · 메리츠화재 · 하나손해 |
| 6 | 미래에셋(KR0079, **이미지-only** — OCR 필요) |
| 1–4 | 에이비엘·카카오페이손해·코리안리·교보·흥국생명·서울보증·한화손해·AIG·롯데·비엔피·아이엠·푸본·하나생명·흥국화재 |

**spec §5 파서 가이드 연결** (난이도 높은 추출 패턴):
- **concatenated-cell**(한 셀에 라벨+숫자 뭉침): 현대해상
- **경과조치 전/후 컬럼 정렬**: 한화생명 · KB라이프
- **다중컬럼**(분기별/경과조치별): 에이비엘 · 메트라이프 · 라이나
- 나머지는 "시장위험액 세부내역" 별도 표 추출(메인 요구자본표엔 item19 단일라인만).

### B. `36_irr` 미적재 = 103 (item36 있는데 item41–46 일부 결측)

**85/103이 1Q·3Q** → 분기보고서에 "금리위험액 현황" 시나리오 표가 **구조적으로 없을** 가능성(반기·연간만 공시). spec §7-5: 209/497 filing 존재. 먼저 **1Q/3Q에 시나리오 표가 원천 부재인지 확인** 요청:
- 원천 부재면 → 구조적 SKIP(정상, RED 아님). validation은 그대로 SKIP 유지.
- 표는 있는데 미추출이면 → §7-6 순자산가치 6종(item41–46) 추출.

**나머지 18건은 2Q/4Q 결손** = 진짜 추출 누락 후보 (우선): 교보 2024.4Q·2025.4Q, 케이디비 2025.4Q, 하나생명 2023.4Q·2025.2Q·2025.4Q, 흥국화재 2023.2Q·2023.4Q·2024.2Q, 에이비엘 2023.4Q, 하나손해 2023.4Q, IBK연금 2025.4Q 등. (전체 `market_risk_coverage.json`.)

### 회귀
적재 후 `python scripts/validate_kics_disclosure.py` → 19_market/36_irr GREEN 증가, RED 0 유지 확인.

## 답변 (parser 작성 — 처리 후)

**Census를 추정 아닌 결정적 분류로 회신** (기존 추출함수 재사용, 소스 전수 대조).
Probes: `scripts/_probes/market_gap_census.py` (MD), `scripts/_probes/market_gap_pdf_check.py` (raw PDF).
Machine output: `data/_derived/market_gap_census.json`, `data/_derived/market_gap_pdf_check.json`.

### A. 19_market 미적재 221 — **결정적 분류** (MD에 세부표 없음 → raw PDF로 한 단계 더 확인)

MD 단계: `table_present_fails_recon = 0` (MD에 세부표가 있는데 파싱실패한 건 **0건**).
전부 `table_absent`(191) 또는 `no_md_file`(30) = **MD에 세부표 자체가 없음**. → PDF 원문 대조:

| 분류 | 건수 | 의미 |
|---|---|---|
| **pdf_has_subrisk_table** | **112** | PDF엔 하위5종 세부표 있는데 MD에 미반영 → **PDF(fitz) 추출로 복구가능** (item41-46과 동일 접근). 파서 로직버그 아님 — `extract_mkt_subs`가 MD만 읽음. |
| **pdf_market_total_only** | **100** | PDF에도 세부표 없이 `시장위험액` 합계라인만 → **구조적 비공시 = 정당 SKIP, RED 아님** |
| pdf_image_only | 4 | KB손해 일부 분기 스캔본(OCR 필요) |
| pdf_no_market | 5 | 미래에셋2·KB손해1·악사1·흥국화재1 (시장위험 섹션 이미지/레이아웃) |

**핵심 정정 — validator 전제 보정:** spec §5가 지목한 현대해상(concat)·한화/KB라이프(경과조치 컬럼)·에이비엘/메트라이프/라이나(다중컬럼)는 **1차패스에서 이미 처리돼 GREEN(저장됨)**, 미적재 221에는 없음. 남은 221은 "MD 파싱 패턴" 문제가 **아니라** "PDF→MD에 세부표 미반영" 문제.

**구조적 SKIP 확정(대형사 포함):** 삼성화재(전분기 12, 별도/OFS 포맷)·현대해상 10·삼성생명 10·한화생명 8 등은 PDF에도 하위5종 분해를 **애초에 공시 안 함** → 정당 SKIP. validation은 그대로 SKIP 유지 요청.

**복구가능(112) 상위:** 신한이지손해10·하나손해9·신한라이프8·KB라이프8·악사6·라이나6·처브6·메리츠5·KB손해5·DB손해5·NH농협5·DB생명5·동양5… (전체 by_company는 pdf_check.json). 단 112는 상한치 — PDF 추출 후 reconcile(<2% vs item19) 게이트가 진짜 저장수를 확정.

### B. 36_irr 미적재 103 — validator 가설 확정

| 분류 | 건수 | 처리 |
|---|---|---|
| **scenario_table_absent (Q1/Q3)** | **85** | 1Q/3Q 분기보고서에 "금리위험액 현황" 시나리오 표 **원천부재** → 구조적 SKIP 확정, RED 아님. (validator 가설 그대로) |
| reconciles_storable | 6 | **저장됐어야 하는데 누락** → 로더버그(아래). 케이디비 2025.4Q·비엔피 2024.2Q·교보라이프 2024.2Q/4Q·2025.2Q·IBK연금 2025.4Q (전부 rel 0~4.9%) |
| table_present_no_total | 3 | 교보생명 2024.2Q/2025.2Q/2025.4Q — 순자산행은 있으나 금리위험액 total 토큰 미검출 → total-anchor regex 보강 필요 |
| scenario_table_absent (Q2/Q4) | 5 | 에이비엘 2023.4Q·하나손해 2023.4Q·흥국화재 2023.2Q/2023.4Q/2024.2Q — 확인要(대개 구조적이나 재확인) |
| table_present_fails_recon | 4 | 하나생명 2023.4Q/2025.2Q/2025.4Q·교보라이프 2025.4Q — **직접형/granular**(순자산-델타 재구성 불가), spec §9대로 deferred(직접공시 시나리오위험액 별도 schema 검토) |

**로더버그 발견:** `fill_market_subitems_to_disclosure.py`의 41-46 PDF추출이 **MD파일 루프 내부에 중첩** → MD가 없으면 PDF가 정상이어도 IRR추출을 시도조차 안 함. reconciles_storable 6건이 이 때문(PDF는 reconcile 0%). 수정: MD/PDF code 합집합으로 순회.

### 처리 결론 (route→reparse, Phase-2 대기)
- **복구가능 = 112(19_market PDF추출) + 6(IRR 재적재) + 3(교보 total-anchor) ≈ 121 분기.** 진짜 SKIP = 100(19_market 구조적) + 85(36_irr Q1/Q3 구조적) + 4(직접형 deferred).
- 구현은 **shared 14k행 disclosure JSON 변경 + 필수 K-ICS 검증게이트 재실행**이 따르고 진단이 작업성격을 재정의(로직버그→PDF추출 신규경로)했으므로, Phase-2 빌드 착수 전 오케스트레이터(사람) 범위승인 대기. 승인 시 PDF세부표 추출기 + 로더루프 수정 + 게이트(RED 0) 검증을 Workflow로 진행.

**[UPDATE — Phase-2 DONE 2026-06-09 (e), 오케스트레이터 "전체" 승인]:** PDF 직접추출 빌드 완료. +150행
(19_market 36-40 +96 / IRR 41-46 +54), `kics_disclosure.json` 14,244→14,394. 게이트 **RED=2**(둘 다 KR0010 OCR
documented, 신규 0). `19_market` GREEN 163→185, `36_irr` GREEN 42→47. 신규 스크립트 `fill_market_subs_from_pdf.py`·
`fill_market_irr_from_pdf.py`(기존 로더 무수정). "로더루프 버그" 가설은 오류로 판명(reconciles_storable 6건 전부 MD
존재; 실제 게이트는 PDF총액→item36 대조여야 정확). 완료 회신: `inbox/validation/20260609T0830Z__parser__...phase2_loaded.md`.
잔여 SKIP은 정당(구조적 비공시/원천부재) 또는 직접형(별도 schema) — TODO_parser Phase-2 DONE 블록 참조.

## 종결 (validation 2026-06-14)
coverage gaps → systemic_underparse + fitz백필로 흡수(RED 31→21) → resolved
