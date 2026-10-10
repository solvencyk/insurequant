# Insurequant Parser TODO — K-ICS lane (Stage 2)

> 갱신 2026-10-10 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-kics.md` · 이력 `docs/changelog_parser_kics.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_parser_kics.md` 맨 위에 있다. IFRS17 레인은 `TODO_parser_ifrs17.md`(별도 세션).

## Status (최신 3개)

- **2026-10-10 (22회차) 재보사 금리민감도 RED 40 → 5 · 듀레이션 갭 재보사 46칸 적재**: 금리민감도 +24행 · 값 정정 28행(단위 19 · 하노버 후 0 행 미러 9), 근거 +3셀, IRR 잔액 +46셀 → 듀레이션 갭 +46행(`DURGAP_CENSUS_MISSING` 46 → 0). 기존 39사 전 파일 HEAD 와 동일, K-ICS 게이트 RED 57·blocking 0 불변.
  커밋 없음. 남은 것: validation 등재 5건(제네럴 2026.2Q +100bp RS1 2 · 마이브라운 RS5 3) · publishing xlsx 금리민감도·금리듀레이션갭 재동기화 · 기존 6셀 IRR 열 뒤바뀜(카카오페이손보 5 · 하나손보 2025.2Q) 적용 결정.
  근거 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_11.md`.
