---
from: owner
to: validation
created: 20260616T1155Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — "Data Contract" 사전-push 게이트 신설 (최우선 인프라)

owner 결정: 두 달간 라이브 QA로 매번 잡던 "기초정합성" 오류를 **권고 → 강제 게이트**로 코드화한다. 진단은 이미 메모리에 다 있음(`feedback_coverage_census_mandatory`·`feedback_validation_blind_spots`) — **새로 만들 건 그 진단의 코드화 + 한 가지 신규 축(소스 provenance/as-of)**. 이게 "맞는 산수·틀린 소스"를 통과시켜온 RED=0 false-green을 끝낸다.

### 0. 게이트 성격 (anti-gaming 원칙 — 최우선)
- **단일 러너** `scripts/validate_data_contract.py` (이름 협의 가능). **publishing이 push 추천 직전 1순위로 실행**하는 차단 게이트. RED=0 또는 `TODO.md` 문서화 예외만 통과.
- **결측 메타/census 데이터 = RED, 절대 SKIP 아님.** provenance 없음·기대 cell 없음·소스 미상 = 무조건 RED. (SKIP=통과로 세는 기존 사각을 구조적으로 차단.)
- **스냅샷 provisional**: 실행 전후 마스터 mtime 기록, 동시 백필 중이면 "잠정" 명시(`validation_blind_spots` 5a).
- **출력 = 사람이 읽는 리포트**(기존 validation 리포트 형식) — owner가 push 전 눈으로 확인.

### 1. ① 완전성 census (기존 진단 코드화·통합)
`feedback_coverage_census_mandatory` 그대로 게이트화:
- **기대 그리드**(회사 × 분기 × 항목블록)를 마스터별로 명시: `kics_disclosure` / `CSM_waterfall` / `PL_breakdown` / `kics_rate_sensitivity` / `tier{1,2}_utilization` / `forward_capital`.
- 적재 데이터와 diff → **빠진 (회사,분기)·항목블록 = RED**(documented exception만 면제). 직전 동형분기 대비 적재사 수 급감 = 즉시 RED(2026.1Q 1개사 사고 방지).
- **부모-자식 완전성**: 부모 공시인데 자식 전부 결측 = parser stitch 실패 = RED. SKIP 별도 카운트, 의심 SKIP은 RED 승격.
- 기존 `validate_master_tables.py` MASTER_COVERAGE / parent-zero 룰을 이 게이트로 흡수·통합.

### 2. ② 소스 Provenance + As-of (🔴 신규 — 도넛 버그 잡는 단 하나)
**기존 validator에 전무한 축.** tier 도넛 오류(downloader가 "26년 3월 기준 *유효* 자본성증권 목록"을 안 거르고 stale 스냅샷 사용)·신뢰도패널 stale baseline(2025.4Q를 2026.1Q로 표시)이 전부 여기서 잡혀야 함.
- **provenance 계약 정의(validation 몫):** 게이트가 각 published 수치에 대해 resolve할 수 있어야 할 메타 = `(source_id, as_of_date, source_file)`. 어디에 둘지(셀별 필드 vs 사이드 manifest)는 validation 설계 — **추천: 마스터별 `*_provenance.json` 사이드카**(셀 스키마 비파괴).
- **검사 3종:**
  - **(a) as-of 일치**: 수치의 `as_of_date` = 공시분기. 2025.4Q baseline이 2026.1Q 패널로 렌더되면 RED. (forward sim `BASELINE_QUARTER` 하드코딩 같은 케이스.)
  - **(b) authoritative source**: 각 metric이 *지정된 권위 소스*에서 왔는지. 예: 자본성증권 유효목록 = FSC bonds API를 **유효-as-of 필터(call/만기) 적용 후** → stale 스냅샷·미필터 목록이면 RED.
  - **(c) effective-list 적용 증거**: as-of 시점 유효분 필터링이 실제 수행됐다는 플래그/근거. 없으면 RED.
- **결측 provenance = RED**(원칙 0).

