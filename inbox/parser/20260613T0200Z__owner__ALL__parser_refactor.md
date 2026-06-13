---
from: owner
to: parser
created: 20260613T0200Z
status: open
route: backlog
company: ALL
period: ALL
rule: REFACTOR
iter: 1
---

## 미결 (sender 작성)

**owner 기술부채 진단 (2026-06-13). 정보성 백로그 — auto_loop 아님.** 코드 실측(4,276 LOC / 13 모듈)
기준 parser가 유지보수 절벽으로 향하는 신호 확인. **지금이 싸게 고칠 창**(회사 10~15개 더 쌓이기 전).
배경: 이 스테이지의 "지능"은 누적 회사별 휴리스틱이라, 변형 추가 = 3~5파일 동시 수술 → 회사 #38쯤 병목.
처방 원칙: **새 변형이 Python 코드가 아니라 config로 착지하게** ("환경을 옳은 결과가 쉬운 결과가 되게").

### 신호 (실측)
- 회사·분기 하드코딩 분기 ~40곳 전역 산포 (단일 모듈 아님).
- IFRS17 추출기 6개가 scorer 키워드+로직 복붙: `_CAPTION_PRIMARY/_SECONDARY`·`_ROW_STUBS_STRONG/WEAK`·
  `_HEADER_*`·`_score_table()`가 `src/ifrs17/{csm,measurement,insurance_pl,reinsurance,bs_snapshot,
  sensitivity}_extractor.py`에 각 40~50줄씩 중복.
- IFRS17 추출기 **유닛테스트 0** (K-ICS는 `tests/unit/test_kics_disclosure_parser.py` 골든 4개 有).
- config 외부화는 `data/dart/normalization/row_aliases.yaml`(36줄)뿐 — 회사별 매핑은 프롬프트에 TBD인 채
  코드/주석에 묻힘. `kics_disclosure_parser.py` 151 if/elif (파일 26%).

### 🟠 작업 (top-3, 순서대로 — 통째 리팩터 금지, 슬라이스로)

**REFACTOR-1 (착수 슬라이스 — 먼저 이것만):**
- [ ] `src/ifrs17/csm_extractor.py`의 `_CAPTION_*`/`_ROW_STUBS_*`/`_HEADER_*`를 `data/ifrs17/
      table_scoring_keywords.yaml`로 추출 + 공유 `src/ifrs17/scoring.py`(`ScoringConfig` 로더) 신설.
- [ ] `tests/unit/test_csm_extractor.py` 골든 1개(고신뢰 공시 fixture — 삼성화재/메리츠 2025.4Q 등 이미
      gold 검증된 c-q 재사용). K-ICS 테스트 패턴 이식.
- [ ] **무회귀 확인**: 추출기 재실행 → 게이트(`_verify_csm_golds.py` + `validate_kics_disclosure.py`) 동일 결과.
- 효과 확인되면 ↓ 나머지 5개 추출기에 같은 틀 적용.

**REFACTOR-2:**
- [ ] 나머지 IFRS17 추출기 5개를 `scoring.py` + YAML로 이관(복붙 제거). 추출기당 골든테스트 1개씩.

**REFACTOR-3:**
- [ ] `src/solvency/parser/company_handlers.py` 레지스트리(KR코드→핸들러) 도입. 신규 회사별/분기별 변형은
      **코드 분기 금지 — 핸들러/config로만 착지**(동결 룰). 기존 산재 분기(SECTION_START_PATTERNS 9종,
      `_strip_label_punct` OCR 치환, Samsung/Hanwha/Shinhan 변형)를 점진 흡수.

### 룰
- 골든게이트·validate 무회귀가 모든 슬라이스의 exit 조건. blast-radius diff 필수(다른 c-q 0).
- 도메인상 불가피한 다양성은 인정 — 목표는 "다양성 제거"가 아니라 "다양성을 config로 외부화".
- 신규 prompt §(label variation matrix / per-company YAML path TBD)를 이 작업 결과로 채울 것.

## 답변 (parser 작성 2026-06-13 — REFACTOR-1 완료 + REFACTOR-2 착수)

owner 지시로 착수. 슬라이스 + 무회귀 게이트로 진행:

