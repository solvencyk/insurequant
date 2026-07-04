---
from: downloader
to: parser
created: 20260703T1200Z
status: open
route: extract
company: KR1011 IBK연금보험
period: FY2023~FY2025
lane: ifrs17
---

## 핸드오프 (downloader → parser-ifrs17) — IBK연금보험 IFRS17 raw 준비 완료

owner inbox `20260703T1138Z` 후속. IBK연금보험 DART 수집·추출 완료.

### 수집 결과

- **루트**: A형 공시(분기/반기/사업보고서) 없음 (비상장 전업 연금사). F형(감사보고서)만 존재.
- **DART 회사명**: 아이비케이연금보험 (corp_code: 00844635)
- **K-ICS 원수사명**: IBK연금보험 (KR1011)

| 회계연도 | rcept_no | 제출일 |
|---|---|---|
| FY2023 (2023.12) | 20240328000905 | 2024-03-28 |
| FY2024 (2024.12) | 20250328000503 | 2025-03-28 |
| FY2025 (2025.12) | 20260331004893 | 2026-03-31 |

※ FY2022(20230407)은 수집됐으나 CSM=0 (IFRS17 전환 전) — 파싱 대상 제외.

### 추출 artifact (data/dart/extracted/)

각 연도별 7종:
- `아이비케이연금보험_<rcept>_csm.json` (FY2023: 2개 테이블, FY2024: 1개, FY2025: 1개)
- `아이비케이연금보험_<rcept>_measurement.json` + `_mvp.json`
- `아이비케이연금보험_<rcept>_insurance_pl.json` + `_mvp.json`
- `아이비케이연금보험_<rcept>_sensitivity.json` + `_mvp.json`

### 회사 특성 (파서 참고)

- **연금/저축성 전업사**: 생보와 동일 GMM 일반모형 적용 (전체 계약 대부분 연금).
- **PAA 적용 비중**: 극히 낮을 것 (단기 일반손보 0). slice_policy = `whole_company_life`.
- **자동차·일반손보 항목 0**: CSM/PL에서 장기보험 전체가 메인.
- **유배당 가능성**: 연금전업사이므로 유배당 계약 비중 확인 필요.
- **측정모형 컬럼**: FY2025 csm.json 캡션에 포트폴리오 열 있음 — A형 다중 포트폴리오 구조.
- **단위**: 천원 (원/억원 아님). 파서 스케일 적용 필수.

### 요청

1. CSM_waterfall.json 및 PL_breakdown.json에 KR1011 IBK연금보험 행 적재.
2. 가정민감도(sensitivity) 추출 확인.
3. 분기 데이터 없음 — 연간(FY.4Q) 포인트만. 워터폴 시계열 연간 3포인트(2023.4Q, 2024.4Q, 2025.4Q).
4. 추출 완료 후 publishing inbox로 "IBK연금 마스터 적재 완료" 통보.

## 답변 (parser-ifrs17, 2026-07-04) — CSM 워터폴 적재 완료 / PL·민감도 focused 후속

**진행 결정(owner 2026-07-04)**: IBK연금은 신규사 온보딩이라 CSM 먼저 조립·검증·적재, PL은 focused 후속.

### ✅ 완료 — CSM_waterfall.json 적재 (18레코드 = 6항목×3개년)
IBK measurement 표가 빌더 STAGE_ROWS와 라벨이 달라(`waterfall_for_dir` None 반환) **hand-assemble**:
- 소스: `아이비케이연금보험_<rcept>_measurement.json` **block[0] = 연금과저축보험 당기(별도) = whole-book** (검증: 유배당+무배당 = 연금과저축 소계, 그리고 3개년 continuity chain).
- **컬럼 = 보험계약마진 소계(col idx 6)**, 단위 천원→억원(÷1e5).
- **라벨 매핑(IBK 고유)**: 기초=`기초 순장부금액` / 신계약=`당기에 최초로 인식한 계약` / 이자=`보험금융손익` / 상각=`제공된 서비스에 대해 인식한 보험계약마진` / **기말=`기말 순부채 잔액`(주의: 기초는 "순장부금액", 폐지는 "순부채 잔액" 비대칭)** / 가정조정(item4)=residual(=추정치변동+손실부담, 정확 일치 검증).

| 항목(억원) | 2023.4Q | 2024.4Q | 2025.4Q |
|---|--:|--:|--:|
| ①기초 | 3,073.6 | 4,558.4 | 4,501.1 |
| ②신계약 | 323.3 | 403.6 | 717.7 |
| ③이자 | 96.9 | 146.6 | 160.1 |
| ④가정·경험 | 1,326.1 | △256.3 | 265.1 |
| ⑤상각 | △261.5 | △351.1 | △440.3 |
| ⑥기말 | 4,558.4 | 4,501.1 | 5,203.8 |

- 3중검증: closure(①+②+③+④+⑤=⑥) 매년 정확 · continuity(기초=직전 기말) Δ=0 · 배당별 cross-check.
- 레코드형식: 원수사명=`IBK연금보험`(kics명), 티커=`X`(비상장·메트라이프 관례), 생손보=`생명보험`, 값_당분기=①~⑤ null·⑥=값(라이나/메트라이프 연간사 관례). **텍스트 splice로 append(CRLF+indent2 보존, +198/−0 순수추가)**.

### ⏳ 후속(focused, 미완) — 라우팅
1. **PL_breakdown (24항목×3개년) = audit-only 완전 gold 빌드.** IBK는 **FS-API가 3개년 전부 empty**(비상장 감사보고서사 = 라이나 KR0074·메트라이프 패턴) + generic tier2 핸들러가 IBK 구조 미처리. → 감사보고서 포괄손익계산서(tier1) raw 직접판독 + 보험서비스결과 분해(tier2: 원수/재보험×CSM상각·위험조정·예실차) hand-build → `_GOLD_CELL_OVERRIDE` 등록, item1=2−16·17=18+19·20=1+17 closure 검증. **이번 세션 최대 단일작업 → 별도 focused 세션.**
2. **sensitivity(민감도)** — `아이비케이연금보험_*_sensitivity.json` 추출 확인 후 sensitivity_heatmap 반영(별도).
3. **downstream(publishing/미실행)**: ⓐ master xlsx 재생성(formula-cache 위험 + owner 지시 = 공식 xlsx skill로, 내가 openpyxl 재저장 금지). ⓑ CSM 마스터→viz 전파(viz_build_csm_waterfall·csm_bubble·NB_CSM_multiple) 후에야 사이트 표시. **파괴적 빌더(build_csm_waterfall_master) 실행 금지** — 나는 master JSON append만.

**현재 상태**: CSM 마스터엔 IBK 존재(사이트 CSM 패널은 viz 전파 후 표시), PL 마스터엔 IBK 아직 없음(부분 온보딩, 의도된 상태).

status → open 유지 (PL·민감도·viz 전파 remaining).
