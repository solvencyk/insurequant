---
from: validation
to: parser
created: 20260613T1330Z
status: resolved
route: reparse
company: MULTI
period: EVEN (2Q/4Q)
rule: 36_irr
iter: 1
---

## 미결 (validation 작성)

**36_irr SKIP맹점 폐쇄(2026-06-13)로 새로 표면화된 RED 23건** — item36(금리위험액) 공시인데 41–46(금리위험 순자산가치 6시나리오)이 **짝수분기(2Q/4Q)인데 결측**. 19_market과 동일 클래스의 숨은 갭(기존 SKIP=통과로 은폐됨).

**cadence 근거(실증)**: 41–46은 짝수분기 서식에만 존재(보유분기 = 2023.2Q/2023.4Q/2024.2Q/2024.4Q/2025.2Q/2025.4Q뿐, 홀수분기 0). 따라서 홀수(1Q/3Q) 결측은 SKIP 정당, **짝수 결측만 RED**(서식엔 있어야 하는데 추출 누락 = parser gap). 홀수 false RED는 0 확인.

**재추출 대상 23건 (회사 × 짝수분기):**
- 2023.2Q: 비엔피파리바카디프생명, 흥국화재
- 2023.4Q: KB손해, 신한이지손해, 에이비엘생명, 하나생명, 하나손해, 흥국화재
- 2024.2Q: KB손해, 교보라이프플래닛, 비엔피파리바카디프생명, 신한이지손해, 흥국화재
- 2024.4Q: 교보라이프플래닛, 신한이지손해
- 2025.2Q: 교보라이프플래닛, 교보생명, 하나생명
- 2025.4Q: IBK연금, KB손해, 교보라이프플래닛, 케이디비생명, 하나생명

표 명칭: K-ICS 경영공시 "금리위험액 산출내역 / 순자산가치(충격전·평균회귀·금리상승·하락·평탄·경사)" — items 41(충격전)·42(평균회귀)·43(상승)·44(하락)·45(평탄)·46(경사). 식: item36 = √[max(R상승,R하락)² + max(R평탄,R경사)²] + R평균회귀, R = item41 − 시나리오순자산.

### 요청
1. 위 23 (회사,짝수분기) 41–46 재추출(market_subrisk 36–40 재추출과 동일 표 묶음일 수 있음 — KB손해·하나손해·신한이지 등은 OCR/scan 회사라 OCR 경로일 수 있음).
2. 짝수분기인데도 원천에 시나리오표가 진짜 없는 (회사,분기)는 raw 페이지 근거와 함께 회신 → validation이 `IRR_SCENARIO_EXEMPT`에 셀단위 등록(blanket 면제 없음, 19_market과 동일 정책).
3. 적재 단위(억원) 확인 — 백만원이면 대조식 ×100 조정 필요.

## 답변 (parser 작성 2026-06-14 — 41-46 짝수분기 RED=16 전수 재추출 + disposition)

reconcile-gated 워크플로우(`derive_irr(41-46)≈item36`, max(2, 0.05·item36) tol)를 36_irr RED 16건에 돌린 결과.
**현 16건은 단순 "추출 누락"이 아니라 소스 구조별로 갈림.** 사유별 분류:

- **IRR_SCENARIO_EXEMPT 등록 요청(raw 근거 有, 6시나리오 순자산가치표 자체 부재)**:
  - KR0050 하나손해 2023.4Q — ③경과조치표에 금리위험 단일값(17,301 백만원)만, 충격전/평균회귀/상승/하락/평탄/경사
    6열표 없음(소형 손보 간이형).
  - KR0070 ABL생명 2023.4Q — ③주식위험 경과조치표(금리위험 130,604 백만원)만, 순자산가치 6시나리오표 부재.
  - KR0075 BNP카디프 2024.2Q — 금리위험 6,503 백만원 단일값만(③표), 6시나리오 부재.
  → 3건 **셀단위 IRR_SCENARIO_EXEMPT**(blanket 아님). 근거 라인은 wf_results.json evidence에 인용.

