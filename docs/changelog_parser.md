# Parser Changelog (Stage 2)

> Last updated: 2026-06-13 · Stage 2/5 — parser (COMBINED — frozen at lane split)
> Prompt: docs/agents/claude-agent-parser.md · TODO: TODO_parser_kics.md / TODO_parser_ifrs17.md

> [!note] Lane split 2026-06-13 — this file is the **FROZEN pre-split combined history**.
> New entries go to [`changelog_parser_kics.md`](changelog_parser_kics.md) (K-ICS solvency) or
> [`changelog_parser_ifrs17.md`](changelog_parser_ifrs17.md) (IFRS17 CSM/PL). Nothing new is appended here.

Parser-specific history. Cross-stage entries keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).
Domain refs: [`docs/domains/claude-agent-{kics,ifrs17,misc}.md`](domains/).

Convention (see [`docs/agents/doc-style.md`](agents/doc-style.md)): current-month entries detailed; older ones collapsed to 1-liners in `## Archive` (git log has commit-level detail).

---

## 2026-06-14 (x) — K-ICS 시장위험 36-40/41-46 대량 회수 (200+ RED 정면대응, SKIP 철회)

owner/validation 지적대로 200+ RED는 룰 아티팩트가 아닌 **파서 underparse**. 이전 SKIP 권고 철회하고
실제 회수. **LLM 추출 + 수학 reconcile 게이트** 파이프라인(ultracode Workflow):

- **NEW `scripts/extract_market_section_pages.py`** (Phase 0): 병렬 pdfplumber + per-PDF 180s 타임아웃.
  대형 생보 4Q PDF(555~740p)의 시장위험 섹션만 국소화 → per-(co,q) md artifact. 298 OK / NO_SIGNAL 38.
  (구 `market_subrisk_pdf_recover.py` monolith는 거대 PDF 1개에서 56분 행 → 병렬+타임아웃 격리로 해결.)
- **NEW `scripts/wf_recover_market_subs.js`** (Workflow): (co,q)별 agent가 국소페이지 읽어 36-40(+41-46
  IRR) 추출 → `sqrt(V'·M·V)≈item19 <2%` reconcile 게이트(환각 차단) → 미달 시 적대적 재독. 384 agent.
  대형 생보는 위험별 '현황' 섹션 분산이라 regex 불가 = LLM 읽기 정답.
- **NEW `scripts/apply_market_recovered.py`**: 단일 writer, reconcile 통과분만. RECOVERED found가 정본 →
  기존 부분/오도값 8건 덮어씀(에이아이에이 24.2Q 37↔38↔39 자리뒤바뀜·코리안리 36 stale 등).
- **결과**: 36-40 5종 완비 **103→264**, 19_market reconcile **264/264 pass 0 fail**, 41-46 IRR **144→177**
  (0 fail). NEW gold `data/_gold/market_subrisk_recovered_gold.json` (2382 cell, 재생성).
- **핵심 수정 (partial_reconcile)**: 소형사(처브·신한이지·교보플래닛 등)는 부동산/자산집중위험액이 진짜 ~0이라
  agent가 3종만 추출 → 초기 `nonNull>=4` 게이트가 PARTIAL로 오분류. **rel<2%면 누락분을 0으로 채워 저장**
  (0은 sqrt reconcile로 검증된 값, 날조 아님) → all-five 146→264로 급증. validation 21-갭 중 신한이지·처브 6건 회수.
- **잔여 ~15**: scan 2(AIA·카카오 25.4Q=owner OCR) + PDF손상 2(DB손해 24.4Q·NH 25.4Q Unexpected EOF=downloader
  재다운) + agent재시도 ~8(KB손해·한화생명·흥국·DB생명 — artifact엔 데이터 有) + 삼성생명 odd 3(MD 표위치 validation
  불일치 확인대기). EXEMPT 수동등록 불요(룰이 `_scan_breakdown_presence`로 cadence 자동SKIP). → inbox 1500Z/0600Z 핸드오프.
- 세션 한도(05:34 KST 리셋) 직격으로 1차 86건 NULL → 리셋 후 재실행 0-fail 완료.

## 2026-06-13 (w) — DEDUP-1/2: IFRS17 scorer YAML 공유리스트 단일화 (owner 리뷰 반영)

owner가 REFACTOR-1/2를 리뷰: "복붙이 Python→YAML로 이동만 했고 공유 리스트가 3중복" (정확). 처리:

- **DEDUP-1 (P1)**: `table_scoring_keywords.yaml`에 `_shared:` 블록 + YAML anchor(`&`/`*`). 리스트는
  merge key(`<<`) 부적합 → plain anchor. `&header`·`&short_term_markers`·`&direct_block_markers`·
  `&ri_block_markers`(각 3블록), `&meas_ri_row_stubs_weak`(measurement+reinsurance 2블록; insurance_pl
  row_stubs_weak는 상이 → inline). 이제 공유 리스트가 파일에 **1회 정의 + alias** = "공통 변형 1곳만 수술".
  safe_load가 parse 시점 전개 → 추출기는 full 리스트(바이트동일).
- **DEDUP-2 (P2)**: `short_term_markers` 중복 마지막 원소("보험료배분접근법을 적용하는" ×2)는 원본
  measurement_extractor.py:55-56의 복붙 오타 — byte-identity 보존이 정확히 작동한 것. `has_short_term_markers`
  membership 체크라 no-op. owner 승인대로 4→3 collapse, test_measurement 갱신.
- **무회귀**: 전체 `pytest tests/unit/` 100 passed. 공유리스트 단일정의·alias 3 확인.
- **GOLDEN-E2E (P2, csm)**: 기존 골든은 합성 단일표 `score_table` 단위테스트라 "多표 MD에서 옳은 표
  골랐나"는 미검증(owner 지적). NEW `tests/unit/fixtures/csm_e2e_meritz_2025q4.xml` = 실제 메리츠 KR0001
  2025.4Q 값 hermetic 픽스처(decoy 2개: 재무상태표 score=0·위험조정 변동 score=−3 + 진짜 CSM 향후상각표
  score=5). `test_csm_extractor.py`에 `extract_csm_tables()` end-to-end 테스트 추가 — CSM표 단독 선별·
  decoy 배제·발행보험계약 합계 11,103,697 검증. 전체 **101 passed**. (타 추출기 E2E는 후속.)

## 2026-06-13 (v) — REFACTOR-3 slice 1: K-ICS 파싱 변형 레지스트리 (owner parser_refactor)

owner inbox(`20260613T0200Z__parser_refactor`) move #1 착수. parser 코어에 하드코딩돼 "새 회사 변형
= 코어 코드 수술"이던 변형 데이터를 **append-only attributed 레지스트리**로 외부화(동결-룰 착지점):

- **NEW `src/solvency/parser/company_handlers.py`**: `SECTION_START_SPECS`(9종)·`SECTION_END_SPECS`(2종)
  ·`PUNCT_STRIP_CHARS`+`LABEL_FIXES`(OCR 치환)·`AUDIT_LABEL_ALIASES`(카카오페이/메트라이프/손보 item10
  skip)를 데이터로. 각 entry에 ASCII attribution(삼성 2023.1Q bullet, 신한 OCR 보헨위→보험위 등) — 새
  변형은 코어가 아니라 여기 한 줄 추가. `build_section_{start,end}_patterns()`·`apply_label_fixes()` 헬퍼.
- **kics_disclosure_parser.py**: SECTION_START/END_PATTERNS·`_strip_label_punct`·`_AUDIT_LABEL_ALIASES`를
  레지스트리 빌드/위임으로 교체(4곳, −70줄). 컴파일된 regex `.pattern`/`.flags`·라벨픽스·alias **바이트동일**.
- **설계 판단(owner에 surface)**: 명명된 대상(section 패턴·OCR 라벨·alias)은 KR코드 키가 **아님** — docling
  MD가 코드를 안 싣고 같은 회사도 분기마다 레이아웃이 바뀜(삼성 2023.1Q bullet vs 2023.2Q ※heading). 따라서
  **ordered 인식기 레지스트리**가 옳은 형태. KR코드→핸들러 dispatch는 진짜 코드-귀속 노브(column-picker quirk·
  값 reconcile)용으로 후속 슬라이스(fill 스크립트에 코드 스레딩)에 유보 — dead scaffolding 회피.
- **무회귀**: 기존 `tests/unit/test_kics_disclosure_parser.py` 25개(삼성 bullet/heading·신한 OCR·처브
  음수·카카오페이 reversed·메트라이프·교보플래닛·하나 — 실제 MD end-to-end) **전부 green** + NEW
  `tests/unit/test_company_handlers.py` 6개(바이트동일 락). 전체 유닛 **100 passed**. 오펀 없음.

## 2026-06-13 (u) — IFRS17 기술부채 리팩터 REFACTOR-1 + REFACTOR-2 착수 (owner parser_refactor)

owner inbox(`20260613T0200Z__parser_refactor`) 처방대로 IFRS17 추출기 6개의 scorer 키워드 복붙을
config로 외부화. 슬라이스 + 무회귀(상수 바이트동일) 게이트:

- **NEW `data/ifrs17/table_scoring_keywords.yaml`** + **NEW `src/ifrs17/scoring.py`** (`ScoringConfig`
  데이터클래스 + `load_scoring(name)` lru_cache 로더). caption_primary/secondary/verbs/negative_topic/
  row_stubs_strong·weak/header/total을 표준 필드로, 추출기별 비표준 키워드셋(block markers 등)은 `.extra`
  dict로 수용. 미선언 키→빈 튜플(추출기가 쓰는 것만 선언).
- **csm_extractor.py** (REFACTOR-1): caption_primary/verbs/negative_topic/total을 YAML 로드로 교체.
  구조 regex(year-bucket·sub-caption)는 라벨변형이 아니라 코드 유지. NEW `tests/unit/test_csm_extractor.py`
  (config 바이트동일 + score_table form A/A_rows·비-CSM cap 분류 6 테스트).
