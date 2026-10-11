# Insurequant Parser TODO — K-ICS lane (Stage 2)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-kics.md` · 이력 `docs/changelog_parser_kics.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_parser_kics.md` 맨 위에 있다. IFRS17 레인은 `TODO_parser_ifrs17.md`(별도 세션).

## Status (최신 3개)

- **2026-10-11 (23회차) 재보사 스윕 단계 13 — 미뤘던 6건 처리**: IRR 잔액 기존 6셀 열 뒤바뀜 정정(+듀레이션갭 6행) · 스위스리 2023.2Q 적재(마스터 +46행) · 금리민감도·IRR 추출기가 수작업 정정을 스스로 재현(재보사 168행·IRR 301셀 = 마스터 동일, 기존 39사 불변 증명) · 이중 raw PDF 공통 헬퍼(15개 도구) · census 40칸 적재(6,048칸 중 빈칸 1,595 전부 사유 분류). 퍼시픽 금리민감도·정밀값은 이미 적재돼 있었음.
  커밋 없음. K-ICS 게이트 RED 57·blocking 0 불변, 단 exit 2 = `CENSUS_EXEMPTION_INERT KR1102 2023.2Q` 1건(티켓이 예고). 남은 것: validation(등재 해제 · 룰 골든 `--update` · 마이브라운 소액 오탐) · publishing(xlsx `K-ICS공시`·`금리듀레이션갭` + public_exports 3종) · owner(전기 열 적재 후보 4버킷).
  근거 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_13.md`.
- **2026-10-10 (22회차) 재보사 금리민감도 RED 40 → 5 · 듀레이션 갭 재보사 46칸 적재**: 금리민감도 +24행 · 값 정정 28행(단위 19 · 하노버 후 0 행 미러 9), 근거 +3셀, IRR 잔액 +46셀 → 듀레이션 갭 +46행(`DURGAP_CENSUS_MISSING` 46 → 0). 기존 39사 전 파일 HEAD 와 동일, K-ICS 게이트 RED 57·blocking 0 불변.
  커밋 없음. 남은 것: validation 등재 5건(제네럴 2026.2Q +100bp RS1 2 · 마이브라운 RS5 3) · publishing xlsx 금리민감도·금리듀레이션갭 재동기화 · 기존 6셀 IRR 열 뒤바뀜(카카오페이손보 5 · 하나손보 2025.2Q) 적용 결정.
  근거 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_11.md`.
