# Insurequant Parser TODO — K-ICS lane (Stage 2)

> 갱신 2026-10-10 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-kics.md` · 이력 `docs/changelog_parser_kics.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_parser_kics.md` 맨 위에 있다. IFRS17 레인은 `TODO_parser_ifrs17.md`(별도 세션).

## Status (최신 3개)

- **2026-10-10 (21회차) 재보사 스윕 단계 9 — 마스터 +164행(퍼시픽 2023.3Q·2023.4Q·2024.3Q, 스위스리 2023.4Q 완성본), 금리민감도 근거 25칸**: sha `90cbc2c6…` → `4f2eb284…`, 시뮬레이션 = 실측 0 차이,
  기존 39사 25,522행 HEAD 와 동일. 퍼시픽 2023.4Q 하위위험 29~46 까지 채워 새 RED 3건 중 2건 해소(내 변경분 RED 57 → 58·blocking 0 → 1 = 2023.3Q `8_life_census`, validation 등재 반영 시 57·0), 데이터계약 RED 34 → 4(K-ICS 0).
  커밋 없음. 남은 것: owner — 스위스리 2023.2Q(새 RED 0)·2023.3Q(새 RED 2) 전기 칸 적재 여부 · 후속 발주 3건(아래) · xlsx 동기화(publishing). 근거 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_9.md`.
- **2026-10-10 (20회차) 재보사 스윕 단계 7(R1 완결) — 마스터 값 75칸 변경 + 49행 신설, 사이드카 18칸, 스테이징 15건**: 스위스리·제네럴·스코리 R1 14칸 반영 · 항등식 되돌림 6건 · 제네럴 정밀값 17칸 ·
  하노버 2023.3Q 비전 적재 · 결측 행 1 · owner 승인 P7·P8·P10 · 게이트 RED 71→65(blocking 35→29, 신규 RED 0) · 기존 39사 25,522행 불변. 미반영: 스위스리 2024.4Q 14칸·퍼시픽 2023.3Q/4Q(새 RED → owner 재결정).
  커밋 없음(오케스트레이터). 남은 것: 예외 등재 29건 · 골든 2종 재생성(validation) · xlsx 동기화(publishing). 근거·칸별 전후 = `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_7.md`.
- **2026-10-06 (19회차) AIA생명 2024.4Q 항목46 단위 100배 정정** — `값`·`값_적용후` 3607646 → 36076.46(원문 PDF p25 이미지 대조).
  `market_subrisk_recovered_gold.json` 동반 정정, 듀레이션갭 audit 9 → 8. `73eb328`, 라이브 `420cdc3`.

## 열린 일

- [ ] **재보사 스윕 owner 결정 — 스위스리 2023.2Q·2023.3Q 를 새 완성본의 전기 열로 채울지**(runlog 9 §7): 2023.2Q 는 항목 1~46 전부 인쇄·새 RED 0, 2023.3Q 는 새 RED 2(룰 4 — 발행사 3Q 열이 운영위험액을 안 더함 · `8_life_census`).
  채우면 validation 의 census 면제 등재를 풀어야 한다. (스위스리 2024.4Q 14칸·퍼시픽 2023.3Q·4Q 는 2026-10-10 owner 결정으로 종결.)
- [ ] **재보사 후속 발주 3건**(runlog 9 §8): ① 퍼시픽 금리민감도 2024.4Q·2025.2Q 미적재(MD 에 표 있음, 12행) ② KR1107 항목 27 정밀값 4칸(2024.4Q 252→251.76 · 2025.1Q 258→257.51 · 2025.2Q 271→271.39 · 2025.3Q 157→156.63, 결정 2)
  ③ 같은 (회사, 분기)에 raw PDF·MD 가 둘일 때 도구가 옛 파일을 고르는 문제(`disclosure_pdfs()[0]` — 스위스리 2023.4Q 60쪽 대 85쪽).
- [ ] **금리민감도 phase 구멍 31칸** — `inbox/parser/20260921T1400Z` §A. 분기별 raw 각주로 전==후를 확인한 뒤 미러하거나, 원천부재면 파일·페이지 근거를 회신.
- [ ] **item13/메리츠 티켓 잔여** — `inbox/parser/20260919T1400Z`: (2) 메리츠화재 2026.2Q item2/3 적용후가 적용전 복사(원문 p18 54,329.57 / 91,102.49억)
  → 고친 뒤 56번째 item13 셀 재측정, (3) 코리안리 2023.4Q·2024.2Q 기준선 확인, (4) 못 잰 29버킷.
- [ ] **2026.3Q 라운드 파싱** — 루트 `TODO.md`. item27/28 은 `recalc_kics_derived.py` 로 산출하고, 경과조치 18사는 `값_적용후` 까지 채운다.

## 휴면 (2026-06~07 개설, 재개 전에 게이트로 다시 잰다)

TRANS-18 게이트 마진 오탐 5셀(validation 마진 로직) · TRANS-AFTER-9 R5/R6/mmult 3사(예별·흥국화재·흥국생명, ③표 또는 36-40 후 추출 필요) ·
GOLD-CHAIN backfill 스크립트 3종을 rebuild 체인(`fill_*` → `apply_user_kics_gold` → `recalc`)에 편입 · MARKET-P2 잔여(구조적 SKIP 분류 ·
IRR 직접형 schema · 레이아웃 미스) · F12 `market_risk_breakdown` schema · IFRS-NORMALIZE(`row_aliases.yaml`) · REFACTOR-3 slice2(PARKED, 착수조건 미발생).

2026-10-07 실측으로 닫은 것: DEDUP(중복키 94 → **0**) · gold 3종 git 추적 확인 · FY2026_Q1 MD 39개 존재 · GOLD-SCAN(2026-08-30 실측 결측 0, 대상 셀 미특정).