- **measurement / insurance_pl / reinsurance** (REFACTOR-2 — 복붙 3인방): 이 셋이 caption/header/row_stub
  + block markers(short_term/direct/ri)를 거의 동일하게 복붙하던 핵심 중복("변형 추가 = 3~5파일 동시
  수술"의 근원). 셋 다 YAML 블록 + `.extra`로 단일 소스화. 역사적 OCR-typo('위허조정'/'위허해제'/'재보험자
  불이행위허'/'보험송취현금흐름'/'잔여보작')까지 **바이트동일 보존**(주석 명시). NEW 테스트 2개
  (`test_measurement_extractor.py`, `test_insurance_pl_reinsurance_extractor.py`).
- **무회귀 검증**: `pytest tests/unit/` **94 passed**, 6개 IFRS17 추출기 import OK, csm·measurement·
  insurance_pl·reinsurance 상수 바이트동일 assert 통과. (csm 골드게이트는 gold 시트 0개라 no-op →
  byte-identity가 최선의 무회귀 보증.)
- **4/6 완료**. **잔여**(다음 슬라이스): bs_snapshot/sensitivity 2개(상수 스키마 상이 = bespoke, 복붙 아님
  → `.extra` 위주 외부화) + REFACTOR-3 (company_handlers.py 레지스트리 — K-ICS 산재분기 흡수). inbox answered.

## 2026-06-13 (t) — 시장위험 하위(36-40) 추출 룰 대폭 강화 + 금리위험액 회수 + owner xlsx gold 일반화 + 예별 네이밍

owner 반박("금리위험액 키워드로 바로 나오는데 왜 못 찾나; 25.4Q 손보는 롯데·KB·흥국만 해놨네"). 직접확인 결과
파서 추출 실패 확정(구조적 미공시 아님). 다축으로 복구:

- **item36(금리위험액) 회수 — IRR 현황표 total 저장**: `fill_market_subitems_to_disclosure.py`가 IRR
  순자산표(items 41-46)에서 disclosed 금리위험액 total을 **reconcile 게이트로만 쓰고 저장 안 하던** 버그.
  reconcile(<3%) 통과 시 item36으로 저장 추가. **item36 (co,q) 214→281 (+67)**. 메리츠 4464.98억·한화
  1237.76·현대 3227.67·DB 8243.48 등 — 전부 IRR표에 있었음.
- **시장위험 5종 분해 추출 재작성 — `extract_mkt_subs` 전면 개편**: (1) 블록당 "시장위험액+금리위험 동시
  존재" 요구 제거 → docling `<!-- image -->` **분절 단독 fragment**까지 전 MD 스캔(하나손해 25.4Q
  주식/부동산/외환/자산집중이 각각 단독표라 누락됐던 것). (2) `_bare_subrisk_item`: enumerator 접두
  ('1.금리위험액'·'Ⅳ.'·라틴'IV.') strip + 'X위험액' 변형 + col0 sentence 배제. (3) 값셀 = col1 이후
  첫 숫자(삼성생명 '충격시나리오 방식' 중간열 건너뜀). 19_market 행렬 reconcile<2% 게이트가 오탐 차단.
  **all-five (co,q) 90→103**. 하나손해(768 정확)·삼성생명(345522 정확) 등 회수.
- **owner xlsx 수기본 영속화 — NEW generic gold** (KR0010 전용 apply_kr0010_gold를 일반화):
  `build_user_kics_gold.py`+`apply_user_kics_gold.py` → `data/_gold/user_kics_cells.json` (550셀/4 OCR사:
  미래에셋 240·AIA 260·동양 21·악사 29; 파생27/28·빈칸 제외, 엑셀수식셀은 data_only 캐시값). 미래에셋
  2026.1Q·AIA 2024.4Q~2026.1Q·동양 2026.1Q 채워짐. + 금리민감도 60행(10생보)
  `build_apply_user_ratesens_gold.py`→`user_rate_sensitivity_rows.json`(kics_rate_sensitivity 435→495).
- **예별손해보험(KR0004) 네이밍**: 구 MG손해보험. owner 누차 지시 + 다운로더 URL yebyeol.co.kr 확인
  (기존 주석 '구 예별'은 반대로 오기). kics_disclosure 33행 원수사명 정정 + raw/MD 파일명 + seed/다운로더/리포트 정정.
- **검증 스테이지 병렬작업 합류 확인**: 검증이 owner 직접지시로 dedup(`dedup_kics_disclosure.py`, 16160→15665,
  항등식으로 정답 1행 채택) + targeted fix(하나손해 26.1Q item2 ×100→28.62%·AIA copy-leak 값_적용후·코리안리
  자동차=0) 적용. 본 세션 변경과 **공존 확인**(중복 0, 정정 보존). 파서는 dedup을 파이프라인 마지막에 실행.
- **게이트 잔여 RED 분류** (검증 소관 hand-off, inbox): (a) 19_market 룰이 **item36만 있어도** 5종 분산합
  공식으로 reconcile 시도→거대 diff RED (삼성생명 24.2Q 등) = 룰 아티팩트, 부분-하위 SKIP 처리 필요.
  (b) rule5 메리츠 12분기 = dedup이 item23(기타요구자본 40)을 0으로 채택(14가 +40 함의). 둘 다 validation 소관.
- **한글 OCR 조사**: 동양=스캔 아님(ToUnicode 없는 CID폰트, **글리프맵 무손실 복구가 정답**), 미래에셋=텍스트레이어
  **숫자 깨짐**(병합) 위험케이스. OCR 무설치(tesseract-kor ~50-100MB 필요). 결론: OCR은 gate-safe 불가 →
  owner-gold 보조(초안 prefill)용, 스캔/깨진사는 gold 유지.