### REFACTOR-1 완료 (csm) + 골든테스트 (move #2·#3)
- NEW `data/ifrs17/table_scoring_keywords.yaml` + NEW `src/ifrs17/scoring.py` (`ScoringConfig` 로더,
  `load_scoring(name)`; 미선언 키→빈 튜플, 추출기별 비표준 키워드셋은 `.extra`로).
- `csm_extractor.py`: caption_primary/verbs/negative_topic/total을 YAML에서 로드. 구조 regex
  (year-bucket/sub-caption)는 코드 유지(라벨변형 아님).
- NEW `tests/unit/test_csm_extractor.py`: config 바이트동일 + score_table 분류(form A/A_rows, 비-CSM cap).
  무회귀 = 상수 바이트동일 증명(csm 골드게이트는 현재 gold 시트 0개라 no-op → byte-identity가 최선의 보증).

### REFACTOR-2 — 복붙 3인방(measurement/insurance_pl/reinsurance) 완료 = 핵심 중복 제거
- 이 셋이 caption/header/row_stub + block markers를 거의 동일 복붙하던 게 "변형 추가=3~5파일 동시수술"의
  근원. 셋 다 YAML 블록 + `.extra`로 **단일 소스화**. 역사적 OCR-typo(위허조정/위허해제/재보험자불이행위허/
  보험송취현금흐름/잔여보작)까지 바이트동일 보존. NEW 테스트 2개.
- **검증: `pytest tests/unit/` 94 passed**, 6개 추출기 import OK, csm·measurement·insurance_pl·
  reinsurance 상수 바이트동일.

### 잔여 (다음 슬라이스)
- **bs_snapshot/sensitivity 2개**: 상수 스키마가 measurement-family와 달라(복붙 아닌 bespoke) `.extra`
  위주 외부화 — 동일 레시피, 중복제거 효과는 작음(config 외부화 목적). 4/6 → 6/6 마무리.