### 3. ③ 동일개념 cross-source 일치 (+ 다른개념 guard)
- 두 소스가 **같은 개념**을 커버하면(DART↔IR CSM step별 등) tolerance 내 일치 검증 — 기존 validation §1.2 룰 흡수.
- **다른 개념은 비교 금지·신뢰도 강등 금지.** 예: tier2 Face(채권등록 outstanding) vs BS(K-ICS 경과조치 기발행)는 **구조적으로 다른 개념**(parser-kics 2026-06-16 진단) → cross-source 불일치로 "신뢰도 낮음" 깎으면 안 됨. **개념 레지스트리**로 "비교 가능/참고만" 분류.

### 4. 단계화 (boil-the-ocean 금지)
- **Phase 1 (즉시, 기존 필드로 buildable):** ① census 통합 + ②(a) as-of 일치 + ②(c) effective-list 플래그 + ③ 다른개념 guard. 새 메타 emission 없이 기존 period/소스경로/플래그로 검사 → **실제 버그(도넛·stale baseline·missing cell) 지금 잡힘.**
- **Phase 2:** 전 마스터 provenance 사이드카 + parser/downloader가 `(source_id,as_of,source_file)` emit. **validation이 provenance 계약(스키마)을 먼저 정의** → 그 emission 서브태스크를 parser/downloader inbox로 **바운스**(이 게이트가 그들에게 요구하는 메타 명시).

### 5. 회귀 테스트(게이트가 반드시 잡아야 할 실제 버그 = 인수기준)
1. tier 자본성증권 **유효-as-of 미필터** → RED (도넛 버그).
2. **stale baseline**(2025.4Q를 2026.1Q로) → RED.
3. **missing cell**(한 분기 1개사만 적재 류) → RED.
4. **불가능-0**(CSM상각=0, PL 생명장기 leg=0) → RED (`validation_blind_spots` 불가능-0 목록).
5. **wrong-concept compare**(Face vs BS tier2) → **신뢰도 안 깎음**(③ guard 동작).

### 6. 와이어링
- publishing 게이트 순서에 **#0 data-contract**로 삽입(기존 validation/assembly 게이트 앞). RED>0이면 push 추천 BLOCKED.
- `consolidate_inbox.py` `VALIDATORS`에 핸들러 추가(RED→route별 메시지).

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. UTF-8 no BOM. `build_csm_waterfall_master.py` 실행 금지(raw purge 붕괴).
- 기존 흩어진 validator(`validate_master_tables`·`validate_csm_*`·`validate_kics_*`)는 **삭제 말고 이 게이트가 호출·통합**(중복 로직만 정리).
- 진행 단위로 회신: Phase 1 러너 + 회귀 5건 통과 여부 먼저.

## 답변 (validation 2026-06-16 — Phase 1 러너 + 회귀 5건 DONE·검증, owner 결정 3건)

**Phase 1 게이트 빌드 완료·메인세션 검증.** `scripts/validate_data_contract.py`(+ `_data_contract_selftest.py`).
기존 validator를 **import·호출**(삭제·수정 없음, 중복로직 정리만): `_coverage_census`·`_parent_zero_child_nonzero`·
`_scan_breakdown_presence`·`coverage_holes`·`kics_run_validation`.

- **회귀 5건(인수기준) 전부 PASS** (`--selftest` → 7/7, 변형·음성대조 포함): ①도넛 effective 미필터 RED ②stale baseline RED
  ③missing cell(1-filer) RED ④불가능-0(상각·생명장기leg) RED ⑤wrong-concept 신뢰도 안 깎음(guard). build_csm_waterfall 미트리거 확인.
