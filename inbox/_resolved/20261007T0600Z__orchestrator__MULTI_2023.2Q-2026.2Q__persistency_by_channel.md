---
from: orchestrator
to: parser
created: 20261007T0600Z
status: resolved
route: backlog
company: ALL (39사)
period: 반기·결산 7개 분기 (2023.2Q·4Q, 2024.2Q·4Q, 2025.2Q·4Q, 2026.2Q)
rule: NEW_DOMAIN_PERSISTENCY_CHANNEL
lane: kics
iter: 1
---

## 미결 (sender 작성)

신규 도메인(owner 2026-10-07, 팀장 요청): **판매채널별 계약유지율**. 홈페이지 표시는 아직 정하지 않았다 —
이번 티켓은 **전사 × 전기간 추출 + 자기검증까지만**. 루트 마스터·HTML 은 만들지 않는다.

### 원천

정기경영공시 PDF `7-6. 불완전판매비율, (청약철회비율 및) 유지율 현황` 안의 유지율 표.
위치 헬퍼 `scripts/_disclosure_pdf_paths.py`(raw/ 우선, 없으면 pdf/). 분기공시(1Q·3Q)는 축약본이라
이 표가 없다 — 반기·결산(2Q·4Q)만 대상. 회사·분기별 쪽수는 아래 「census」 참고.

- 열(채널, 협회 표준 서식): 설계사 · 개인대리점 · 법인대리점{금융기관보험대리점 · TM · 홈쇼핑 · 기타} ·
  직영{임직원 · 복합 · 다이렉트} · 중개사 · 기타 = **11채널**. 분기·회사마다 열 이름 변형이 있을 수 있으니
  표준 코드로 매핑하고 원문 라벨은 그대로 남긴다(매핑 불가 열은 버리지 말고 `채널=UNMAPPED` + 원문).
- 행: 13회차 · 25회차 · 37회차 · 61회차 각각 유지율(%) / 유지계약액 / 대상신계약액.
- 단위는 표 머리의 단위를 그대로 기록(대부분 백만원). 손보는 장기보험 기준.

### 산출

1. `scripts/extract_persistency_channel.py` — 패턴은 `scripts/extract_management_indicators.py`·
   `scripts/extract_asset_quality.py`(fitz raw PDF 1차, 텍스트 없으면 docling MD 폴백, 스캔 예외 명시).
   `page.find_tables()` 가 점선 칸을 못 나눠 숫자가 붙는 회사가 있다(삼성화재 2026.2Q p59: `89.36928,0841,038,620`).
   단어 좌표(`page.get_text("words")`)로 열을 가르고, 아래 항등식으로 쪼개기를 검산하라.
2. `data/persistency/persistency_channel.json` — long format 1행 = (회사, 분기, 회차, 채널):
   `원보험사코드 · 원수사명 · 생손보여부 · 공시분기 · 회차 · 채널 · 채널_원문 · 유지율 · 유지계약액 · 대상신계약액 · 단위 · 출처(file, page) · 추출방식(text|md|vision)`.
   원문 `-` 는 0 이 아니라 null(+ `dash: true`).
3. `data/persistency/census.csv` — 기대그리드(회사 × 7개 분기) 전 칸: `FILLED` / `ABSENT_IN_SOURCE`(근거: 표 머리·문장) /
   `UNREADABLE`(240dpi 렌더 확인 후) / `SCAN_PENDING`(스캔본, 별도 vision 에이전트가 채움). 빈 칸 없이.
4. 스캔본 병합: vision 에이전트가 `data/persistency/vision_cells.json`(같은 스키마, 추출방식=vision)에 쓴다.
   추출기는 이 파일이 있으면 해당 (회사, 분기)를 병합하고 census 를 `FILLED(vision)` 로 바꾼다. 이 파일은 네가 쓰지 마라.

### 자기검증 (무답지)

- 셀 항등식: |유지율 − 유지계약액 ÷ 대상신계약액 × 100| ≤ 0.06 (반올림). 깨지면 RED 목록.
- 회사 합 대조: Σ채널 유지계약액 ÷ Σ채널 대상신계약액 vs `management_indicators.json` 의 `계약유지율_13/25/37/61회차`
  (같은 회사·분기, 1-2 표). 정의 차이로 안 맞을 수 있으니 차이만 표로 보고(단정 금지).
- 범위: 유지율 0~100 밖, 회차가 올라갈수록 유지율이 뛰는 채널은 플래그만.

### 하지 말 것

