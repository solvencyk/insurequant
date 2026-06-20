---
from: owner
to: parser
created: 20260615T0435Z
status: open
route: backlog
company: MULTI
period: 2025.4Q (FY2025 사업보고서)
lane: ifrs17
iter: 1
---

## 미결 (sender 작성 — owner)

**CSM 민감도 표를 FY2024(24.4Q) → FY2025(25.4Q) 기준으로 전사 재추출 + heatmap 재빌드.** (raw fetch는 downloader 연계 `inbox/downloader/20260615T0435Z__…ifrs17_sensitivity_fy2025_fetch.md`.)

파이프라인: DART FY2025 사업보고서 → `data/dart/extracted/<회사>_<rcept>_sensitivity.json` → `scripts/viz_build_ifrs17_panels.py` → `data/dart/viz/sensitivity_heatmap.json`.

**파일럿 = 흥국생명보험(검증 필수)**: FY2025 추출이 owner가 25.4Q 경영공시 원문에서 본 값과 맞아야 한다 —
- 사망률↑ shock: **보험계약마진 +28억(증가)·당기손익 +6억(증가)** (현재 FY2024는 −35.94억/−29.27억 = 부호 반대 = 묵은 데이터).
- **장해질병(정액보상)·장해질병(실손보상) 각 행 존재** (FY2024 표는 사망보험/건강보험/연금저축으로 묶여 장해질병 분리가 없었음 → FY2025는 분리돼야 정상).
- 매칭되면 staleness만의 문제였음이 확정. 안 맞으면 부호/컬럼/단위 매핑 버그이니 원인 적시 후 멈춰서 회신(억측 금지).

파일럿 통과 → 전사 batch → heatmap 재빌드. 단위(억원, 1억=100백만)·부호 회귀 없는지 기존 대조. FY2025 미공시 회사는 FY2024 유지 + 명시.

**주의**: Windows 인라인 멀티라인 `python -c` 금지(행). python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. `build_csm_waterfall_master.py` 실행 금지(파괴적). sensitivity 파이프라인만.

## 답변 (parser 2026-06-15 — 파일럿 흥국생명: staleness 확정 + FY2025 핸들러 버그, batch 전 정지)

owner 지시대로 흥국생명 FY2025 raw(`KR0071_흥국생명보험_20260331004251`)로 파일럿 추출 → 패널 결과 대조.
(read-only: extracted/heatmap 미작성, 마스터 미빌드.) 0520Z downloader 건과 동일 파일럿.

### ✅ FY2025 데이터 정확 — staleness 확정
FY2025 흥국 "3) 보험위험의 민감도 분석" **합계 행**(사망률 3.27% 상승, 당기말):
CSM=`2,795`백만=**+27.95억**, 손익효과=`578`백만=**+5.78억** → **owner 기대값(+28/+6)과 정확 일치(부호 +)**.
현 heatmap FY2024 −35.94/−29.27 = 묵은 데이터 확정. → FY2025 갱신 필요.

### 🔴 그러나 현 추출 핸들러가 FY2025 레이아웃에서 오작동 → batch 정지
FY2025 표가 FY2024 대비 **컬럼 추가**됨:
- FY2024: 당기말/전기말 × (CSM, 손익효과, 자본효과) = **6 value col**
- FY2025: 당기말/전기말 × (**이행현금흐름**, CSM, 손익효과, 자본효과) = **8 value col**

F16 `_extract_heungkuk_product_rows`가 `offset = len(cells) − 6` + `vals[0]=CSM` 하드코딩이라 8-col에서 전부
오정렬 → **합계 행 대신 유배당보험(첫 상품) 행 읽음**(CSM 7,422백만=74억, 기대 28억 아님) + 일부 상품명을
risk로 emit(product-as-risk 버그 재현). rowspan으로 행별 셀수 6/8 혼재.

### ⚠️ 장해질병(정액/실손) 행 — 확인 요청 (억측 금지)
owner 기대 "장해질병(정액보상)/(실손보상) 각 행"이 **흥국 FY2025 민감도표에 없음** — 이 표는 **사망률/해지율 ×
유배당/무배당/변액(상품)** 구조라 장해질병 risk 행 자체가 부재. (downloader 0520Z: 리터럴 "장해질병" 0,
장해6·질병6·정액19 별도.) → owner 의도가 (a) 다른 표(계리적가정 민감도?) (b) 라벨변형 (c) 착오 중 무엇인지 확인 요청.

### 제안 (owner go 대기)
1. `_extract_heungkuk_product_rows`+가드를 **8-col FY2025 레이아웃**(이행현금흐름 추가)으로 확장 — 헤더에서
   CSM/손익효과 컬럼 동적 인덱싱, **합계 행 당기말 CSM/손익효과** emit → 흥국 사망률↑ +28/+6 재현 검증 후 batch.