- **라이브 실행: exit 2, RED=52, provisional=False.**
  - CHECK1 census 30 = 기존 K-ICS 게이트 흡수(12 36_irr+7 19_market+1×5 등식) + MISSING_FILER 6(카카오×4·동양 2023.2Q·하나생명 2024.2Q). 표준 K-ICS 게이트와 정확 일치(중복계상 0 — blanket "children all missing"이 odd-Q 간이공시에 281 RED 오발 → cadence 엔진 위임으로 19 정정).
  - **CHECK2 as_of 22 = 🔴 진짜 버그 적발(신규 provenance 축)**: `sensitivity_heatmap.json`이 아직 **period=FY2024/as_of=2024-12-31(2024.4Q)** 스탬프인데 기준은 2025.4Q = **V12 staleness**(기존 validator가 못 잡던 것). forward_capital(2026.1Q)·tier1/2(2026.1Q)·bond effective-list는 clean.
  - CHECK3 0(comparable는 IR parsed JSON 미배포라 SKIP, guard 정상).

**🟠 owner 결정 3건:**
1. **22 STALE_AS_OF(sensitivity_heatmap)** = V12 진행건(parser가 25.4Q 경영공시 refill 대기). 게이트가 정당하게 차단 중.
   → refill 안착 전까지 (a) TODO.md `DATA_CONTRACT_EXCEPTION` 등록 vs (b) push 보류. **§4상 면제등록=owner 권한**이라 상신.
2. **와이어링(§6)** = spec "Phase 1 먼저"라 보류함. publishing 게이트 #0 삽입 + `consolidate_inbox.py VALIDATORS` 핸들러 — go 주시면 진행(publishing 게이트 순서는 publishing 연계).
3. **documented-exception 포맷** = `DATA_CONTRACT_EXCEPTION: <master> <code> <quarter>` 라인 제안. 기존 per-rule 스타일 선호 시 1줄 변경.

**Phase 2(provenance 사이드카)** 계약 정의 완료(`--print-provenance-contract`): 마스터별 `<master>_provenance.json`,
셀당 `{company_code, quarter, item_block, source_id(DART|FSC_BONDS|KIDI|DISCLOSURE_MD|IR_FACTSHEET), as_of_date, source_file,
effective_filtered}`. **라우팅 분담**: downloader=source_file·as_of_date·effective_filtered / parser=source_id·item_block.
owner go 시 parser/downloader inbox로 바운스(Phase 2 = emission 서브태스크).

## 추가 (owner 12:44 지시 반영 — 결정 끝, 전부 실행)

owner 정책 확정: **"RED 1건이라도 있으면 push 안 한다."** → 위 "결정 3건" 폐기, 전부 실행:
1. **22 STALE_AS_OF = exception 안 함, fix.** fixable RED이므로 우회/문서화 아니라 고쳐서 0으로. = V12 sensitivity_heatmap을 25.4Q로 refill(parser 진행건). 그때까지 push 차단이 정상.
2. **와이어링 = publishing 발주함**(`inbox/publishing/20260616T1254Z__…data_contract_gate0_wiring`): push 추천 직전 #0로 `validate_data_contract.py` 실행, exit 2면 BLOCK + `claude-agent-publishing.md` 게이트표 명문화.
3. **Phase 2 emission = 바운스함**: downloader(`…provenance_sidecar_emission`, source_file·as_of·effective_filtered) + parser(`…provenance_sidecar_emission`, source_id·item_block). 마스터별 사이드카, 셀 스키마 비파괴.

## 최종 (validation 2026-06-17 — 게이트 검증·면제제거·reader 완료 = validation 측 종결)

- Phase 1 게이트 빌드 + **면제 메커니즘 제거**(zero-RED 정책) + **Phase 2 사이드카 reader**(있으면 strict/없으면 Phase-1 fallback) 전부 완료. `--selftest` 7/7, 라이브 exit2 RED=52(무회귀).
- 와이어링(publishing #0)·Phase 2 emission(parser·downloader)은 각 stage inbox로 발주됨(다운로더는 일부 사이드카 이미 emit).
- 22 STALE_AS_OF·census RED은 면제 아니라 fix 경로(parser refill 등) — RED=0 될 때까지 push 차단이 정상.

status: resolved (validation 측 게이트 구축·정책·reader 종결. 다운스트림 emission/wiring/STALE fix는 타 stage inbox 추적).