- **REFACTOR-3 (move #1)**: `company_handlers.py` 레지스트리(KR코드→핸들러). K-ICS 산재분기
  (SECTION_START_PATTERNS 9종·`_strip_label_punct` OCR 치환·삼성/한화/신한 변형) 점진 흡수.
  이번 세션 시장위험도 회사분기 없이 일반규칙+config로 해결 = 레지스트리 원칙 부합.

진행: REFACTOR-1 + REFACTOR-2 복붙3인방 = **4/6 완료**. status: open 유지(bs_snapshot/sensitivity + REFACTOR-3).

## 미결 추가 (owner 2026-06-13 — REFACTOR-1/2 산출물 리뷰)

검수함. 메커니즘(`scoring.py` 로더 + `ScoringConfig` + `.extra`)·골든테스트(`score_table` 동작 분류 +
바이트동일 가드) = **실질 개선 인정**. 단 핵심 목표("변형 추가 = 1곳만 수술")는 아직 미달 — 복붙이
Python→YAML로 **이동만** 했고 공유 리스트가 그대로 3중복임. 다음 보강:

- [ ] **DEDUP-1 (핵심, P1)**: `table_scoring_keywords.yaml`의 공유 리스트가 measurement/insurance_pl/
  reinsurance에 바이트동일로 3중복 — `header`(line 24·34·44), `short_term_markers`·`direct_block_markers`·
  `ri_block_markers`(27-29·37-39·47-49), `row_stubs_weak` 공통부. **YAML anchor(`&name`/`*name`) 또는
  `_shared:` 블록 + merge key(`<<: *name`)로 단일화** → 그래야 "공통 변형 1곳만 수술" 성립. 바이트동일
  테스트는 anchor 전개 후에도 통과해야 함(전개 결과가 기존 상수와 동일).
- [ ] **DEDUP-2 (latent dup, P2)**: `short_term_markers` 마지막 2원소 동일("보험료배분접근법을 적용하는"
  ×2, 3블록 전부) — 원본 복붙 오타가 바이트동일로 보존된 것으로 보임. 의도 확인 후 1개로 정리(테스트 갱신).
- [ ] **GOLDEN-E2E (P2)**: 현 골든은 합성표 `score_table` 단위테스트 — 좋으나 "실제 다(多)표 MD에서 옳은
  표를 골랐나"는 미검증. 고신뢰 공시 1사 MD→기대값 **end-to-end fixture 1개**(csm부터). 블로그 "fast
  feedback" 갭 해소 — 추출기 버그가 1~2분기 뒤 validation이 아니라 PR에서 잡히게.

순서: DEDUP-1/2는 bs_snapshot/sensitivity(6/6) 이관과 **같은 PR**(어차피 같은 YAML). GOLDEN-E2E는
REFACTOR-3와 병행 가능. 무회귀 게이트(골든 + validate) 동일 적용. 시장위험 census 보고(b0z4g90k0)는
validation으로 핸드오프 확인 — enumerator-fix 이전 코드 caveat 잘 달림(면제 등록 전 재-census 동의).

## 답변 추가 (parser 2026-06-13 — owner 리뷰 반영: REFACTOR-3 slice1 + DEDUP-1/2 완료)

owner 리뷰 옳음. "복붙이 Python→YAML로 이동만 했고 공유 리스트 3중복"은 정확한 지적 — 처리함.

### DEDUP-1 (P1 핵심) — 완료. 공유 리스트 단일화로 "공통 변형 1곳만 수술" 성립
- `table_scoring_keywords.yaml`에 `_shared:` 블록 + YAML anchor(`&`/`*`) 도입. 공유 리스트가 리스트라
  merge key(`<<`, 매핑 전용)는 부적합 → plain anchor 사용.
- 단일화 대상: `&header`(3블록), `&short_term_markers`(3), `&direct_block_markers`(3), `&ri_block_markers`(3),
  `&meas_ri_row_stubs_weak`(measurement+reinsurance 2블록 — insurance_pl의 row_stubs_weak는 상이하므로 inline 유지).
- **검증**: 파일에 `미래 현금흐름`(header)·`순보험계약부채`(direct) 리터럴이 **각 1회만** 존재(=단일 정의),
  `*header` alias 3회. safe_load가 parse 시점에 전개 → 추출기는 여전히 full 리스트(byte-identical). 3블록
  header/direct/ri 동일·row_stubs_weak measurement==reinsurance 확인.
- reinsurance.caption_primary가 우연히 ri_block_markers와 동일 4원소지만 **의미 다른 필드**라 alias 안 묶음(향후 분기 대비).

### DEDUP-2 (P2) — 완료. 의도 확인 후 collapse
- `short_term_markers` 마지막 원소 중복("보험료배분접근법을 적용하는" ×2)은 **원본 HEAD 추출기
  (measurement_extractor.py:55-56)에 실재**한 복붙 오타 — byte-identity 보존이 정확히 작동한 것. `has_short_term_markers`는
  membership(any) 체크라 중복은 순수 no-op. owner 승인대로 1개로 정리(4→3), test_measurement:33 갱신.

### REFACTOR-3 slice1 (move #1) — 완료. K-ICS 파싱 변형 레지스트리
- **NEW `src/solvency/parser/company_handlers.py`**: `SECTION_START_SPECS`(9)·`SECTION_END_SPECS`(2)·
  `LABEL_FIXES`+`PUNCT_STRIP_CHARS`·`AUDIT_LABEL_ALIASES`를 append-only attributed 레지스트리로. 각 entry
  ASCII attribution(삼성 2023.1Q bullet·신한 보헨위→보험위 등) = 동결-룰 착지점. parser는 빌드/위임으로 교체(−70줄), 바이트동일.
- **설계 surface**: 명명 변형(section 패턴·OCR 라벨·alias)은 KR코드 키가 아님(MD가 코드 미탑재 + 같은 회사도
  분기별 레이아웃 변동) → **ordered 인식기 레지스트리**가 정답. 삼성/한화/신한 "변형"은 이미 `if code==`가
  아니라 일반 패턴이었고 이 슬라이스가 그 데이터를 config로 빼냄. KR코드→dict dispatch는 진짜 코드-귀속 노브
  (column-picker quirk 등)용으로 slice2(fill에 코드 스레딩)에 유보 — dead scaffolding 회피.
- **무회귀**: 기존 골든 25개(실제 MD end-to-end) green + NEW test_company_handlers.py 6개(바이트동일 락).

### GOLDEN-E2E (P2, csm) — 완료
- owner 지적 정확: 기존 골든은 합성 단일표 score_table 테스트라 "多표에서 옳은 표 골랐나" 미검증.
- NEW `tests/unit/fixtures/csm_e2e_meritz_2025q4.xml`(실제 메리츠 KR0001 2025.4Q 값, decoy 2개:
  재무상태표 score=0·위험조정 변동 score=−3 + 진짜 CSM 향후상각표 score=5). `extract_csm_tables()`
  end-to-end 테스트 추가 — CSM표 단독 선별·decoy 배제·발행보험계약 합계 11,103,697 검증. "csm부터" 지시 이행.

### 검증 종합: 전체 `pytest tests/unit/` **101 passed**(94 → +6 company_handlers +1 csm E2E).

### 잔여 (우선순위)
- **bs_snapshot/sensitivity → 6/6**: bespoke(복붙 아님) `.extra` 외부화. 같은 YAML PR.
- **REFACTOR-3 slice2**: column-picker/`_canonicalize_table_label` 변형 → 레지스트리; 진짜 KR-keyed 노브 나오면 dict dispatch.
- **GOLDEN-E2E 확장**: measurement/insurance_pl/reinsurance도 동일 다표 fixture(csm 패턴 이식).

status: open(bs/sens 6/6 + REFACTOR-3 slice2 + E2E 확장 잔여).

## 답변 추가 (parser 2026-06-14 — ifrs17 lane: bs/sens 6/6 완료 + GOLDEN-E2E 3종 확장)

ifrs17 레인 세션에서 잔여 슬라이스 마저 처리. 무회귀 게이트 + HEAD 독립 byte-identity로 검증.

### bs_snapshot/sensitivity → 6/6 (REFACTOR-2 완결)
- 두 추출기의 하드코딩 키워드 15개 리스트를 `table_scoring_keywords.yaml`로 외부화. bespoke라
  전부 `.extra`(표준필드 미사용). 모듈 상수명 동일 유지 → 다운스트림 무변경. intra-block DEDUP:
  bs의 `_HEADER_BS_SLICES`==`_ROW_SLICES`(장기/일반/자동차/생명) → `&bs_slices` 앵커 단일화.
- 골든테스트 신규 2개(`test_bs_snapshot_extractor.py`·`test_sensitivity_extractor.py`): 바이트동일 lock
  + `.extra` 키 존재 + `score_table` 스모크. OCR 오타(보험위허/위허률/잔여보작/비금융위허) byte-identical 보존.
- 6개 추출기 diff = import 1줄 + 상수→load 치환 + 주석뿐(로직 0변경 확인). −280/+74.

### GOLDEN-E2E 확장 (measurement/insurance_pl/reinsurance)
- 삼성화재 20250311001055 실값 hermetic fixture 3종(decoy 2 + genuine 1) + 선택성 테스트 3개.
  build→run→observe→assert(추측 금지). measurement=장기손해 변동내역(신계약 3,451,183),
  insurance_pl=보험손익 상세(CSM상각 1,612,298 / 합계 8,833,157), reinsurance=출재 신용위험 익스포져
  (합계 1,382,954). 각 decoy 선택 시 fail하도록 assert.

### 검증 (에이전트 보고 불신, 메인세션 직접 재실행)
- `pytest tests/unit/` → **110 passed** (107→+3 E2E).
- **HEAD 독립 byte-identity**(테스트 리터럴 순환 차단): git HEAD 원본 상수 vs 외부화 후 로드값 ast 비교
  = bs 7 + sens 8 = **15/15 일치**.
- E2E assert값 9/9 소스 JSON 실재(날조 0). consumer 4종(viz_panels·batch_bs·batch_sens·ingest_audit) 파싱 OK.

### 잔여 = REFACTOR-3 slice2뿐 (= K-ICS/solvency 레인 소관)
- slice2(`src/solvency/parser/` column-picker/`_canonicalize_table_label` → 레지스트리)는 solvency 코드라
  **ifrs17 레인 세션 범위 밖**. kics 레인 세션이 이어받을 것. owner 리뷰의 "GOLDEN-E2E 확장"은
  measurement/insurance_pl/reinsurance까지 확장 완료로 충족.

status: open (ifrs17 레인 refactor 전부 완료 — bs/sens 6/6 + E2E 3종 done; 잔여 REFACTOR-3 slice2는 kics 레인).