2. 장해질병 의도 owner 확인.
3. **FY2024→FY2025 레이아웃 드리프트가 흥국만일 리 없음** → batch 시 사별 검증 필수(owner pilot-first 판단 정확).
   단위(억원)·부호 회귀 대조 포함. FY2025 미공시사 0(downloader 28/28).

status: open (owner 회신 대기 — 핸들러 fix go + 장해질병 의도 확인. 둘 다 받으면 핸들러 수정→흥국 재검증→전사 batch→heatmap 재빌드.)

## 답변 추가 (parser 2026-06-15 — owner go 반영: 핸들러 fix 완료 + batch가 광범위 product-row 드리프트 노출)

owner 결정(핸들러 수정+흥국 재검증+전사 batch / 장해질병 없으면 패스·있으면 up/down 별도) 반영.

### ✅ 흥국 핸들러 8-col fix — 완료·검증
`_extract_heungkuk_product_rows`를 헤더 동적 인덱싱(CSM/손익 컬럼)으로 재작성 → FY2025(이행현금흐름 추가 8-col)·
FY2024(6-col) 둘 다 처리. **흥국 FY2025 사망률↑ csm=+27.95 pl=+5.78 = owner 기대(+28/+6) 일치**, FY2024 흥국
무회귀(−35.94/−29.27), pytest 110. + `_has_shock_rows`에 **'%' 필수** 가드(롤포워드 "증가분(감소분)" 라벨이 shock로
오인되던 것 차단) + build_panel **best-status dedup**(FY2025-ok가 FY2024 대체, FY2025 빈값이면 FY2024 유지).

### 🔴 그러나 전사 batch가 광범위 FY2025 레이아웃 드리프트 노출 — heatmap 미커밋
FY2025 raw 30사 추출→rebuild: 21사 FY2025 갱신·AIG/카카오페이 신규·status 회귀 0이나, **다수 회사가 product-row /
원수·출재·순액 sub-row 레이아웃**(FY2024보다 granular)이고 패널 band/generic 경로가 **sub-row를 risk로 가비지 emit**:
- 농협생명: 사망률(정상) + "무배당보험 shock=22,644,512"(가비지) / 케이디비: 사망률(정상)+무배당/변액/출재/순액(가비지)
- 삼성화재/흥국화재: measurement 롤포워드 오선택(now '%' 가드로 거부→FY2024 유지)
- 동양/메트라이프/에이비엘/처브: FY2025 SA=0(src 추출 분류 실패→FY2024 유지)

owner "잘못 ship 금지" 대로 **가비지 heatmap 커밋 안 함, FY2024로 되돌림**. 코드(흥국 핸들러·'%'가드·dedup·batch 스크립트)만
커밋(FY2024 무회귀 0 검증). FY2025 extracted는 재생성 가능이라 제거.

### 다음 단계 (FY2025 refresh phase 2 — 다세션)
band/generic 경로를 **product/sub-row 일반 처리**로 확장(합계/순액만 emit, 무배당/유배당/변액/원수/출재 skip, 장해질병
up/down 별도) + 동양/메트라이프/에이비엘/처브 src sensitivity 분류(SA=0 원인). owner pilot-first 판단이 정확했음.

status: open (FY2025 refresh phase 1 = 흥국 핸들러+인프라 done; phase 2 = product-row 일반화 + SA=0 4사, 다세션)

## validation 핀 (2026-06-20) — phase 2에 라이나 단위정규화 명시 요망

`validate_master_tables.py` SENSITIVITY_UNIT_SANITY 게이트에서 **라이나생명 RED 1건** — max|Δ|=0.95억 vs 또래median 0.00036 (ratio>1000x, unit=억원/det=천원). audit-only **band-layout 단위 미정규화**(0712Z "라이나=CSM delta 100배 규모" 진단과 동일 뿌리). phase 2 "band/generic product/sub-row 일반화" 목록에 라이나가 **명시 누락** → 추적 보장 위해 phase 2 batch 시 라이나 band 단위정규화(÷1000 or 헤더 동적) 포함 요망. (sens는 push #0 data-contract 게이트엔 없어 비차단, IFRS17 master 게이트에서만 RED.)

진단 2026-06-20 (parser-ifrs17, open 유지): FY2025 sensitivity 27 ok+3 partial. 3 partial 근본원인=추출기가 오탐 잡음(미래에셋=요약손익계산서, 신한라이프=확정급여채무[퇴직급여] 민감도, 한화손해=비연결구조화기업). 진짜 IFRS17 보험위험 민감도는: 미래에셋=OCR/이미지(텍스트0), 신한라이프=prose 서술, 한화손해=시장위험형(환율/금리/주가→손익,자본)만. → 자동복구 불가, owner 손fix 또는 prose/OCR 별도파이프. 12사 sensitivity_overrides.json은 기적용.
