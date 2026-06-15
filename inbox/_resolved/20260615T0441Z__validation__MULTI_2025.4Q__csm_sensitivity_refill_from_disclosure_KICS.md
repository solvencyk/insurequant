---
from: validation
to: parser
created: 20260615T0441Z
status: resolved
route: reparse
company: MULTI
period: 2025.4Q
rule: SENSITIVITY_REFILL
lane: kics
iter: 1
---

## ⏸️ HELD — fallback (validation 2026-06-15)
owner가 0435Z에 **DART FY2025 사업보고서 → IFRS17 lane**으로 직접 발주(`20260615T0435Z__owner__MULTI__ifrs17_sensitivity_fy2025_reextract`, 흥국 파일럿 게이트). 본 disclosure/KICS 발주는 그와 충돌하므로 **보류(fallback)**. owner의 DART 파일럿이 FY2025에 장해질병 분리·값일치를 못 보이면(=DART 실익 없음) 이 disclosure/KICS 경로로 전환. 그때 재발행. 아래 구조 검증은 그대로 유효.

## 미결 (validation — owner가 소스 판단 위임: CSM 민감도 전수 fill = 경영공시, 담당 = KICS)

**결정: 25.4Q CSM 민감도 전수 fill 소스 = 정기경영공시(`data/disclosure/FY2025_Q4`), 담당 = KICS 파서**(이 PDF 파싱이 KICS 도메인이고, 이미 K-ICS·금리민감도를 같은 PDF에서 추출 중). owner가 DART vs disclosure 선택을 validation에 위임 → raw 대조로 disclosure 선택.

### 소스 결정 근거 (실측)
| | DART 사업보고서 | 경영공시(disclosure) |
|---|---|---|
| 25.4Q 데이터 | **미보유** — 현 28개 전부 FY2024(2024.12.31, rcept 2025). FY2025(rcept 2026) **미다운로드** | **보유** — FY2025_Q4 **39 PDF** |
| 커버리지 | 28사(비상장 누락) | **39사 전수** |
| 파싱 | 기존 IFRS17 파이프라인 有(단 FY2025 fetch 필요 + F16 product-as-rows) | 새 추출(구조는 아래 명확) |

→ **전수(39) + 25.4Q 이미 보유 + KICS가 이 PDF 이미 파싱** = disclosure 압승. DART는 FY2025 미다운로드 + 비상장 누락이라 25.4Q 전수 불가. granular(장해질병)는 DART도 전수 불가·미다운로드라 실익 없음(경영공시도 회사별 risk 셋 상이 → 공시된 risk 전수 캡처, 하드코딩 금지).

### 검증된 표 구조 (흥국생명 KR0071 raw 대조 = 정본 템플릿)
- 위치: PDF **602페이지** 중 IFRS17 주석 `3) 보험위험의 민감도 분석`. **page 281(연결)·487(별도)** 둘 다 존재(흥국은 동일=standalone). raw: `data/disclosure/FY2025_Q4/raw/KR0071_흥국생명보험.pdf`.
- ⚠️ **parsed MD엔 없음** — `data/disclosure/FY2025_Q4/parsed/KR0071*.md`는 K-ICS 솔벤시(6-8 위험민감도=지급여력비율)만. IFRS17 주석 민감도는 MD 범위 밖 → **raw PDF 주석 직접 추출** 필요(전사 동일 가정).
- 표 구조(백만원): 행 = risk×shock×상품구분(유배당/무배당/변액/**합계**), 컬럼 = **[이행현금흐름, CSM, 손익효과, 자본효과] × [당기말, 전기말] = 8 value cols**.
- ⚠️⚠️ **컬럼 오프셋 함정**: **CSM은 첫 값컬럼이 아니라 2번째**(이행현금흐름 다음). 사업보고서(6컬럼, 이행현금흐름 없음)용 추출기를 그대로 쓰면 이행현금흐름을 CSM으로 오독. **헤더 라벨로 매핑 필수**. `csm_delta` ← 당기말 CSM, `pl_impact` ← 당기말 손익효과(≠자본효과).
- **합계 행**을 risk-level로(상품분해 보존은 designer 협의). **당기말만**(전기말=FY2024=현 stale heatmap값이므로 무시).
- **검증 앵커(흥국 당기말 합계, 백만원 → ÷100=억원)** — owner가 page 487에서 본 값과 일치:
  - 사망률 3.27%↑: CSM **+2,795**(+27.95억) / 손익 **+578**(+5.78억)
  - 해지율 9.16%↑: CSM **(173,186)**(−1731.86억) / 손익 **(3,283)**(−32.83억)
  - 사업비&인플레 2.62%↑/0.26%↑: CSM **(50,389)**(−503.89억) / 손익 **(4,062)**(−40.62억)
  - 부호 전부 CSM↔손익 동행 = 정상(현 heatmap의 역행은 FY2024 stale값 + 그해 실제 부호. FY2025엔 반전).

### 출력 계약 + IFRS17 핸드오프
- KICS가 disclosure→CSM 민감도 추출물 생성(heatmap 스키마: `{company, rcept_no, unit:"억원", scenarios:[{risk, shock, csm_delta, pl_impact}]}`).
- **현 `data/dart/viz/sensitivity_heatmap.json` 소스(FY2024 DART)를 이 25.4Q disclosure 추출물로 교체.** 빌더 `viz_build_ifrs17_panels.py`(IFRS17 소관)가 새 소스 consume하도록 전환 = **IFRS17 lane 핸드오프 1건**(KICS 추출 완료 후 inbox/parser lane:ifrs17 통지).
- 별도/연결: 흥국 동일. 회사별 상이 가능 → 연결 우선(없으면 별도) 권고, owner 확정.
- coverage: 민감도 주석 없는 회사 `unavailable` 정직표기(추측·가비지 금지, [[coverage-census-mandatory]]).

### validation 가드 (fill 후 자동 재검증)
- **SENSITIVITY_DIRECTION_SANITY**(`validate_master_tables.py` 5b): sign(csm)≠sign(손익) YELLOW. 흥국 25.4Q는 전부 동행=clean 기대.
- **SENSITIVITY_UNIT_SANITY**(5): 또래-median 규모비 RED>1000x/YEL>100x.

회신: 추출 회사수 + risk행수 + unavailable 명단 + IFRS17 빌더 전환 여부 1줄 → validation 전수 재검증.

⚠️ 본 메시지가 `20260615T0415Z__...refill_disclosure_basis`(lane:ifrs17, 소스 미결정 generic)를 **대체**한다(그건 supersede).

## 답변 (parser 작성 — 처리 후)
