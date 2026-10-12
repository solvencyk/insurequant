# Insurequant Parser TODO — K-ICS lane (Stage 2)

> 갱신 2026-10-12 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-kics.md` · 이력 `docs/changelog_parser_kics.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_parser_kics.md` 맨 위에 있다. IFRS17 레인은 `TODO_parser_ifrs17.md`(별도 세션).

## Status (최신 3개)

- **2026-10-12 (29회차) 신종자본증권·후순위채 분류 전수조사(티켓 `20261012T1230Z`) — 마스터 변경 0 · 149행 표 · 등재부와 다른 증권 8건(등재부는 안 고침)**: 47사의 채권 목록 133건(신종 46 · 후순위 87, 27사) + 목록 밖 16건(우선주 · 상환 이력 · 자회사 보유분)을 발행일 · 콜 · 만기 · 쿠폰 · 잔액 · 등재부 type · 근거 표(`census_securities.csv`)로 만들어 확정도 ⓐ 126 · ⓑ 16 · ⓒ 7 로 매겼다(신종 채권 ⓐ 40 · ⓑ 6 · ⓒ 0 / 후순위 ⓐ 83 · ⓒ 4). 등재부 18사 중 신종 채권이 있는 17사에서 14사는 채권 전부 ⓐ(제외 DB손보 · 하나손보 · 하나생명). 아이엠라이프 「미특정 1,517억」 = 2022 발행 전환우선주 1,517.18억(FY2022 감사보고서 · 항목 53 합 2,465.98 정확 일치)으로 특정.
  등재부와 다른 8건(`census_mismatch.csv`): DB손보 2026 세 건(발행사 K-ICS 표 정량 검정 c9 가 보완자본형 쪽 ⓑ — 등재부 tier1 이면 소진율 151.6%, tier2 면 약 75%) · 교보 2024-11-12 6,000억(발행조건 = 스텝업 = 보완자본형 ⓐ 인데 발행사 표는 기본자본형으로 처리: 상충) · 푸본 · 농협생명 · 코리안리 2건(등재부 미확정 tier1 → 사업보고서 스텝업 문구로 tier2 ⓐ).
  남은 것: owner(등재부 8건 결정 · 교보 2024-11 발행사 처리 확인) · 증권신고서/사모 계약서 원문이 생기면 ⓑ 6건 승급 · 후순위 예외 후보 4건(ⓒ). 근거 `data/_derived/capital_securities_classification_census_20261012/`(재현 순서 = `census_summary.txt` 끝). 커밋 = 이 문서와 같은 커밋.
- **2026-10-12 (28회차) 퍼시픽·악사·뮌헨 후속(티켓 `20261012T1030Z`) — 마스터 +16행 · 4칸 정정 · 뮌헨 +3행(owner 승인 뒤 51 도출)**: 퍼시픽 KR1107 2025.3Q·2026.2Q 항목 47~54 16행을 인쇄된 0 그대로 적재(p22·p25 「해당사항 없음」 서식, 미적용사 확인: 전환 사이드카 10분기 TFI·TAC·TIR·TER·TIRR 전부 X · FSS 붙임-1 밖) · 악사 KR0049 2024.3Q 4칸(항목 3 전·후 2325 · 4 전 5215 · 27후 286.5) = 2024.4Q 공시 전기 열(p36·p39) 채택.
  뮌헨 KR1101 2026.2Q 는 p17 이 50·52(2,716.42)만 인쇄하고 51 은 대시도 아닌 공란이라 처음엔 보류(50·52 만 = RED 2)했으나 owner 승인(10-12 「1 승인」)으로 50·52 + 51 = 0(항등식 52 = 50 + 51 도출, 원문 공란)을 적재(`provenance_derived_cells.json`). 마이브라운 무변경. HEAD 대비 바뀐 칸·새 키 = 계획 정확히 일치(4칸 + 16행, 뮌헨 +3행), K-ICS 게이트 RED 56 · blocking 0 · exit 0 불변(YELLOW 1935 → 1936, 새 RED 0).
  남은 것 없음(git log 확인): validation 골든 갱신 완료(`470e146` · `b8b949a`), publishing xlsx `K-ICS공시` +19행 · 4칸 · public_exports 재동기화 완료(`538cbe7` · `fda6752`). 커밋 `acd351a`(퍼시픽 · 악사) · `33635d1`(뮌헨). 근거 `data/_derived/kics_followups_20261012/`(`proof_vs_head.txt` · `sim_*.txt` · 계획 `plans/`).
- **2026-10-12 (27회차) 재보사 자본성증권 소진율 재확인(티켓 `20261012T0130Z`) — 8사 전부 0 이 원문 근거로 맞다 · 마스터 보정 0칸**: 8×14×7(항목 6·13·47·48·49·53·54) 784칸 전수 분류(일치 635 · 원공시 유지 결정 2 · 부재 147, 미분류 0), 감사 K-ICS 12건·IFRS 감사·MD 106개 대조. 스위스리 보완자본 4,274억 = 전액 해약환급금 부족분 초과분(Ⅲ.3, 자본증권 아님, 영업기금은 보통주), 알지에이 47 = 5,499 는 발행사 서식 오기(raw p18 확인).
  `kics_disclosure.json` == HEAD(변경 0), docling 0회, 커밋 없음. 남은 것: owner/publishing(스위스리 분자 0 확정 규칙 · 「발행 없음」 표시 · 보류 20칸·버킷 14칸) — 산식 제안은 런로그 §7. 근거 `data/disclosure/_meta/reinsurer_capital_securities_recheck_runlog_20261012.md`(사본 `data/_derived/reinsurer_capital_recheck_20261012/`).

## 열린 일

- [ ] **신종·후순위 분류 전수조사 후속(29회차, 티켓 `20261012T1230Z`)**: ① owner — 등재부와 다른 8건(DB손보 2026 세 건 · 교보 2024-11 · 푸본 · 농협생명 · 코리안리 2건) 결정; 교보 2024-11 은 발행조건(스텝업)과 발행사 처리가 상충, DB손보는 tier2 로 바뀌면 소진율 151.6% → 약 75% ② 증권신고서/사모 계약서 원문이 생기면 ⓑ 6건(DB손보 제2~5회 · 하나손보 제1회 · 하나생명) ⓐ 승급 ③ 후순위 예외 후보 4건(KDB생명 보증부 · 악사 JPY · 흥국화재 · 아이엠라이프) 판정. 산출 `data/_derived/capital_securities_classification_census_20261012/`(`census_mismatch.csv` · `census_securities.csv`).
- [ ] **사이트 신판 16칸 후속(runlog `kics_newer_editions_apply_runlog_20261011.md` §8)**: ① validation — 교보 2026.1Q 재작성 연쇄(`kics_restatement_ledger.json` `_adoption_cascades` 19_market)·후 박제 `AFTER_IDENT_ISSUER_INCONSISTENT` 해제 · 골든 `test_kics_rules_golden`·`test_post_transition_golden`·입력지문 `--update`(이유: 사이트 신판 5칸 정정) · KB손보 텍스트층 사이드카·KICS-IMG 완화·비전 원장 검토(신판은 텍스트층) ·
  ② publishing — xlsx `K-ICS공시`(+98칸)·`금리민감도`(62칸)·`금리듀레이션갭`(+8칸) 재동기화 + public_exports ③ parser — (완료 26회차: 신판 MD 5개 변환 · 판 선택 등재부 · `fill_*` 재현 증명) 교보 2026.1Q 완결(A5)을 되돌릴 때는 `unapply_newer.py --pkgs A5 --apply`.
- [ ] **신판 3건 후속(runlog `kics_editions_runlog_20261011.md` §6)**: ① validation — 악사 2024.3Q 부재 박제 해제(`_POST_PARENT_SOURCE_ABSENT_CELLS` · 원장 `kics_exemption_provenance.json` · `docs/kics_gate_exceptions.md` 악사 절; 게이트가 `EXEMPTION_ABSENCE_PIN_VALUE_PRESENT` review 로 알림) · 골든 `test_kics_rules_golden`(이유: 단계 13 +86행·이번 +17행/+9칸)·`test_post_transition_golden`(이유: 신판 MD 추가로 555→556 company-quarter, 7,123→7,144칸; MD 를 치우면 통과) `--update` ·
  ② publishing — xlsx `K-ICS공시` 재동기화(데이터계약 RED `MASTER_XLSX_ROW_MISSING` 103행·`MASTER_XLSX_DRIFT` 9칸) ③ owner — (악사 보류 4칸은 28회차에 2024.4Q 공시 전기 열로 채택 완료) 하나 2025.4Q 판 선택 확인 ④ 헬퍼 `latest_disclosure_pdfs` 가 기존 39사 두 판 쌍을 못 가림 → 판 채택 등재부 결정(`edition_choice.json` 이 기록) ⑤ parser — `fill_post_transition_adjust_items.py` `_SKIP` 의 낡은 `KR0049 2024.3Q` 제거.
- [ ] **재보사 단계 13 후속(runlog 13 §7)**: ① validation — `_CENSUS_SOURCE_ABSENT` 의 KR1102 2023.2Q 등재(+ 원장 항목) 해제(풀면 K-ICS 게이트 exit 0 복귀) · `tests/fixtures/kics_rules_golden.json` `--update`(이유: 단계 13 데이터 +86행; 시작 마스터에서는 골든 sha 일치) ·
  마이브라운 2025.3Q `47_tier2_census` `TIER2_LIMIT_STALE` 소액 오탐(룰 조정 또는 등재가 있으면 47·48·49·53·54 = 0 5칸을 넣을 수 있음) · 뮌헨 2026.2Q 공란 표(28회차: 50·52 인쇄 · 51 공란 → owner 승인(10-12)으로 50·52 + 51 = 0 도출 3행 적재 완료, RED 0) ·
  퍼시픽 2025.3Q·2026.2Q 47~54 16칸(**28회차에 인쇄된 0 대로 적재 완료**: 새 RED 0 · 새 YELLOW 4(`48_tier2_limit` 정보) · 해소 YELLOW 4)
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