- **생보 경과조치 적용후 item14후 적재** (backlog 신규-2, owner xlsx #3 블로커): `fill_post_transition_to_
  disclosure.py` 두 버그 수정. (1) "전=후면 스킵" 룰이 지급여력기준금액 적용후(14후)를 비웠음 — 경과조치
  적용사는 가용자본만 변하고 요구자본 base(14)는 불변이라 14후=14전이지만 **명시 적재돼야** 검증식
  (2후+3후)/14후×100≈27후가 닫힘(유도 15후-22후+23후는 ②표 경과조치-감소 15후 때문에 틀림). 경과조치
  적용사(전≠후 존재)에 한해 코어 {1,2,3,14,27} 동일값도 적재. (2) `_is_market_or_rate_section`이 '금리위험'
  부분일치로 **주요변동요인 서술문**까지 ③섹션으로 오분류 → 처브 공통적용표 제외됐음 → '주식위험경과조치'/
  '금리위험경과조치' 인접 매칭으로 좁힘. **25/25 (co,q) 검증 통과**(ABL·푸본현대·iM·IBK·농협 20 + 처브 등).
  rule 8_post RED 해소, GREEN 3739→4028.
- **신규 RED은 전부 validation 룰 아티팩트(핸드오프)**: 19_market 220(부분 item36-only/전결측에 분산합 reconcile
  오발화)·36_irr 23(item36 present인데 41-46 부재 → exp=None RED, SKIP해야)·rule5 13(메리츠 dedup item23=0).
  내 데이터는 owner 지시대로 더 채워졌고(item36 281·all-five 103·14후 25), 룰이 부분데이터에 RED 대신 SKIP하도록
  validation 조정 필요.
- 신규 도구: `census_market_subrisk.py`(MD census), `market_subrisk_pdf_recover.py`(pdfplumber 복구+증거 census),
  `diff_xlsx_vs_kics_json.py`.

## 2026-06-12 (s) — 2026.1Q 36/39사 적재 완료 + MG/AIA 신규 편입 + 파서 핵심버그 2건 수정

owner 지시("26.1Q 39개사 전부") 이행. kics_disclosure 2026.1Q **0행 → 36사 1,037행** (전체 15,636행).

- **docling K-ICS 페이지 누락 5사 우회 — NEW `scripts/append_kics_detail_from_pdf.py`**: 삼성화재/악사/
  DB생명/농협생명/하나손해는 cap-40 재변환에도 K-ICS 세부 페이지가 MD에서 탈락(텍스트레이어는 정상).
  pdfplumber로 [세부] 표를 PDF에서 직접 추출(병합셀 개행분해 + 백만원→억원 환산 + 악사형 pre/post 2차모드)
  → 표준 헤딩과 함께 MD append → 기존 fill 파이프라인 그대로 소비. 재변환 시 재실행 필요(마커 idempotent).
  cf. 삼성 zip은 '연결 검토보고서'가 최대 PDF — '경영공시_최종.pdf' 멤버를 명시 재추출.
- **파서 fallback 2종 신설** (`kics_disclosure_parser.py`): `_kics_detail_table_anywhere_rows`(헤딩 소실 시
  quarter-컬럼 매칭 + 지급여력금액/기준금액 라벨 검증으로 세부표 탐지 — 한화손해 27행),
  `_kics_pre_post_table_rows`(경과조치 표만 남은 MD용, 코어라벨 allowlist + nearest-preceding 단위 스케일).
- **버그 1 — `_strip_label_punct` 치환 역방향**: 신한 OCR 교정('보헨위'→'보험위')이 거꾸로(정상→오타)
  구현돼 있었음. 양쪽 동일오염 시 무해했으나 공백변형('보험 위험액')이 미매칭 → item17/18 누락
  (현대해상/흥국화재/카카오페이 2026.1Q). 방향 교정 + 장기손액 교정도 정상글자 기준으로.
- **버그 2 — fill_period 값_적용후 누출**: 신규 분기 행 생성 시 `dict(base)`가 직전분기 `값_적용후`까지
  복사(메리츠 26.1Q 적용후<적용전 rule9 RED 3건). pop 가드 추가 + 26.1Q 적용후 112행 전삭제 후
  fill_post 재생성(63행, 메리츠 50,632.45 정상).
- **신규 회사 편입 — NEW `scripts/seed_new_companies.py`**: KR0004 MG손해(2026.1Q 27행, 비율 -13.11%)·
  KR0080 AIA생명(마스터에 회사 자체 부재 → 2023.1Q/3Q/4Q+2024.1Q~3Q 6분기 적재). 시드 1행(item1)로
  fill의 same-quarter-partial 경로 활성화.
- **섹션/픽커 보강**: 헤딩 `[ 경과조치`(괄호 뒤 공백) 허용, '2023년1Q' 헤더 변형 매칭 — 동양 2023.1Q
  백만원 leftover 7행(item12 오염 포함) → 정식 세부표 29행(억원)으로 교체.
- **게이트**: RED 227 = 19_market 223(구조적 미공시 — EXEMPT 등록 요청 inbox 발신, census
  `artifacts/kics_validation/market_breakdown_red_census_20260612.md`) + 악사 26.1Q 4건(세부표 이미지).
  root TODO.md에 documented-exception 등재. rule9/2/4/5/6(동양·현대·흥국화재·카카오·메리츠 계열) 전부 해소.
- **발견(미해결)**: (code,q,item,name) 중복 행 94키(값상이 65) — dedup 슬라이스 TODO_parser 등재.
  스캔-only PDF: 미래에셋 전구간 / AIA 2024.4Q~26.1Q / 동양 26.1Q / 악사 26.1Q 세부 → owner gold 요청.

## 2026-06-11 (r) — KB손해(KR0010) owner gold cell 적재(RED=0 달성) + 2026.1Q 파싱 착수

owner xlsx 수기검수: KB손해 정합성 결여 cell(24.2Q·25.4Q·26.1Q) 정정값 제공. KR0010은 image-only(OCR) filer라
MD 파이프라인이 부정확 cell 생성(rule2 RED 2건) + 재빌드 시 덮어씀.
- **gold 영속화**: `data/_gold/kr0010_user_cells.json`(파생 27/28 제외, 24.2Q 37 / 25.4Q 34 / 26.1Q 24 cell) +
  신규 적용기 `scripts/apply_kr0010_gold.py`(UPSERT; 26.1Q 42행 신규생성). **fill_period→apply_kr0010_gold→recalc 순서**로
  재빌드에도 생존. recalc가 27/28 파생 재생성.
- 핵심 정정: 24.2Q item4 11,559→**115,559**(OCR 자릿수)·item12 121,661→528 등 / 25.4Q item4 19,985→109,985 + 29-40
  시장위험·생명장기 하위 채움 / 26.1Q 전 capital cell 신규.
- **게이트 `validate_kics_disclosure.py`: RED=0 최초 달성**(기존 KR0010 OCR RED 2건 해소; KICS-IMG 예외도 불요해짐).
  GREEN 3239→3248.
- **2026.1Q 파싱 착수**: kics_disclosure에 2026.1Q가 통째로 부재(2025.4Q까지만)였음 — owner 지적. raw PDF 37사 존재하나
  MD 0 → `run_harness --stage parse --period FY2026_Q1 --pdf-root raw` docling 변환 진행(일부 대형 PDF std::bad_alloc).
  변환 후 fill_period 적재 + 시장위험/금리민감도/CSM/PL 2026.1Q 확장 예정.
- **시장위험 36-40 현황**: `fill_market_subs_from_pdf` 재실행 결과 추가 복구 0(worklist 299 중 reconcile 96 전부 적재완료).
  분기당 13-22사뿐인 잔여는 PDF에 세부표 없는 **구조적 비공시**(삼성화재 등) — 2026.1Q item19 적재되면 그 분기 worklist 신규편입.

## 2026-06-11 (q) — 현대해상 PL 3/7/8/12 복구 (owner gold 반박 수용) + 13/14 gross 전환

validator iter-2(`...KR0009__hyundai_pl_legit_misjudge`): owner gold(`gold/보험손익 breakdown_현대해상_2026.1Q.xlsx`)가
직전 "legit_absent(GMM합 17% 불일치로 도출불가)" 판정을 반박 — 수용·수정. `extract_tier2_hyundai` 확장:

- **NEW form(2025.3Q+) LOB 합계 추출**: rev=단일행 '보험수익' 합계변형(PAA 쌍둥이 장기=0 제외, 연결/별도 동률 시
  later-wins=별도) / cost·rerev=분석공시 총행(분기·연차 라벨 각각) / recost=단일행 '재보험서비스비용' 합계변형.
  assemble이 3·8·7·12·2 도출. **13/14는 수지현황 netted → 분석공시 gross(재보험 포함)로 교체** — gold가 컨벤션 입증
  (자동차 −10,891.09 정확 재현). 과거 audit이 기각했던 "GMM합 409,705"가 실은 정답(수지현황은 사업비 차감 netted).
- **gold 게이트: 2026.1Q 7항목 전부 정확일치(Δ<1백만)**, 2025.3Q/4Q 포함 3분기 브리지 잔차 0.0. blast radius KR0009 한정.
- **2024.1Q~2025.1Q 5분기 = 도출불가 확정(정밀 근거)**: OLD form은 보험수익·재보험서비스비용만 LOB 분리, **보험서비스
  비용·재보험수익은 LOB 미분리**(FY2024_Q1 전수 표 확인) → 3/8 원천 부재. 2025.2Q는 owner 확인 legit. ZLEG per-quarter
  목록 `현대해상 2024.1Q~2025.2Q`로 회신.
- **컨벤션 혼재 공지**: 2025.3Q+ gross(1=2+13+14−16) vs 이전 netted(1=2+13+14, 사업비 LOB배분 비공시로 변환 불가) —
  validation eq 분기별 처리 요청.

## 2026-06-11 (p) — 값_적용후 정합 2건 (owner R1-후 xlsx 검수) + recalc 분모버그 수정

owner inbox `20260611T0000Z__owner__MULTI__post_capital_legs` 처리. `kics_disclosure.json` 7셀 + 파생 62셀.

- **농협생명 KR0104 2024.1Q/2Q 값_적용후 복사버그**: 2023.4Q의 후값(기본 35,651.31/보완 40,110.8)이 두 분기에 복사
  적재돼 있던 것 — 각 분기 자체 MD [전|후] 백만원 표로 정정(Q1 30,176.09/45,499.70 · Q2 29,367.52/44,611.24,
  합=item1 전값 정확일치). 후기본−전기본=+2,500억(신종자본 재분류) 패턴 2024.3Q+와 일관.
- **삼성화재 KR0008 2025.3Q**: 후 분해 적재(기본 179,287.94/보완 107,214.02 — 전=후, 주1 명시) + **item1후
  286,051.95는 원천 자릿수전위 오타로 판정·정정(→286,501.95)**: 후 비율 275.92=전 동일, 오타값 역산 275.49% 불일치,
  28,650,195↔28,605,195. 3중 증거(비율·주석·분해) 기반 documented 정정.
- **recalc_kics_derived.py 분모버그**: item28후 재유도 분모가 전(i14) 고정 → validator 8_post(후14 우선, fallback 전)와
  불일치 — 선택 경과조치 적용사(농협·처브·교보플래닛 등 후14 공시사)에서 8_post RED 양산됨을 1차 재실행에서 확인 후
  **공식을 validator와 동일하게 수정**(den14=post14 우선), 62셀 재유도. 교훈: 파생 recalc는 검증룰과 공식 1:1 대조 후 실행.
- 게이트 `validate_kics_disclosure.py` **RED=2**(KR0010 OCR documented만, 신규 0)·GREEN 3,239. xlsx 재생성.

## 2026-06-11 (o) — 사용자 xlsx 검토 최종 closure: PL gold-cell 170셀 + WFY 10/10 판별

validator 4갈래 패키지(`20260611T0900Z`) 전 항목 종결. 최대 모드(대량 fan-out 중단, 직접+검증 위주).

- **PL 감사 10/10사 완료** → 정답값을 `_GOLD_CELL_OVERRIDE`로 적재(핸들러 신규작성 대신 — 감사 자체가 "life_old 선점
  제거는 4/5/6 회귀 유발" 경고한 케이스 포함). **+170셀, blast radius 5사 14분기 한정(타사 0, 전수 diff)**:
  케이디비(2023.2Q OLD양식 13셀 + 2025.2Q~26.1Q 9/10/12·**item11 레그혼합 오류 4분기 교체** — 25.4Q raw 재검증:
  노트 실제 42,611−예상 35,399=7,212 vs 공표 39,470) / 라이나·메트라이프(비상장 감사보고서-only, Q4 전항목 재구성
  22셀×4) / 미래에셋(2023.1Q/2Q, 공표 시리즈 연속성 검증) / 동양(2023.1Q·2024.4Q item6 leg보정 20,691·2025.2Q/3Q).
  KDB 2023.2Q의 15/17/18은 OLD 양식 매핑 모호 → 보류(owner gold 대기). 미래에셋 2025.2Q KDB item6 오염 의심 1건 잔존(TODO).
- **WFY 10/10 판별**: ① DB손해 FY2023 = 원본공시가 분기마다 기초 재작성(118,270→122,497→117,349→116,435, 비단조) →
  롯데 선례대로 연차기초 116,434.9 re-anchor(override 18셀, 보정 Q4기말=FY2024기초 **정확일치**, 전분기 항등식 0).
  ② 교보 FY2023/FY2024 = **공식 소급재작성**(3Q24 주석: "CSM 상각 시간가치 계산 오류" + 금감원 가이드라인 회계정책변경)
  — 최신 정정본 재추출이 현 마스터와 전항목 일치 → legit, 수정 불요. ③ 잔여 7건(한화생명·현대·케이디비·메리츠·KB라이프·
  에이비엘·농협생명) = probe(waterfall_for_dir 재실행) 결과 **전부 분기당 필링 1개(정정공시 無) + 마스터=필링 충실** →
  원천 자체의 단일 클린 재작성(반기 또는 연차 시점) = **legit_restatement documented**, 데이터 수정 불요.
- 재빌드 체인 + xlsx 갱신. CSM overrides 62 set/12 add/1 excl.

## 2026-06-11 (n) — PL Tier-2: 롯데 2025.2Q 표준양식 + 악사 전용핸들러 (extraction-miss 잔여 closure)

`scripts/build_pl_breakdown.py`. diag(`data/dart/viz/pl_breakdown_master.json`)까지 재빌드 — 루트 마스터 조립은 메인 세션.

- **롯데 KR0003 2025.2Q** (반기 `20250814003966`): 주석25가 이 분기만 DART 표준양식 분해주석(레그별 서브헤딩 +
  [3개월|누적]×[장기|일반|자동차] + '합계' 레그, '총…'행 없음). split-핸들러 3보강: ① `_lotte_from_sections`에
  표준양식 라벨 2nd needle('서비스의 이전으로 당기손익에 인식한 보험계약마진' 등), ② '재보험비용의 보험서비스비용
  분석 공시' 서브헤딩 = 재보험 회수수익(re_rev) 레그 매핑, ③ grand-total fallback('총…'행 부재 시 섹션 마지막
  테이블의 마지막 numeric 행). 13셀 보정: item4 52,270(3개월 leg 오염)→104,548(누적), 5: 7,745→15,072,
  6: −8,256→−22,785, 9: −1,261→−2,456, 10: −657→−1,097, 2/3/7/8/11/12/13/14 null→채움. 브리지 잔차 0.0
  (item1 21,631 = ΣLOB 37,114 + 15 − 16(15,483)). item4 YTD 연속성 ✓ (1Q 52,278 → 2Q 104,548 → 3Q 156,316 → 4Q 213,943).
- **악사 KR0049 전용핸들러 신규** (`extract_tier2_axa` + `SONBO_HANDLERS["KR0049"]`): 연차 감사보고서 '(6) 보험손익
  상세내역' note (천원, 컬럼 [자동차|일반|장기|합계] — 장기-first 아님). generic Format-A가 `_row_nums`의 '-'셀
  collapse로 컬럼 오매핑(2024.4Q: item3에 자동차 레그 −918, item6=95,418 = rev_exp−재보회수예상 오염; 2025.4Q는
  RC게이트 suppressed → 13항목 null). 새 핸들러: 헤더기반 LOB 컬럼매핑 + 4섹션(보험수익/보험서비스비용/출재보험수익/
  출재보험비용) 워크 + 비PAA/PAA 중복라벨은 target-LOB가 numeric인 첫 행. **악사 IS는 기타사업비용을 Ⅰ.보험손익
  내부('3) 기타사업비용', 원단위)에 둠** → 핸들러가 item16 emit(기존 Tier-1 16=0.0016은 '16,25' 주석참조 오파싱),
  RC adj-브리지 정확 폐합(2024.4Q: −7,078.456 − 10,561.922 = item1 −17,640.378). 26셀 보정, 양분기 RC ok.
- **blast radius**: KR0003 2025.2Q(13셀) + KR0049 2024.4Q/2025.4Q(26셀)만 — 타 회사·분기 0셀(전수 diff).
  직전 세션의 현대 KR0009 수정(2025.3Q item6=−322,635/item11=−9,203, 2026.1Q item6=−126,865/item11=+2,075) 보존 확인.
  악사 2025.2Q/3Q/2026.1Q는 raw_not_extracted(다운로드 갭, meta.json만) — 파서 범위 밖.

## 2026-06-10 (c) — owner xlsx 수동검토 정정: CSM override 영속화 + 3사 제외 (1926→1908행)

owner가 통합 xlsx로 마스터를 수동검토, CSM워터폴 H열(값) 직접 정정 + 신규행 입력. xlsx-vs-JSON diff로
편집분 44건(set 32 + 신규 12) 추출 → **`data/dart/viz/csm_manual_overrides.json`** 생성,
`build_root_masters.py`에 적용 훅 추가(diag 로드 직후 exclude→upsert→당분기 재계산). **diag 재빌드에도 정정 생존.**

- **롯데 KR0003**: 2023.1Q 전항목 신규 + 2023.2Q 정정(기초 18004.6→16774.38). root cause = 다중 정정공시 중
  구공시 채택. 기존 justified_restatement verdict는 owner가 반증(구공시 오채택이 진실).
- **케이디비 KR0072**: 2023.1Q/2Q 상각 공란→실값(-111.25/-234.15) + 조정·기말 정정.
- **미래에셋 KR0079**: 2023.1Q 신규 + 2025.2Q~2026.1Q 상각 0→실값·조정 재산출. '기타' 테이블 CSM 누락은
  비용 크면 패스(owner). 경계 drift 2건(2023.2Q Δ2.25억·2025.2Q Δ6.5억)은 원천 재진술성 — documented로 노출.
- **3사 제외(owner 결정)**: 하나손해 KR0050·하나생명 KR0097·신한이지 KR0051 — CSM waterfall 분리공시 불가
  (보험손익만 분해 가능). CSM_waterfall(−30행) + NB_CSM_multiple(−5행, 파생) 제거. CSM_amortization의
  하나생명 상각스케줄은 직접공시라 유지. HTML '분리공시 미제공' 처리는 designer 핸드오프(root TODO).
  **[보정 2026-06-11 — 하나 2사 복원, 신한EZ만 제외 유지]**: 소스가 지주 사업보고서가 아니라 **각사 감사보고서**
  임이 확인되자 owner가 복원 지시 → 검증: 하나손해(기말 2,802·신계약 1,506·상각 −219억)·하나생명(기말 4,390·
  신계약 3,240·상각 −399억) 모두 감사보고서 경영서술 수치와 **정확 일치** = 진짜 데이터 → 복원(1908→1926행,
  NB +3행; 복원된 하나손해 NB배수 11.0/14.0 = 정상범위). **신한EZ는 ×1000 단위오류**(변동표 천원인데 백만원
  오인 — 진짜 신계약 10.1억·기말 CSM 1.69억) + PAA 중심으로 CSM book ~2억 = 워터폴 무의미 → 제외 유지.
- **데이터소스 질문 회답**: 비상장사(라이나/BNP/아이엠/메트라이프/처브/교보플래닛/카카오페이/AIG)의 CSM 소스 =
  **각사 자체 DART 감사보고서**(첨부 XML `_00760`=별도; 접수번호 확인). 아이엠라이프도 DART 감사보고서 존재
  (정기보고서 카테고리엔 없음). 하나/신한EZ도 자사 감사보고서에서 추출했었으나 owner가 분리불가 판정 → 제외.
- **검증룰 발주(validation inbox)**: AMORT_ZERO — item5(상각)=0/None인데 기초/기말 양수면 RED (미래에셋 사례).
  체인 재실행: build_root_masters → update_tickers → build_nb_csm_multiple → build_master_xlsx. 전 항등식 OK.
- 후속 조사(Workflow 11 agents): NB배수 분모 '기타' 초회보험료 혼입(농협/KB라이프/교보/한화/삼성 IR 대조) +
  PL 0값 회사별 감사(현대해상 생명장기 6항목 등 10사) — 결과는 (d)에.

## 2026-06-11 — 사용자 xlsx 검토 후속: NB 분모 EX-기타 + 아이엠 분자정정 + 하나 복원 + PL/WFY 분류

owner xlsx 수기검토(롯데/케이디비/미래에셋 정정) + validation 4갈래 조사 후속. (validator inbox
`20260611T0900Z__...user_xlsx_audit_followup`.)

- **NB배수 분모 = 월납초회(VAL4)만** (`build_nb_csm_multiple.py` load_wolnap): 기타초회(VAL8, 단체물량) 제외. owner 지적
  (농협 568억 기타혼입) 확정 + 검증: 농협생명 3.71→11.20·NH손해 1.74→11.38·KB라이프 9.10→10.48·삼성생명 10.11→11.47
  (2026.1Q, validator 예측 정확일치). 삼성 IR factsheet MAE 1.15→0.40, 한화 9.84 일치. 전사 중앙값 11.3, 10~17 범위 22/32.
  `_MULT_FLOOR=1.0` 하한 플래그 추가(분자붕괴 표면화).
- **아이엠라이프(KR0076) 워터폴 분자오염 정정** (override): 구성요소별 변동표에서 **합계열(BEL+RA+CSM=443) 오선택** →
  CSM열(tok[2]+tok[3]=159,982)만 행별 추출로 전 워터폴 재구성. gold 일치(신계약 1,356.6/1,599.8억, 기말 7,614.5억≈
  narrative 7,590). `csm_manual_overrides.json` 12항목, 항등식 Δ0. NB배수 0.02→8.36/8.82. (정식 빌더 핸들러는 큐.)
- **하나손해/하나생명 복원, 신한EZ만 제외**(별도 changelog 항목; 06-10 (c) 정정).
- **PL 생명장기 None 무더기 분류(5사)**: 대부분 JSON null(분리불가 legit, xlsx 빈칸=0 아님) — owner의 "전부 0"은 HTML
  null→0 렌더. 진짜 extraction_miss = 현대(예실차 2025.3Q·2026.1Q, CSM상각 2023.1Q~2Q)·롯데(2025.2Q~ 고유레이아웃)·
  악사(2024.4Q/2025.4Q generic fallback 실패). NH·ABL은 의도적 convention. → designer null='—' 권고 + miss 핸들러 큐.
- **세션한도(5am Asia/Seoul)로 큐**: PL 5사(미래에셋·라이나·케이디비·메트라이프·동양) 감사, WFY 10건(DB손해 FY2023 등 구판
  보고서 의심), 아이엠 빌더핸들러 정식화, PL miss 핸들러 보강.
- **검증룰 신규 요청(→validation)**: ① NB배수 <1.0 하한(분자붕괴) ② CSM 상각액=0 불가(미래에셋 25.2Q+ 0 인식 — owner 지적).
- 재빌드 전체(build_root_masters→update_tickers→nb→xlsx) 완료.

## 2026-06-10 (b) — docling 페이지선택 v4: 민감도 섹션 탈락 수정 + KR0075/KR1000 재파싱 (+12행, RS4 해소)

downloader가 재-docling 요청 2건을 반송(raw 완비, 근본원인=parser MD-생성 파이프라인; **docling=파서 소관, 사용자 결정**).
파서가 직접 수정·재파싱:
- **근본원인 실측:** 페이지선택이 키워드 score 상위 N(캡 16)만 docling하는데, 6-8 위험민감도 페이지는 score 3(지급여력
  비율/금액/기준금액)뿐이라 **KR0075 FY2025_Q4에서 rank 18 → 캡 탈락**. KR1000 FY2025_Q2는 MD 자체 미생성.
- **수정 (`src/solvency/parser/docling_parser.py`, `docling_partial_v3`→v4):** ① 키워드 +3(위험민감도/금리민감도/환율민감도,
  공백정규화 매칭) ② `max_keyword_hit_pages` 16→**20**(기존 top-16 ⊂ top-20 → 섹션탈락 회귀 0) ③ 프로필 bump(멱등 재실행).
  `run_harness.py` CLI 디폴트 동기화.
- **재파싱(`--pdf-root raw`, pdf/ 스테이징 비어있어 우회):** KR0075 재변환(conf 0.73, 헤딩 **LOST 0**/GAINED 18) +
  KR1000 신규(conf 1.0). 추출기 재실행 423→**435행(+12)**: KR0075 2025.4Q(253.35/2,031/801) + KR1000 2025.2Q
  (204.45/44,902/21,963). diag suspect_truncation 2→1(KR0010 진짜부재만).
- **검증:** `validate_kics_rate_sensitivity.py` RS1 0 RED / RS2 0 RED(+exc) / RS3 30 Y(정보성) / **RS4 hole=0**
  (코리안리 2025.2Q YELLOW 해소). gate RED=0. xlsx 재생성.

## 2026-06-10 — 티커 정정: OpenDART 종목코드로 전 마스터 갱신 (사용자 검토)

기존 티커가 무작위(37사/고유 15개, 메리츠=카카오페이손보=60 중복, 삼성생명·동양·미래에셋 등 상장사가 X로 오기).
신규 `scripts/update_tickers_from_dart.py` — OpenDART `corpCode.xml`의 `stock_code`로 런타임 해석(영구 매핑파일 미생성,
재실행 가능), 6개 마스터 `티커` 패치. 미상장(stock_code 공란)=`X`, 상장=6자리 코드(앞자리 0 보존).
- **상장 14사**: 메리츠 000060·한화손해 000370·롯데손해 000400·흥국화재 000540·삼성화재 000810·현대 001450·
  KB손해 002550·DB손해 005830·한화생명 088350·삼성생명 032830·미래에셋 085620·동양 082640·서울보증 031210·코리안리 003690.
- **미상장 23사 = X**. 접미사 strip은 `보험`/`재보험`만(삼성생명보험→삼성생명 등); `생명보험` strip은 2글자 stem(흥국·DB)이
  무관 상장사에 오매칭돼 제외.
- 주의: KB손해(002550)·메리츠(000060)는 자회사 편입/상폐됐어도 DART가 코드 유지 → DART값 사용(사용자가 X 원하면 조정).
- 패치 후 `build_master_xlsx.py` 재생성. **마스터 재빌드 시 이 스크립트 재실행 필요**(티커는 입력 xlsx→kics_disclosure에서 유입).

## 2026-06-10 — 신규 feature: K-ICS 지급여력 금리민감도 추출 (kics_rate_sensitivity.json, 416행)

owner 발주(inbox `20260610T0100Z__owner__...kics_rate_sensitivity`). 정본 스펙 `docs/agents/kics-rate-sensitivity-spec.md`.
신규 추출기 `scripts/extract_kics_rate_sensitivity.py` — `md_inbox/FY*/*.md` 전분기 스캔 → 루트 마스터
`kics_rate_sensitivity.json` (long-format, 1 row = 사·분기·경과조치·measure) + diag `data/_derived/kics_rate_sensitivity_diag.json`.
기존 마스터 무변경(신규 파일만) = 회귀 0.

- **소스:** 경영공시 `금리 민감도 분석` 2-key 매트릭스(경과조치 적용전/후 × measure{비율/금액/기준금액} × {base,±50,±100bp}).
  값 컬럼순서(기준금액 먼저) → `-100bp,-50bp,base,+50bp,+100bp` 재배열. prefix(티커·생손보)는 kics_disclosure에서 복사.
- **커버리지:** 섹션 FY2024_Q4부터 등장(FY2025 Q2/Q4 중심). 74 (사,분기) 적재, **416행**. FY2023~FY2024_Q3 부재=정상(서식 도입 전).
- **자기검증 내장 — RS1(비율≈금액/기준금액×100):** 전 블록 통과(**rs1_fail 0**). RS2(적용전 base vs kics_disclosure
  item1/14/27) 전수 교차 **215 OK / 1 mismatch**.
- **엣지 처리:** ① delta 인코딩(흥국화재·흥국생명 FY2025_Q2/Q4 = shock이 base 대비 변화량) → absolute 1차→RS1 실패시
  `base+delta` 재해석, **delta_converted 4**. ② 경과조치 세로분할 라벨(`경 과/조/치 전`) → 블록 col0 합쳐 전/후 판정.
  ③ 적용후 all-dash → rows 생략 + **post_dash 6**. ④ 카카오페이 KR1098 OCR(char-spacing·verbatim 중복) → norm(공백제거)
  매칭 + 블록 dedup. ⑤ 동양생명 6컬럼/빈줄분할 표 → 섹션 내 다음 헤딩까지 전 | 줄 수집으로 수정.
- **RS2 base_diff 1 = KR0011 DB손해 2025.2Q:** 추출 충실(RS1 통과)이나 금리민감도표가 **주4) 별도 재무제표 기준**이라
  헤드라인(연결, item1/14/27=209,192/98,079/213.29)과 base 상이(200,558/90,447/221.74). 파싱오류 아님 = basis 차이 →
  diag `rs2_base_diff`로 자기문서화(validation RS2 RED 시 justified).
- **raw-PDF suspect 3건 대조(owner 요청):** AIA(KR0080)=PDF에 K-ICS 금리민감도표 부재(IFRS17 민감도만)+K-ICS 마스터 자체
  부재 → 진짜 부재. KB손해(KR0010) FY2025_Q4=PDF에 "민감도" 0페이지 → 진짜 부재(suspect 해소). **BNP(KR0075) FY2025_Q4=
  PDF page 75에 표 존재하나 MD 미반영 → 변환누락, 재-docling 필요**(inbox/downloader 핸드오프).
- 검증룰(RS1–4)은 validation 스테이지 발주(별도). 완료 회신 inbox/validation.
- **(validation RS1-4 통과 + RS4 콜백 처리):** validation이 RS1-4 구현·실행 — RS1/RS2 **RED 0**(KR0011 exception 코드 반영),
  RS3 28 YELLOW(ALM 정보성), RS4 1 YELLOW=코리안리 2025.2Q hole → 파서 확인 결과 **MD 파일 자체 부재**(raw PDF p27엔 표
  존재·판독 OK) = 변환누락 → downloader 재-docling 핸드오프(`...KR1000_2025.2Q__md_missing_redocling.md`). gate RED 0,
  마스터 publishing 적격.
- **(fix, 사용자 수동검토 반영 2026-06-10):** 현대·신한이지·KB라이프 등 FY2025_Q2 지급여력비율 행이 빈칸이던 버그 —
  소스가 비율을 `%` 접미사(`170.00%`)로 표기하는데 `parse_value`가 미파싱 → 비율 전량 누락. 수정 3건: ① `parse_value`
  `%` 제거 ② measure 매칭을 코어("여력비율/금액/기준금액")로 + `지금여력`→`지급여력` 오타 허용(현대 2025.2Q) ③ 라벨 없는
  전/후 동일블록이 dedup에 합쳐지던 것 → phase 배정을 dedup 전으로. 결과 416→**423행**, blank 비율 0, RS1 능동검증
  705/0 통과. (RS1/RS2는 "있는 값의 정합성"만 봐서 비율 누락=완전성 결함을 못 잡음 → 사용자 검토가 포착.) xlsx 재생성.

## 2026-06-09 (e) — 시장위험 커버리지 Phase-2: PDF 추출로 36-46 복구 (+150행, RED 0 유지)

(d) census 승인 후 빌드 완료. **MD에 누락됐지만 PDF엔 있는** 시장위험 세부표/금리위험 현황표를 fitz로 직접 추출,
**reconcile 게이트 통과분만** 저장(garbage 원천차단). 신규 스크립트 2종(기존 `fill_market_subitems_to_disclosure.py`
무수정 → 14k행 회귀위험 0):

- **`scripts/fill_market_subs_from_pdf.py` (items 36-40):** worklist=item19 있고 36-40 결측인 312분기. PDF에서
  하위5종을 interleaved/grouped/concat 전략으로 추출, **단위 자동판별**(est_raw vs item19 / est_raw÷100 vs item19),
  **M행렬합 rel<2% 게이트**. 109분기 reconcile(대부분 0.00~0.15%), 신규 **96행**. MD가 wrong값 내던 하나손해(rel 60-77%)·
  신한이지(99%)·에이비엘(25M% garbage)이 PDF로 0.00~0.7% 복구. 신한이지=억원·부동산/외환 미보유로 [36,37,40]만 저장.
- **`scripts/fill_market_irr_from_pdf.py` (items 41-46):** worklist=item36 있고 41-46 불완전인 123분기. 순자산6값 추출 후
  **PDF총액 아닌 기존 item36과 대조**(validator 정확공식+tol max(2,5%)) → 통과분만. 9분기 **54행**. 교보생명(KR0073) 전치
  (transposed)표 5분기 포함(총액토큰 부재였으나 item36 대조로 복구). 15분기는 derived≠item36(직접형 KR0097·교보라이프
  KR1010·신한이지 granular)이라 **저장 시 RED 유발 → 정확히 skip**(SKIP 유지).
- **충돌 사전검증:** 신규 item36 추가가 기존 41-46과 만나는 2분기(KR0009 2023.2Q·KR0070 2025.2Q) → derived(41-46)와
  정확 일치 확인 후 적재(SKIP→GREEN 전환, RED 무).
- **결과:** 14,244 → **14,394행(+150)**. 게이트 `validate_kics_disclosure.py` **RED=2**(둘 다 사전존재 KR0010 rule2
  OCR 예외, KICS-IMG; 신규 RED 0). 룰 `19_market` GREEN 163→**185**(SKIP 221→199), `36_irr` GREEN 42→**47**/YELLOW 17→23
  (SKIP 325→314). 진단 artifact: `data/_derived/market_gap_census.json`·`market_gap_pdf_check.json`.
- **잔여(정당/후속):** 19_market 구조적 SKIP ~100(삼성화재 전분기·삼성생명·현대해상·한화생명 — PDF에도 하위5종 비공시,
  RED 아님) / 36_irr Q1·Q3 구조적 ~85 / IRR 직접형 15(별도 schema) / 하나손해 2024.x 등 PDF레이아웃 미스(전략 fallback 후속)
  / KB손해 image-only 4(OCR).

## 2026-06-09 (d) — inbox 드레인: 시장위험 커버리지 갭 결정적 census (진짜갭 vs 구조적 SKIP)

validator inbox 신규 open 3건 처리(시장위험 도메인). T0000Z subdecomp=superseded(c에서 완료), T0300Z
loaded_pass=ack(1차패스 RED 0 확인 수신), **T0400Z coverage_gaps=메인**. 미적재 census(19_market 221 / 36_irr 103)를
추정 아닌 **기존 추출함수 재사용 전수 분류**로 회신. read-only probe 2종:
`scripts/_probes/market_gap_census.py`(MD), `scripts/_probes/market_gap_pdf_check.py`(raw PDF).
출력 `data/_derived/market_gap_census.json`, `market_gap_pdf_check.json`.

- **19_market 221:** MD단계 `table_present_fails_recon = 0`(MD에 세부표 있는데 파싱실패 0건) → 전부 table_absent/no_md_file.
  raw PDF 대조: **pdf_has_subrisk_table 112**(PDF엔 세부표 있는데 MD 미반영 → fitz추출로 복구가능, 로직버그 아님) /
  **pdf_market_total_only 100**(PDF도 합계라인만 = 구조적 비공시 = 정당 SKIP; 삼성화재 전분기·삼성생명·현대해상·한화생명 등) /
  image-only 4(KB손해 OCR) / no_market 5.
- **validator 전제 보정:** spec §5가 지목한 현대(concat)·한화/KB라이프(컬럼)·에이비엘/메트라이프/라이나(다중컬럼)는
  1차패스에서 이미 GREEN 저장됨, 미적재 221에는 없음. 남은 갭은 "MD 파싱패턴" 아닌 "PDF→MD 세부표 미반영".
- **36_irr 103:** scenario_table_absent 90(**Q1/Q3 85 = 구조적 부재 정당 SKIP**, validator 가설 확정; Q2/Q4 5 확인要) /
  reconciles_storable 6(rel 0~5%, 저장됐어야 함 = 로더버그) / table_present_no_total 3(교보 total-anchor 보강) /
  table_present_fails_recon 4(하나생명·교보라이프 직접형, deferred).
- **로더버그 발견:** `fill_market_subitems_to_disclosure.py`의 41-46 PDF추출이 MD파일 루프 내부에 중첩 → MD 부재 시
  PDF 정상이어도 IRR추출 미시도. reconciles_storable 6건 원인. 수정안: MD/PDF code 합집합 순회.
- **Phase-2(미착수, 범위승인 대기):** 복구가능 ≈121분기(19_market PDF추출 112 + IRR 재적재 6 + 교보 total 3).
  shared disclosure JSON 변경 + 필수 K-ICS 게이트 재실행 수반 + 진단이 작업성격 재정의(로직버그→PDF신규추출경로)라
  빌드 착수 전 오케스트레이터 승인 필요. → `TODO_parser.md` OPEN 블록.

## 2026-06-09 (c) — 시장위험 하위분해 적재 (items 36–46)

`kics_disclosure.json`에 시장위험액 2단계 하위분해 신규 적재. 12,795 → **14,244행 (+1,449)**.
스크립트 `scripts/fill_market_subitems_to_disclosure.py` (29–35 적재 `fill_subitems` 패턴 확장).
정본 스펙: `docs/agents/kics-market-risk-decomposition.md`.

- **items 36–40** (금리/주식/부동산/외환/자산집중 위험액): md_inbox "시장위험액 세부내역" 표 col0(경과조치 전),
  백만원→억원(÷100). 적재 buckets 162/161/141/154/93 (부동산·자산집중은 미보유사 제외). 자기일관성 게이트:
  `19_market`(sqrt V'MV)가 item19와 <2% 재현될 때만 저장 → 163 bucket 통과.
- **items 41–46** (금리위험 시나리오별 순자산가치: 충격전/평균회귀/상승/하락/평탄/경사): raw PDF "금리위험액 현황"
  표 Ⅲ.순자산가치 행 fitz 추출(MD엔 누락된 표). Q2/Q4만 공시(반기·연차). 각 123 bucket. 게이트: 검증룰 `36_irr`과
  동일 계산(반올림 억원값 재유도 vs item36, abs tol 0.9·max(2, 5%))로 정렬 → 신규 RED 0 보장.
- **단위함정**: 세부표·현황표 = 백만원, 메인 item19 = 억원(×100). 흥국 검증: item36=1571.27억(=157,127백만 ✓),
  순자산 base=43,126.81억(=4,312,681백만 ✓).
- **검증 게이트**: `validate_kics_disclosure.py` RED=2 (둘 다 사전존재 KR0010 rule2 이미지-OCR 예외, KICS-IMG).
  신규 `19_market`/`36_irr`에서 RED 0 (GREEN 3211, golden 19_market 163 ok / 36_irr 123 ok).
- **미적재(추출 갭, 후속)**: MKT — KR0050 하나손해(세부표 폼 불일치 전분기), KR0051 신한이지, KR0070 에이비엘
  (2025 일부 concat/garbage), KR1098 카카오페이. IRR — 직접형/granular(KR0094 신한·KR0097 하나생명: 순자산
  토큰은 정상이나 aggregate-델타로 위험액 재구성 불가), 총액 추출실패(KR0068 한화·KR0073 교보·KR0051), 원천표
  불일치 경계(KR1010·KR0075). 모두 자기일관성 게이트로 **미저장**(garbage 마스터 유입 차단), 파서 후속 정제 대상.

## 2026-06-09 (b) — inbox 드레인: 동양 이자부리 합계행 오선택 수정 + 코리안리 basis escalate

validator inbox 미결 2건(`status: open`) 처리. 4건 진단(서브에이전트 병렬) → 1 fixed / 1 close / 2 escalate.

- **동양생명 KR0087 2025.4Q 이자부리 (코드수정):** `viz_build_csm_waterfall.py extract_stages`가 이자 후보를
  |값| 최대로 골라 **합계행** "보험서비스결과 및 보험금융손익의 … 총 변동"(CSM −228,193백만)을 순수 금융라인
  "보험금융손익/당기손익"(+108,715백만) 대신 집음. 2025 라벨폼에서만 충돌(2024 A/B/C 레이아웃엔 '보험금융손익'
  문자열 없음). `INTEREST_AGG_MARKERS=("보험서비스결과","총변동","총포괄손익")` 가드 추가(interest 스테이지 한정,
  공백제거 비교). item3 −2139.9→**+1105.0**(2024.4Q +1134와 정합), item4 residual 흡수→마감항등식 유지.
  rebuild→diff = **그 1셀쌍만 변경**, validate_master_tables/continuity SUMMARY byte-identical(신규 finding 0).
- **교보생명 KR0073 2025.3Q 이자부리:** real_negative. 공정가치법 책 보험금융손익 +206,695→−624,435백만(금리효과),
  마감항등식 정확(64380.6+9303.5−5289.6−4383.5−125.5=63885.4=기말). 수정 없음, close.
- **코리안리 KR1000 mis-slice + 2025.2Q FX-in-이자: escalate.** 9046.7↔8031.5는 slice 오선택이 아니라 **basis
  불연속**(2023-24 일반모형노트 8031.5 / 2025+ CER·배당칼럼노트 9046.7). 기초만 8031.5로 강제하면 항등식이 정확히
  1015억(=904,674−803,146백만)만큼 깨짐 — 현 FY2025 movement 전부 9046.7 basis. 직전 진단의 "KR1000-only
  자동수정" 주장은 on-disk diag 동일+산술로 **반증**. 2025.2Q 이자부리 −116.4 = base +30.8 + 환율 −147.2(pattern2
  `find_interest`가 FX 합산, combined 경로는 제외). 동일 2025 CER/pattern2 뿌리 + 삼성생명 공유경로 → basis
  canonical 결정(사람/2nd소스)까지 escalate.

modified: `scripts/viz_build_csm_waterfall.py`, `CSM_waterfall.json`, `data/dart/viz/csm_waterfall_master_{diag,cov}.json`.
inbox: `KR1000_2025.1Q`(answered, route→escalate), `MULTI_2025 signflip`(answered; 동양 fixed·교보 close·코리안리 escalate).

## 2026-06-09 (a) — CSM 워터폴 블록선택 근본수정 (흥국생명 세그먼트 + 코리안리 slice)

inbox-loop 전수 triage(continuity finding 11건)가 짚은 real_error 3건을 추출기 소스에서 해결.
`scripts/build_csm_waterfall_master.py` `pick_group` 2개 원칙적 수정:

- **흥국생명 KR0071 (anchor-defer):** `pick_group("원수일반모형")` 후보게이트가 caption에 '일반모형'
  있는 **손해보험 블록(22326)만** 통과시키고 생명 블록(19137=시리즈 basis)은 배제 + anchor 무시 →
  max-opening으로 손해를 집음. anchor(YTD 기초)가 있으면 anchor-closest 선택 + anchor에서 10%↑
  멀면 None 반환해 anchor-aware `pick_combined_agnostic`로 양보. → FY2023 기초 4분기 19137.5 상수.
- **코리안리 KR1000 (is_prior mvp-guard):** `is_prior`가 canonical 블록(mvp=True, 1,071,519→1,064,090)을
  비-mvp slice 블록(1,064,090→803,146)의 opening과 우연일치로 prior 오판→드롭, slice(803,146=8031.5)를
  집음. is_prior 참조 opening을 **mvp_candidate 블록으로 한정** → canonical 생존, max-opening이 정답 선택.
  → 2023.4Q 기말 10640.9, FY2024 기초 4분기 10640.9.

**검증 게이트(마스터 덮어쓰기 전):** rebuild diag→full diff = **KR0071/KR1000만 변경(26사 불변)**;
continuity validator **11→9**(3건 clear); 타깃값 전부 정답. 실제 master diff도 두 사만(23셀);
`build_csm()`만 호출(PL_breakdown 불변), KR0029 2025.4Q unit-error null 유지.

**노출된 후속(FY2025):** 코리안 FY2024를 고치니 2024.4Q 기말(8031.5=정답) ≠ 2025.1Q 기초(9047)
boundary가 **드러남** — FY2025도 같은 mis-slice인데 **배당칼럼(pattern2) 경로**라 이번 수정 미적용.
회귀 아니라 latent 노출(예전엔 둘 다 9047이라 숨어있었음). `inbox/parser/`에 후속 메시지 투입.
코리안 mis-slice는 FY2023→FY2025, 2개 추출경로(`pick_group`+`pattern2`)에 걸쳐 있음.

## 2026-06-08 (n) — Tier-1 커버리지 감사 (audit_tier1.py) + FS-API 한계 진단

owner: "Tier-1도 많이 뿌셔먹었잖아. 앞으로 Tier-1이나 잘좀 해." → 측정부터. `audit_tier1.py`
신설(전 company-quarter에 `tier1_for` 호출 → HTML fallback / 항목 누락 분류, 캐시 사용 read-only).

- **구조적 진실:** FS-API(`fnlttSinglAcntAll.json`)가 **비상장 보험사 + FY2023 상반기**에 status-013
  (조회 데이터 없음)을 준다. 내 부주의가 아니라 표준 API가 **상장사/사업보고서 제출사 위주**라서다.
  하나생명·메트라이프·라이나·카카오페이손보 등은 감사보고서만 제출(비상장) → FS-API 원천 부재.
- **노출 데이터 기준 Tier-1은 양호:** CORE universe 24곳 중 **23곳이 깨끗한 FS-API**, FS-API가 못 주는
  CORE는 **하나생명 1곳뿐**(비상장). 나머지 HTML fallback은 비-core 소형/디지털사 + FY2023 상반기(비노출).
- **하나생명 item17(투자손익) — 정직히 안 건드림:** 하나 filing은 표가 엉켜 있다(재작성영향표 보험손익
  20,325 vs primary 33,699.9 vs 대손준비금 조정표). `extract_tier1`의 표 선택이 각주표를 집기도 함.
  여기서 투자손익을 강제 추출하면 **basis 오선택으로 새 Tier-1 버그 위험** → 추측 안 함. item17 None 유지.
- **무변경(코드 0줄 수정):** 측정 도구 + 진단만. fragile Tier-1 추측 금지가 핵심.

## 2026-06-08 (m) — PL Tier-2 분해 전수검증(census) + 예실차-미공시 generic closure

owner: "농협만 그럴까? 그래프 안 닫히는 애들 많았어. 전수검증해라." → `check_pl_reconcile.py`
신설(commit, 프로젝트 pl_bridge 식 그대로: 기타원수/기타재보 + dual-form 보험손익 포함).
전사×전분기 분해를 WRONG(present인데 안 맞음=버그)·HOLE(스택 슬라이스 빔)으로 분류.

- **census 초기치:** WRONG=18(대부분 문서화된 FY2023 + KB라이프/악사 잔차), **HOLE=96**.
- **근본원인(조사 에이전트 검증):** 다수 생보사가 원수손익/재보손익 subtotal + CSM상각 + RA는
  공시하나 **예상-vs-실제 청구(예실차) split은 공시 안 함** → item6/7(및 11/12) None → 원수/재보
  막대 안 닫힘. 미래에셋은 공시된 "경험조정" 행이 premium-side뿐이라 부호·크기가 진짜 잔차와
  불일치(쪼개면 조작). 에이비엘은 추가로 당기/전기 leg 버그(별도 처리).
- **owner 결정(2026-06-08): 분리불가 잔차를 예실차로 쪼개지 말고 기타(item7/12)로.**
  `assemble()` generic closure 추가 (commit 7ae7e26): item3 present·item4/5 present·item6 None →
  item6=0, item7=item3−4−5; 재보 동형. **전사 자동** 적용(농협·미래에셋·에이비엘·교보·동양·흥국생명).
- **농협 되돌림:** (l)의 `extract_tier2_nh` item6/11 유도 제거 → 같은 generic 경로로 잔차가
  예실차(item6)→기타(item7) 이동(item7=−266,177, 금액 불변).
- **결과:** census **HOLE 96→45, WRONG 18→14**(새 버그 0). 무회귀: PL gold ALL DIRECT PASS,
  closing 315P/0F, **pl_bridge 14F 불변**(+51 pass/−51 skip), crosscheck 0F(1 minor=에이비엘 leg).
- **남은 actionable(2024.2Q+, 비-legit) 14개:** 동양/케이디비 재보 9·10 누락, 하나생명 원수 side
  전체 누락 + 투자손익(17), 교보라이프플래닛 Tier-2 부재(디지털, 공시 최소). 코리안리 자동차(13)
  누락 11개는 재보험사라 **정상(legit)**. FY2023 홀은 사이트 비노출.

**후속 수정 (same day):**
- **에이비엘 당기/전기 leg 버그 (commit 5a7b548):** 15-agent leg 감사(adversarial 검증) 결과 생보
  14곳 중 **에이비엘 1곳만** 진짜 버그. LIFE_HANDLERS 미등록 → generic `extract_tier2_life`의
  `_life_note_total=max(abs)`가 `[구분|당기|전기]` 2기간 노트에서 전기>당기라 **전기(작년치)** 선택.
  전용 `extract_tier2_abl`로 **당기 명시 선택**(원수 4/5 + 재보 9/10). item4 88,926→82,804,
  item5 12,282→8,346. **crosscheck 1M→0M**(그 minor가 이 버그였음). 나머지 13곳 clean.
- **하나생명 장기손익 (commit 255f8f2):** item4/5/6 추출되는데 item2/3 None. assemble가 item3=
  보험수익−보험서비스비용 유도 시 IS `_is_cost`가 보험수익의 ~9%(mis-pick)라 materiality guard가
  reject → item3 None. `extract_tier2_hana`가 **발행 노트 합계를 `_jang_rev/_jang_cost`로 설정**
  → item3(53,256/28,358)·item2 닫힘. **census HOLE 45→43.**
- **정직히 남긴 잔여 갭:** 동양(2024.x)/케이디비(2025.x) 재보 CSM상각(9)/RA(10) — 출재 섹션 깊이
  박힘 + 분기별 노트 구조 상이(fragile, 재보 sub-slice). 하나 투자손익(17) — Tier-1/FS-API lane.
  교보라이프플래닛 Tier-2 부재 — 디지털 생보 공시 최소(legit 가능). WRONG 14 = FY2023 비노출 +
  KB라이프/악사 sub-1.5% 잔차(문서화됨).

## 2026-06-08 (l) — 농협손해 PL Tier-2 예실차 IFRS17 항등식 유도 (보험손익≈0 재현) [→ (m)에서 기타로 재분류]

owner: "농협손보 보험손익 0원으로 나온다 / PL breakdown 똑바로 안 한 건 니 잘못". FS-API로 보험손익
**-22억(-2,234백만)** 이 회사 실값임 확인(보험영업수익 4,634,635.5 − 비용 4,636,869.7). 문제는 **분해가
닫히지 않음** — item6/11 예실차가 0이라 item4+5+6+9+10+11 ≠ item2(장기손익). 근본: NH는 예상-vs-발생
claim split을 공시하지 않고 **보험수익/보험서비스비용 소계만** 공시.

- **수정 (commit 32c7613):** `extract_tier2_nh`에 IFRS17 항등식으로 experience residual 유도:
  `원수 예실차(6) = (보험수익−보험서비스비용) − 원수CSM상각(4) − 원수RA(5)`, 재보(11) 동형.
  큰 **음(-)의 원수 예실차**(실제 손해가 CSM/보험료에 내재된 예상 초과)가 +CSM상각에도 보험손익≈0을
  만드는 정체. 2024.4Q·2025.4Q 모두 **분해합=장기손익 닫힘 OK**(87,482=87,482 / 175,332=175,332).
- **무회귀:** PL gold **ALL DIRECT PASS**, closing 315P/0F, pl_bridge 2082P/**14F**(불변), crosscheck 0F.
- **정직히 남긴 것:** item13/14(자동차/일반) None 유지 — NH는 종목별이 아니라 **전사 단일 보험손익만** 공시.

## 2026-06-07 (k) — 야간 #2 라운드2: 라이나 CSM 상각 라벨 + PL gold gate GREEN

(j) 이후 owner가 "남은 것 없을 때까지" 추가 지시 → 더 고침:
- **라이나생명 CSM 상각 라벨 (commit 4935afc):** 라이나(KR0074)가 CSM 상각 행을 `제공된 서비스의
  보험계약마진` / `제공한 서비스 반영 인식한 보험계약마진`으로 표기 → STAGE_PATTERNS 미포함 → item5=None
  → closing-identity SKIP. 두 라벨 추가(`보험취득현금흐름의 상각`은 substring 불일치라 자동 제외).
  라이나 상각 −3,973.5/−3,314.4 복구, **closing 302P→303P/0F, SKIP 6→5**, 무회귀.
- **PL gold gate GREEN (commit 9204ee2):** 남은 gold DIRECT fail은 전부 **RA↔예실차 내부 split 관례차**
  (추출 오류 아님 — exact pair-offset으로 경제총액이 골드와 원 단위까지 일치):
  DB손보 2024.2Q item11+12=−82,549 · 한화생명 2025.2Q item5+7=−28,254/item10+12=−7,742 ·
  롯데 2026.1Q item11+12=−3,153. 우리 추출=DART note 충실, 골드=owner 귀속 관례. 선례(한화손보/KB
  CLAIMED)대로 직접추출 primary만 gate, split 잔차는 reference. → `_verify_pl_golds`: **ALL DIRECT PASS.**

**최종 게이트:** closing **303P/0F**/5S · crosscheck **69P/1M/0F** · PL gold **ALL DIRECT PASS** ·
K-ICS RED=2(KR0010 문서화 예외→통과) · NB 5/5 · pl_bridge 2058P/14F(FY2023 비노출 + sub-1.5% 잔차,
deferred-by-design). **deployable.**

**고치지 않고 정직히 남긴 것(불가/저가치):** pl_bridge FY2023(사이트 비노출) · 2024-25 sub-1.5% dual-form
잔차 · 케이디비 2024.1Q spike(반기 테이블 구성차) · 롯데 2023.1Q(IFRS17 transition 분기 CER 표 부재) ·
미래에셋/케이디비 2023.1Q closing SKIP(product-segment/transition) · 메리츠 2023 pl_bridge(FY2023, 미배포) ·
cont 12(IFRS17 기초재작성 gray) · MLG-1/2(owner 결정 필요). 억지 fragile fix·gold 매칭 하드코딩은 안 함.

## 2026-06-07 (j) — CSM 당기/전기 leg-selection 버그 5종 (야간 자율) + 중장기(MLG) feasibility

validator의 `CSM_PLAUSIBILITY` 연속성/복붙 룰이 closing-identity(산술만 검사)가 놓친 **절댓값 오류**
5종을 표면화 → 전부 당기/전기(혹은 합계/세부) 블록 오선택이 근본 원인. 5건 수정 + 커밋:

- **흥국화재 (commit 2edfa2e):** `배당합산`이 **기말=None인 불완전 무배당 블록**을 골라 closing이 유배당
  소계(34억)로 붕괴 → 망가진 4Q 기초가 anchor로 연쇄 오염돼 2025 전분기가 2024 복붙. `pick_group`에
  **기말 있는 완전 블록 우선**(`complete` 필터). 2025.4Q 34→28,047, 복붙·폭락 0. anchor 연쇄로 전분기 해결.
- **케이디비생명 분기 (commit 2edfa2e):** 전기 라벨 `제N(전)기`가 가/나 product enumerator(`나. 제37(전)기`)
  를 달고 나와 `_is_prior_caption` startswith 검사를 통과 → 전기 opening이 anchor 오염 → 2025.Q=2024.Q 복붙.
  `_is_prior_caption`에 `re.search(제\d+\(전\)기)` 추가. 2025.1~3Q 5,854/9,237/9,137 → 9,047/9,154/9,331.
- **메트라이프생명 (commit 2edfa2e):** `별도세그합산`이 **측정요소별 grand-total 블록 + 유/무/변액 세부**를
  같이 합산 → 기초=2×전년말. `_strip_aggregate`(opening≈Σ나머지인 cluster 제거). 2025.4Q 기초 48,134→24,067.
- **케이디비생명 2025.4Q 연차 (commit a924202):** `_double_total_sum`이 grand-total 블록을 picks에 포함해
  psum 2배 → confirm 실패 → `_comparable_min`이 무배당 세그(5,338)를 별도로 오인. `_double_total_sum`에
  `_strip_aggregate` 선적용(grand-total 제외 후 컴포넌트 합). 2025.4Q 5,338→**7,730**. DB생명/미래에셋/한화생명 무회귀.
- **롯데손보 quarterly/annual (commit e5bb9c9):** 롯데는 배당있는/없는이 **별도 CER 표**(삼성화재 등은 한 표
  컬럼그룹) → single-pick이 tiny 배당있는(128억)만 잡거나 `분기말` 마감라벨 미스로 누락. (1) closing
  STAGE_PATTERNS += 당분기말/당반기말/분기말/반기말, (2) 신규 `_pattern2_segsum`+`_pick_per_cluster_to_anchor`:
  당기 배당군 합산(annual=전기 value-continuity drop, quarterly=opening합이 anchor 최근접). disjoint 가드
  (2nd cluster <40% top)로 별도/연결쌍은 미합산 → 무회귀. 2025.4Q 12,828→**24,748.6**(crosscheck amort
  −213,943 = pl 원수CSM상각 +213,943 상쇄), 2026.1Q·2025.3Q 부활. 잔여: 롯데 2023.1Q(early-2023 layout)
  + 2025.2Q/3Q 배당있는(~0.5%, 반기보고서 미분리).

**검증(validate_master_tables):** closing **302P/0F/6S**, crosscheck **69P/1M/0F**(롯데·케이디비 2F→0F),
plausibility **0dup/1spike/12cont**(복붙 6→0; 잔여 spike=케이디비 2024.1Q, cont 12=전부 IFRS17 기초재작성
gray-zone). **CSM 도메인 closing 0F + crosscheck 0F 정합 달성.**

**중장기 목표 feasibility(둘 다 owner 결정/다세션 필요로 판명):**
- **MLG-1 듀레이션갭:** DART 본문(한화생명/삼성생명 주석 50)에 듀레이션갭 *서술* + 만기사다리(16버킷) +
  100bp 금리민감도(손익/OCI)는 있으나 **자산/부채 듀레이션 숫자·갭 자체는 없음**(만기+할인곡선 유도 필요).
  손보(삼성화재/DB)는 sparse. → 100bp 민감도 추출이 구체적 첫 단계, 갭 유도식은 owner 결정.
- **MLG-2 K-ICS 시장위험 분해:** 통합 시장위험액 현황 표 부재. 하위(금리/주식/부동산/외환/자산집중)가 사별·
  위험별 이질 표(금리=충격전후 shock표 → 위험액 유도 필요, 주식=헤더 embed, 부동산=합계행). clean disclosed
  총액 사별 불일치(삼성화재 금리·주식만, 삼성생명 금리만, DB손해 전무). → PL-Tier2급 사별 핸들러 다수 +
  금리위험액 유도규칙 owner 결정 필요. R11(Σ하위=시장위험액)은 금리 확정 후 가능. 정밀 기록 후 defer.

## 2026-06-07 (i) — 한화손해 2025.4Q CSM 신계약 음수 수정 + NB CSM 신선 KIDI 재빌드

NB CSM 배수 빌드 중 사용자가 한화손해 2025.4Q 신계약CSM 음수(−710억)를 지적. 원인 추적:
- **근본 원인:** 2025.4Q **사업보고서** 차이조정표는 부모행("미래 서비스와 관련된 변동")과 자식행
  ("처음/최초 인식한 계약")이 **rowspan 병합으로 컬럼이 행마다 시프트** → 추출기가 부모값(−71,576,507
  = 신계약+가정 net)을 신계약으로 읽음(상각·이자·기초·기말은 정상, closing은 가정이 잔차로 흡수해 닫힘).
  분기보고서(Q2/Q3)는 별도 신계약 행이 있어 +4,510/+7,350 정상. 추가로 detail 차이조정 블록(처음 인식한
  계약 행 보유)이 `_reins_header`에 재보험으로 오분류돼 스킵되던 것도 원인.
- **수정(`build_csm_waterfall_master._annual_newbiz_from_detail`):** 신계약이 음수(불가능)면 standalone
  "처음/최초 인식한 계약" detail행에서 **진짜 값 직접 추출** — 연속 csm_cols run마다 LAST 칼럼(= [PV, RA,
  보험계약마진] 레이아웃의 trailing 보험계약마진; 신계약 행은 앞 칼럼이 PV/RA라 sum 불가)을 골라 배당그룹
  합산, max-positive(=당기 원수 발행). 한화손해 2025.4Q **신계약 −710 → 10,178억**(무배당 1,029,070,395 +
  유배당 −11,274,344), 가정 −4,862.7(잔차), closing 보존. 당분기 신계약 2,827억(정상), 배수 11.56(=Q3
  11.58과 일치 → 검증). `_fix_annual_newbiz`(YTD 단조성 carry-forward)는 detail 추출 실패 시 fallback.
- **전수 감사:** 전 회사×4Q 당분기 신계약을 Q1-3 평균과 대조(미분리/과소추출 탐지) + YTD 단조성 → **다른
  의심 0건.** 병합셀 오류는 한화손해 2025.4Q 단독.
- **NB CSM 배수 마스터(g 정정):** stale `nb_premium_wolnap.json`(2025-05-30, 월평균) 대신 **사용자가
  재크롤한 `data/kidi/premium_summary.json`(2026-06-06, denominator_eok=월납+기타초회 일시납제외,
  KR_code 키, YTD 직접, 2026.1Q 포함)** 으로 빌더 교체. 월납 **305/305(100%)**, 2026.1Q 19개사, 비현실
  배수(>40·음수분자) null+flag. 한화손해 2025.4Q 배수 −0.81(null)→**11.56**(detail 추출 후).
- **결과:** closing 299P/0F 무회귀, NB flag 6→5(남은 = 신한이지·카카오페이 디지털 PAA-only인데 CSM 큼,
  BNP 소형 — CSM_waterfall 별도 점검 대상).

## 2026-06-01 → 2026-06-07 — CSM/PL 파싱 push (compressed, prior session)

> 1줄 요약(헤더에 핵심 결과 포함). 전문(어느 함수·어느 라인)은 git log/blame.

- 2026-06-07 (h) — 흥국화재 _single 핸들러: 재보험 PAA 장기 누락 수정
- 2026-06-07 (g) — 신계약CSM배수 루트 마스터 빌드 (연누계 + 당분기)
- 2026-06-07 (f) — FY2023 H1 Tier-1 item17(투자손익) net 보정: 생보 영업이익 닫힘
- 2026-06-07 (e) — DB손해·KB손해 PL: 별도/연결 노트 오선택 (병렬 진단 → 통합)
- 2026-06-07 (d) — 삼성화재 2026.1Q PL: component 노트 레그별 별도/연결 기준 불일치
- 2026-06-07 (c) — 한화손보 2025 PL 13/14: 연결 표 오선택 → 별도 표 (deferred 버그 해소)
- 2026-06-07 (b) — CSM crosscheck 잔여 2건: KB라이프 이중합산 버그 + 코리안리 룰 스코프
- 2026-06-07 — 마스터 검증 정합 + root 마스터 + 당분기 + CSM 정본 승격
- 2026-06-06 (c) — Tier-2 잔여갭 마무리 (답지 0 코드수정 + 한화/롯데 답지)
- 2026-06-06 (b) — Tier-2 전사 대확장 (병렬 7에이전트 분석 → 직렬 통합 12배치)
- 2026-06-06 — 구형식(pre-2025.2Q) 손보 핸들러 + 코리안리/흥국 OLD + 병렬에이전트 레시피 (SESSION HANDOFF)
- 2026-06-05 — 삼성화재(KR0008) PL Tier-2 답지 통합 + 범용 손보 컴포넌트 핸들러 + 별도 전환
- 2026-06-05 — DB손해(KR0011) PL Tier-2 답지 통합 + 핸들러 재작성
- 2026-06-05 (g) — Tier-1 전사 DART 표준 FS API 전환 (HTML 손익계산서 파싱 졸업)
- 2026-06-04 — PL 전사 전분기(2023.1Q~2026.1Q) sweep + Tier-1 일반화 (broken 44→0)
- 2026-06-04 (b) — 롯데 PL 답지 통합 + 재작성-영향표 제외 (PL 골드 5장)
- 2026-06-04 (c) — 상장사 분기 확장: IFRS4↔17 전환표 col + 헤더기반 재작성 제외
- 2026-06-04 (d) — 한화생명 분기 답지 → 반기순이익 + YTD(누적) col 일반수정 (분기 전사 교정)
- 2026-06-04 (e) — KB 손보 CSM 분기 답지 → 통합 net표 인식 일반수정 (KB 4/13→12/13)
- 2026-06-04 (f) — KB PL 분기 분해 (CSM상각 단위), KB-전용 격리 핸들러
- 2026-06-03 (b) — PL breakdown 24항목 추출기 신규 + 전사·전분기 sweep
- 2026-06-03 (c) — PL Tier-2 전사 확장 (답지 없이 self-check 검증) + Tier-1 item1 4건 수정
- 2026-06-03 (d) — CSM 골드 7장 받아 BROKEN/large-wobble 해소 (게이트 86/90)
- 2026-06-03 (e) — 당기/전기 stacked 블록 일반 수정 (미래에셋 전분기 평탄화)
- 2026-06-03 (f) — 분리 sub-portfolio 합산 일반화 (교보·푸본·신한라이프 코드스코프 제거)
- 2026-06-03 — CSM 2024 생보 + 분기검출 전면 안정화 (gold 8/8), 회귀 점검
- 2026-06-02 (c) — CSM 분기 FY-anchor + 코드베이스 아카이빙
- 2026-06-02 (b) — CSM 생보 별도 픽스 (6사 gold 6/6) + PL 24항목 + basis 노트
- 2026-06-02 — CSM waterfall 배당합산 일반화 (사용자 3-gold 검증)
- 2026-06-01 (e) — History 빌더 13Q 재빌드 + 음수-NB 가드 (DB 부호반전 해소)
- 2026-06-01 (d) — FY2025 V7 cohort 마이그레이션 → check 7/7
- 2026-06-01 (c) — 롯데 FY2025 NB CSM = 412,168 (reconciliation_lrc override)
- 2026-06-01 (b) — 소계 이중계상 fix + 롯데 NB source (구성요소별 차이조정)
- 2026-06-01 — CSM waterfall: 별도·당기 블록 disambiguation (2026-05-31 trade-off 해소 → Option B)

---

## Archive (pre-2026-06)

> 1줄 요약. 전문은 git log/blame. 재발 gotcha는 프롬프트/도메인 doc에.

- 2026-05-31 — NB CSM widespread fix: 처음 인식 / 전환방법별 표 단일셀 1순위 path.
- 2026-05-31 — F17 Tier2 LOB 9/11사 확장 + IR cross-check 3사(메리츠 clean / 삼성화재·DB 재보험 누락 구조적).
- 2026-05-30 (b) — F17 Tier2 LOB 방법론 수정 (FY2024·삼성화재도 분해 있음).
- 2026-05-30 — F17 손보 당기순이익 분해 Tier1 10사 + Tier2 1사(현대); `build_net_income_breakdown.py`.
- 2026-05-30 — IR factsheet 수집 + 손보 disclosed/derived NB CSM 배수 9사 (`build_ir_disclosed_multiples.py`).
- 2026-05-29 (5건, parser fixes) — `<TE>` 데이터셀 미파싱 root-cause 수정(한화 13Q·교보·삼성화재·현대·케이디비·코리안리 복구) · `find_csm_leaf_cols` 6행 multi-level 헤더 fallback · 삼성생명/미래에셋 상품군 분리공시 합산+소계 이중계상 제거(FY 삼성 13.08조/미래 2.08조/동양 2.54조) · Panel 5 sensitivity rowspan+header-aware(한화/교보/케이디비/DB생명) · CSM 시계열 prior-period decontamination+per-quarter NB+한화 2023.4Q continuity tiebreak. 28사 회귀 0.
- 2026-05-25 — IFRS17 historical 13Q promote(294→293 ok, `<TE>` fix 후 258 ok) · B5 K-ICS sensitivity appendix wording + `--all-periods`(49 tables/12 quarters).
- 2026-05-25 mid-session — NB CSM ratio prototype(cp949 fallback, Samsung 금융 layout) · IFRS17 B3 row tagging(2956 rows/930 hits) · B5 K-ICS v1(FY2025_Q4 10/23) · CSM waterfall STAGE_PATTERNS 확장(23/23) · Unit-hint mismatch auto-detect(23 insurer-quarter, 56 post 보정).
- 2026-05-25 K-ICS RED reduction (parser) — Rule 2 KakaoPay/MetLife reversed labels·item4 reconcile · 8_life item35 multi-line unit hint · Shinhan Life rule6 분산효과 alias drop · Rule 5 item22=0 추론 · Samsung Life 2023.1Q/3Q bullet sections · DB손해 8_life first 위험액 block.
- 2026-05-24 KICS parser progression — RED@177 → KR0097 Hana(18→2) → missing-data reparse+item27/28(311→217) → RED pass2(419→311) → REPARSE-Q4(30/38 ok) → split-table+row scope(KR0005 golden).
- 2026-05-24 IFRS17 parser bootstrap — CSM 추출기 강화+37사 일괄(23/37 ok) · MVP A3/A4/B1/B5 skim+23-co batch · A1 gap 3사 fix · A1 23사 batch · `값_적용후`+KR0076 보조지표 · sensitivity heatmap load fix.
- 2026-04-25 ~ 04-28 Pipeline foundation — Docling 파이프라인(PDF→MD inbox) · NONLIFE/LIFE 협회 파서 1차 · FY2025_Q4 PDF→MD→kics_data.json · kics_disclosure.json 직접 채우기(749 rows) · 과거 분기 배치 검증(27/28).