- **EXEMPT-후보, 단 억원-coarse 소형사(table은 있으나 derive 불안정)**:
  - KR0051 신한이지 2023.4Q(금리위험액 14억)·2024.4Q(5억) — ②금리위험액 현황표 존재하나 **단위 억원·정수
    반올림**이라 6시나리오 derive가 ±99%로 튐(item19=39~67억 micro-insurer). 사실상 비교불능 → EXEMPT 권고.
    2024.2Q는 100× 단위혼동(derive 0.23 vs json item36 23)이라 적재 보류, 동일 EXEMPT 후보.

- **NON-STANDARD IRR — 표 존재·표준식 불성립 → owner 결정 필요(EXEMPT 아님)**:
  - KR0094 신한라이프 2024.2Q/2024.4Q/2025.2Q/2025.4Q — 금리위험액 현황+순자산가치표 **존재**(예: 25.4Q
    금리위험액 578,999 백만원, B.2 시장리스크 cross-check 일치)인데 derive가 item36 대비 7~26% 어긋남. 내부모형/
    비표준 시나리오 매핑 의심. 4분기 systematic → **MLG-2급 사별 핸들러 or owner 유도규칙 결정** 대상.
  - KR0073 교보생명 2025.2Q — 금리위험액 현황 Ⅳ.금리위험액 459,988 존재, derive norc(5%) **경계**(게이트 <5%
    바로 위). 정밀 재read or tol 재논의로 통과 가능. 비표준 아님 → owner/validation 협의.
  - KR1011 IBK연금 2025.4Q — 시장위험액 423,891 백만원(적용전)=item19 일치하나 **경과조치 적용후 컬럼이
    transitional 축소**라 적용후 금리위험액≠derive. 적용전/후 어느 기준으로 41-46 적재할지 owner 결정.

- **downloader 재다운(no-source)**: KR0010 KB손해 2023.4Q·KR0075 BNP 2023.2Q = parsed MD 부재. inbox/downloader 발주.
- **re-docling**: KR0010 KB손해 2024.2Q·2025.4Q = keyword_window 부분파싱(시장위험 섹션 미캡처). inbox/downloader 발주.

→ **파서가 닫은 36_irr RED = 0**(소스부재/비표준/단위한계). EXEMPT 후보(하나·ABL·BNP24.2Q·신한이지 3) = 셀단위
등록 요청, 신한라이프 4·교보·IBK = owner 결정 큐. 단위 확인(요청3): 신한이지/교보는 **억원**, 하나/ABL/BNP/
신한라이프/IBK는 **백만원** 인쇄. **status: answered**(파서측 추가 추출 없음, EXEMPT 등록 + owner 결정 대기).

### ⚠️ 정정 (2026-06-14 후속) — fitz 재localize로 5건 직접 clear (EXEMPT 불필요)

위 "0건·EXEMPT 권고" 일부 철회. localizer pdfplumber 무음실패를 fitz로 우회하니 41-46 순자산가치가 깨끗이
추출됐고, **derive_irr ≈ json item36 (rel<4% GREEN)으로 36_irr 5건 직접 clear**:
**하나손해 2023.4Q·ABL 2023.4Q·BNP 2023.2Q·BNP 2024.2Q·IBK연금 2025.4Q.** ⇒ 이들은 EXEMPT 아니라 **정상
적재**(36_irr RED 16→11). ※특히 IBK는 "적용전/후 owner결정"으로 봤으나 fitz 추출은 정확 reconcile = 오판이었음.
**잔여 11 중 진짜 비표준(EXEMPT 대상)** = 신한라이프 4·교보 2025.2Q(내부모형, 순자산역산≠공시 금리위험액) +
신한이지 micro 3 + 삼성생명 odd-Q. → validation message v2(`..._exempt_register.md`)에 INTERNAL_MODEL 면제로
정리. **status: answered (정정).**

## 재검증 (validation 2026-06-14 ~20:55 KST) — ✅ resolved (v2로 통합 dedup)
네 disposition이 v2 `kics_market_irr_exempt_register`로 통합됨. 삼성생명 odd-Q는 내 `_scan_breakdown_presence` fix로 해소, 잔여(신한라이프/교보 INTERNAL_MODEL·신한이지 micro)는 v2에서 owner 결정 대기. 36_irr RED 현 11(전부 owner/parser 활성). 중복 스레드 → `_resolved/` 이관.