- **2026-10-10 (21회차) 재보사 스윕 단계 9 — 마스터 +164행(퍼시픽 2023.3Q·2023.4Q·2024.3Q, 스위스리 2023.4Q 완성본), 금리민감도 근거 25칸**: sha `90cbc2c6…` → `4f2eb284…`, 시뮬레이션 = 실측 0 차이,
  기존 39사 25,522행 HEAD 와 동일. 퍼시픽 2023.4Q 하위위험 29~46 까지 채워 새 RED 3건 중 2건 해소(내 변경분 RED 57 → 58·blocking 0 → 1 = 2023.3Q `8_life_census`, validation 등재 반영 시 57·0), 데이터계약 RED 34 → 4(K-ICS 0).
  커밋 없음. 남은 것: owner — 스위스리 2023.2Q(새 RED 0)·2023.3Q(새 RED 2) 전기 칸 적재 여부 · 후속 발주 3건(아래) · xlsx 동기화(publishing). 근거 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_9.md`.
- **2026-10-10 (20회차) 재보사 스윕 단계 7(R1 완결) — 마스터 값 75칸 변경 + 49행 신설, 사이드카 18칸, 스테이징 15건**: 스위스리·제네럴·스코리 R1 14칸 반영 · 항등식 되돌림 6건 · 제네럴 정밀값 17칸 ·
  하노버 2023.3Q 비전 적재 · 결측 행 1 · owner 승인 P7·P8·P10 · 게이트 RED 71→65(blocking 35→29, 신규 RED 0) · 기존 39사 25,522행 불변. 미반영: 스위스리 2024.4Q 14칸·퍼시픽 2023.3Q/4Q(새 RED → owner 재결정).
  커밋 없음(오케스트레이터). 남은 것: 예외 등재 29건 · 골든 2종 재생성(validation) · xlsx 동기화(publishing). 근거·칸별 전후 = `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_7.md`.

## 열린 일

- [ ] **재보사 스윕 owner 결정 — 스위스리 2023.2Q·2023.3Q 를 새 완성본의 전기 열로 채울지**(runlog 9 §7): 2023.2Q 는 항목 1~46 전부 인쇄·새 RED 0, 2023.3Q 는 새 RED 2(룰 4 — 발행사 3Q 열이 운영위험액을 안 더함 · `8_life_census`).
  채우면 validation 의 census 면제 등재를 풀어야 한다. (스위스리 2024.4Q 14칸·퍼시픽 2023.3Q·4Q 는 2026-10-10 owner 결정으로 종결.)
- [ ] **재보사 후속 발주 2건**(runlog 9 §8; 퍼시픽 금리민감도 2024.4Q·2025.2Q 는 단계 11 에서 적재 완료): ① KR1107 항목 27 정밀값 4칸(2024.4Q 252→251.76 · 2025.1Q 258→257.51 · 2025.2Q 271→271.39 · 2025.3Q 157→156.63, 결정 2)
  ② 같은 (회사, 분기)에 raw PDF·MD 가 둘일 때 도구가 옛 파일을 고르는 문제(`disclosure_pdfs()[0]` — 스위스리 2023.4Q 60쪽 대 85쪽).
- [ ] **재보사 금리민감도·듀레이션 갭 마무리(단계 11 후)**: validation 등재 후보 5건 — 제네럴 2026.2Q +100bp RS1 2(발행사 표 자기모순 856/270=317.04 대 인쇄 319.78) · 마이브라운 RS5 3(원문 「해당사항 없음」 p17·p50·p34) ·
  publishing: master xlsx `금리민감도`(재보사 168행)·`금리듀레이션갭`(+46행) 재동기화 + `public_exports`. 근거 runlog 11 §1.4·§1.5·§6.
- [ ] **IRR 잔액 기존 6셀 시나리오 열 뒤바뀜(실데이터 오류, 게이트 통과 중)** — 카카오페이손보 2023.2Q·2023.4Q·2024.4Q·2025.2Q·2026.2Q · 하나손보 2025.2Q(`kics_irr_balance.json` → `kics_duration_gap.json` 6행, 하나손보 자산듀레이션 2.25 → 4.78 등).
  위치 대응(`stage11/run_irr_extract11.py --all --canon`)으로 고친다 — 기존 39사 변경이라 오케스트레이터 결정 대기. 도구 보강 후보(`extract_kics_irr_balance.py` 위치 대응 우선 · `extract_kics_rate_sensitivity.py` 단위 환산·잘린 라벨·쪽 넘김·비적용사 후 블록)는 runlog 11 §7-2.
- [ ] **금리민감도 phase 구멍 31칸** — `inbox/parser/20260921T1400Z` §A. 분기별 raw 각주로 전==후를 확인한 뒤 미러하거나, 원천부재면 파일·페이지 근거를 회신.
- [ ] **item13/메리츠 티켓 잔여** — `inbox/parser/20260919T1400Z`: (2) 메리츠화재 2026.2Q item2/3 적용후가 적용전 복사(원문 p18 54,329.57 / 91,102.49억)
  → 고친 뒤 56번째 item13 셀 재측정, (3) 코리안리 2023.4Q·2024.2Q 기준선 확인, (4) 못 잰 29버킷.
- [ ] **2026.3Q 라운드 파싱** — 루트 `TODO.md`. item27/28 은 `recalc_kics_derived.py` 로 산출하고, 경과조치 18사는 `값_적용후` 까지 채운다.

## 휴면 (2026-06~07 개설, 재개 전에 게이트로 다시 잰다)

TRANS-18 게이트 마진 오탐 5셀(validation 마진 로직) · TRANS-AFTER-9 R5/R6/mmult 3사(예별·흥국화재·흥국생명, ③표 또는 36-40 후 추출 필요) ·
GOLD-CHAIN backfill 스크립트 3종을 rebuild 체인(`fill_*` → `apply_user_kics_gold` → `recalc`)에 편입 · MARKET-P2 잔여(구조적 SKIP 분류 ·
IRR 직접형 schema · 레이아웃 미스) · F12 `market_risk_breakdown` schema · IFRS-NORMALIZE(`row_aliases.yaml`) · REFACTOR-3 slice2(PARKED, 착수조건 미발생).

2026-10-07 실측으로 닫은 것: DEDUP(중복키 94 → **0**) · gold 3종 git 추적 확인 · FY2026_Q1 MD 39개 존재 · GOLD-SCAN(2026-08-30 실측 결측 0, 대상 셀 미특정).