- **2026-10-10 (21회차) 재보사 스윕 단계 9 — 마스터 +164행(퍼시픽 2023.3Q·2023.4Q·2024.3Q, 스위스리 2023.4Q 완성본), 금리민감도 근거 25칸**: sha `90cbc2c6…` → `4f2eb284…`, 시뮬레이션 = 실측 0 차이,
  기존 39사 25,522행 HEAD 와 동일. 퍼시픽 2023.4Q 하위위험 29~46 까지 채워 새 RED 3건 중 2건 해소(내 변경분 RED 57 → 58·blocking 0 → 1 = 2023.3Q `8_life_census`, validation 등재 반영 시 57·0), 데이터계약 RED 34 → 4(K-ICS 0).
  커밋 없음. 남은 것: owner — 스위스리 2023.2Q(새 RED 0)·2023.3Q(새 RED 2) 전기 칸 적재 여부 · 후속 발주 3건(아래) · xlsx 동기화(publishing). 근거 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_9.md`.

## 열린 일

- [ ] **재보사 단계 13 후속(runlog 13 §7)**: ① validation — `_CENSUS_SOURCE_ABSENT` 의 KR1102 2023.2Q 등재(+ 원장 항목) 해제(풀면 K-ICS 게이트 exit 0 복귀) · `tests/fixtures/kics_rules_golden.json` `--update`(이유: 단계 13 데이터 +86행; 시작 마스터에서는 골든 sha 일치) ·
  마이브라운 2025.3Q `47_tier2_census` `TIER2_LIMIT_STALE` 소액 오탐(룰 조정 또는 등재가 있으면 47·48·49·53·54 = 0 5칸을 넣을 수 있음) · 뮌헨 2026.2Q 공란 표(50·52 만 싣기 = `TFI_TIER_PARTIAL_ROWS` RED 2, 51 을 0 으로 도출하는 것은 owner 판단) ·
  퍼시픽 2025.3Q·2026.2Q 47~54 16칸(원문이 「해당사항 없음」 서식에 전 칸 0 인쇄, 머리글 지급여력금액은 2,043·1,781억 — 0 으로 싣는 시뮬은 새 RED 0 · 새 YELLOW 4 · 해소 YELLOW 4, 이웃 8분기는 50·52 = 머리글 값이라 서식 채움으로 보고 빈 칸 유지, 적재 여부는 owner)
  ② publishing — xlsx `K-ICS공시`(+86행)·`금리듀레이션갭`(+1행·6행 값 변경) 재동기화 + `public_exports` `기본자본소진율`·`보완자본소진율`·`자본비율전망`(KR1102 2023.2Q) 재생성(금리민감도 xlsx·export 재동기화는 단계 11 에서 이어짐)
  ③ owner — 후속 문서 전기 열로 채울 수 있는 빈 버킷 결정: 스위스리 2023.3Q(새 RED 2) · 하노버 2023.4Q·2024.1Q · 알지에이 2023.2Q ④ parser-ifrs17 — 자체 raw glob 이 두 판이 있는 스위스리 2023.4Q 에서 옛 판을 읽을 위험(`latest_disclosure_pdfs()` 로 교체; `test_disclosure_raw_pdf_wiring` 7건 실패의 정체).
- [ ] **금리민감도 phase 구멍 31칸** — `inbox/parser/20260921T1400Z` §A. 분기별 raw 각주로 전==후를 확인한 뒤 미러하거나, 원천부재면 파일·페이지 근거를 회신. (단계 13: 하나손보·신한이지·삼성생명·동양 MD 에 비적용 명문이 있다. 추출기 `NON_APPLIER_POST_MIRROR` 등재부로 같은 방식으로 풀 수 있다 — owner 승인 + 분기별 원문 확인 뒤.)
- [ ] **item13/메리츠 티켓 잔여** — `inbox/parser/20260919T1400Z`: (2) 메리츠화재 2026.2Q item2/3 적용후가 적용전 복사(원문 p18 54,329.57 / 91,102.49억)
  → 고친 뒤 56번째 item13 셀 재측정, (3) 코리안리 2023.4Q·2024.2Q 기준선 확인, (4) 못 잰 29버킷.
- [ ] **2026.3Q 라운드 파싱** — 루트 `TODO.md`. item27/28 은 `recalc_kics_derived.py` 로 산출하고, 경과조치 18사는 `값_적용후` 까지 채운다.

## 휴면 (2026-06~07 개설, 재개 전에 게이트로 다시 잰다)

TRANS-18 게이트 마진 오탐 5셀(validation 마진 로직) · TRANS-AFTER-9 R5/R6/mmult 3사(예별·흥국화재·흥국생명, ③표 또는 36-40 후 추출 필요) ·
GOLD-CHAIN backfill 스크립트 3종을 rebuild 체인(`fill_*` → `apply_user_kics_gold` → `recalc`)에 편입 · MARKET-P2 잔여(구조적 SKIP 분류 ·
IRR 직접형 schema · 레이아웃 미스) · F12 `market_risk_breakdown` schema · IFRS-NORMALIZE(`row_aliases.yaml`) · REFACTOR-3 slice2(PARKED, 착수조건 미발생).

2026-10-07 실측으로 닫은 것: DEDUP(중복키 94 → **0**) · gold 3종 git 추적 확인 · FY2026_Q1 MD 39개 존재 · GOLD-SCAN(2026-08-30 실측 결측 0, 대상 셀 미특정).