- 루트 마스터(`management_indicators.json`·`kics_disclosure.json` 등)·HTML·게이트·테스트 수정 금지. 커밋 금지(오케스트레이터가 리뷰 후 커밋).
- 스캔본을 즉흥 OCR 하지 마라(`SCAN_PENDING` 으로 남김).
- 멀티라인 `python -c` 금지(스크립트 파일). 파일 I/O 는 `encoding` 명시. 파이썬 풀패스.

## 답변 (recipient 작성 — 처리 후)

**진행 로그 (P3, 이어받기 2026-10-07 15시대 -- 최종 답변은 아래 「P3 최종」 블록이 생기면 그것이 정본)**
- 15:25 1단계 끝: 인자 없는 전체 실행 226초, `data/persistency/{persistency_channel.json 10,312행, census.csv 277칸, selfcheck.csv}` 갱신. census = FILLED 236 · FILLED(vision) 18 · ABSENT_IN_SOURCE 19 · NO_RAW_PDF 3(KR0150 2023.2Q·2024.2Q·2025.2Q) · RAW_TRUNCATED 1(KR0075 2024.2Q). KR0010 2024.4Q·2026.2Q = FILLED(vision), KR0074 2023.2Q = FILLED(text p37-38, 8열, `ㅡ` 대시 패치로 이미 풀림 -- SCAN_PENDING 아님). 항등식 break 17건 = 원문오기 등재 16 + 미등재 1(KR0097 2024.4Q p88 37회차 설계사, 450dpi 렌더 재확인 -> 인쇄 그대로라 source_errata.csv 에 RATE_INCONSISTENT 로 17행째 등재).
- 남은 일: 3(항등식 재집계는 마지막 재실행에서) · 4 회사합 triage · 5 마스터 변환기 · 6 최종 답변.
- 16:1x 산출 확보: `scripts/build_persistency_master.py` -> `data/persistency/master_persistency.{json,csv}` 10,312행(원본 1:1 검산 통과), `scripts/triage_persistency_company_sum.py` -> `data/persistency/company_sum_triage.csv` 87칸(MI_COLUMN_SHIFT 8 · DEFINITION 26 · SOURCE 53 · PARSE_ERROR 0 · UNKNOWN 0). 남은 일: 추출기 단위(`천`->천원)·이름 패치 반영 최종 재실행 -> 변환기·triage 재실행 -> 최종 답변.
- 15:41 (두 번째 시도) 전체 재실행 278초 완료: census 277칸 = FILLED 236 · FILLED(vision) 18 · ABSENT_IN_SOURCE 19 · NO_RAW_PDF 3 · RAW_TRUNCATED 1, 행 10,312. 항등식 break 17건 = 원문오기 등재 17 / 미등재 0, 경고 0. 다음: 5 마스터 변환기 먼저(산출 파일 확보) -> 4 triage.

**P3 최종 (17:50, 오케스트레이터 대행 — P3 는 16:33 사용 한도로 마지막 재실행 직후 죽었다)**
- 최종 전체 실행(16:27~16:39, 704초, 단위 `천`->천원·회사명 패치 반영): `persistency_channel.json` 10,312행, census 277칸 = FILLED 236 · FILLED(vision) 18 · ABSENT_IN_SOURCE 19 · NO_RAW_PDF 3(KR0150 2023.2Q·2024.2Q·2025.2Q) · RAW_TRUNCATED 1(KR0075 2024.2Q, downloader 티켓 열림). SCAN_PENDING 0.
- 항등식(유지율 = 유지계약액/대상신계약액) break 17건 = 전부 원문 오기로 `data/persistency/source_errata.csv` 등재, 미등재 0. 보정 9건. vision-텍스트 차이 0건.
- 그 실행 기준으로 마스터·분류 재생성: `master_persistency.{json,csv}` 10,312행(= 44행×176칸 + 32행×78칸(2023 8열 서식) + 36행×2칸(9열), 원본<->JSON<->CSV 1:1 검산 통과), `company_sum_triage.csv` 87칸 = SOURCE 53 · DEFINITION 26 · MI_COLUMN_SHIFT 8(관리지표 마스터 쪽 버그, 별도 티켓 T1300Z) · PARSE_ERROR 0 · UNKNOWN 0.
- KR0074 2023.2Q 옛 통합서식 = FILLED(text p37-38).

## 오케스트레이터 검증·종결 (23:2x)
- P4 반영 후 재실행본 기준: census 277칸(FILLED 236·vision 18·ABSENT 19·NO_RAW_PDF 3(KR0150 최종)·RAW_TRUNCATED 1), 마스터 10,312행 1:1 검산 통과. resolved.
