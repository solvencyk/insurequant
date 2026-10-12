# Insurequant Parser TODO — K-ICS lane (Stage 2)

> 갱신 2026-10-12 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-kics.md` · 이력 `docs/changelog_parser_kics.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_parser_kics.md` 맨 위에 있다. IFRS17 레인은 `TODO_parser_ifrs17.md`(별도 세션).

## Status (최신 3개)

- **2026-10-12 (30회차) 신종·후순위 분류 2차(티켓 `20261012T2000Z`) — 집계 대상 124건(신종 43 · 후순위 81) 전부 분류(미분류 0) · 마스터·등재부 변경 0**: 149행을 제외(owner) 17(이력 7 · 잔액 0 5 · 2026-06-30 목록에서 빠진 후순위 5) · 항목 6 대사용 기타 8(전환우선주 4 · 우선주 3 · DB생명 포함분 1; 아이엠라이프 전환우선주 포함)로 갈라내고 후순위 81건은 전부 tier2 기본값으로 두었다(예외 후보 4건은 검색에서 반대 근거 없음, 악사 JPY 는 공개 자료 자체가 없음). 신종 43건 = legacy_tfi 21 · tier1 5 · tier2 17 이며 1차 ⓑ 6건이 전부 ⓐ 로 올랐다: DB손보 5건 tier1 · 하나손보 2건(2024-05 · 2026-06-29 1,000억 6.20%) tier2 · 하나생명 제1회 tier2.
  DB 발췌의 원문 후보는 IB토마토 2026-07-09(1차의 W2)로 내용만 일치(문장 그대로는 미확인), 하나손보 「스텝업은 없으나 배당가능이익 부재」 문장은 못 찾아 owner 제공 발췌, 하나생명은 아시아경제 2023-04-05(W11)와 같은 서술이다. 등재부는 작업 중 publishing(`ef62969`)이 owner 확정으로 갱신해 HEAD 와 type 불일치 0(티켓 시점 기준 6건) · `issuer_type` 병기 2건(교보 2024-11 · 하나생명)만 남는다. DB 제3회(2026-02-11)는 건별 직접 근거 없이 owner 지시에 기대며 반대 방향 신호(W5 · W14 · 표 검정)는 한도 초과 재분류와 구분되지 않는다.
  남은 것: 증권신고서·신평 PDF 원문 대조(WebSearch 로는 불가; W16 · W18 은 요약 기반) · 2026-06-30 이후 신규 발행(하나생명 2026-09-15 1,500억 · 교보 2026-09)은 2026.3Q 라운드. 근거 `data/_derived/capital_securities_classification_census_20261012/`(`census_summary_r2.txt` · `census_securities_final.csv` 43행 · `r2_selfcheck.py` 20/20). 커밋 = 이 문서와 같은 커밋.
- **2026-10-12 (29회차) 신종자본증권·후순위채 분류 전수조사(티켓 `20261012T1230Z`) — 마스터 변경 0 · 149행 표 · 등재부와 다른 증권 8건(등재부는 안 고침)**: 47사의 채권 목록 133건(신종 46 · 후순위 87, 27사) + 목록 밖 16건(우선주 · 상환 이력 · 자회사 보유분)을 발행일 · 콜 · 만기 · 쿠폰 · 잔액 · 등재부 type · 근거 표(`census_securities.csv`)로 만들어 확정도 ⓐ 126 · ⓑ 16 · ⓒ 7 로 매겼다(신종 채권 ⓐ 40 · ⓑ 6 · ⓒ 0 / 후순위 ⓐ 83 · ⓒ 4). 등재부 18사 중 신종 채권이 있는 17사에서 14사는 채권 전부 ⓐ(제외 DB손보 · 하나손보 · 하나생명). 아이엠라이프 「미특정 1,517억」 = 2022 발행 전환우선주 1,517.18억(FY2022 감사보고서 · 항목 53 합 2,465.98 정확 일치)으로 특정.
  등재부와 다른 8건(`census_mismatch.csv`): DB손보 2026 세 건(발행사 K-ICS 표 정량 검정 c9 가 보완자본형 쪽 ⓑ — 등재부 tier1 이면 소진율 151.6%, tier2 면 약 75%) · 교보 2024-11-12 6,000억(발행조건 = 스텝업 = 보완자본형 ⓐ 인데 발행사 표는 기본자본형으로 처리: 상충) · 푸본 · 농협생명 · 코리안리 2건(등재부 미확정 tier1 → 사업보고서 스텝업 문구로 tier2 ⓐ).
  남은 것: owner(등재부 8건 결정 · 교보 2024-11 발행사 처리 확인) · 증권신고서/사모 계약서 원문이 생기면 ⓑ 6건 승급 · 후순위 예외 후보 4건(ⓒ). 근거 `data/_derived/capital_securities_classification_census_20261012/`(재현 순서 = `census_summary.txt` 끝). 커밋 = 이 문서와 같은 커밋.
- **2026-10-12 (28회차) 퍼시픽·악사·뮌헨 후속(티켓 `20261012T1030Z`) — 마스터 +16행 · 4칸 정정 · 뮌헨 +3행(owner 승인 뒤 51 도출)**: 퍼시픽 KR1107 2025.3Q·2026.2Q 항목 47~54 16행을 인쇄된 0 그대로 적재(p22·p25 「해당사항 없음」 서식, 미적용사 확인: 전환 사이드카 10분기 TFI·TAC·TIR·TER·TIRR 전부 X · FSS 붙임-1 밖) · 악사 KR0049 2024.3Q 4칸(항목 3 전·후 2325 · 4 전 5215 · 27후 286.5) = 2024.4Q 공시 전기 열(p36·p39) 채택.
  뮌헨 KR1101 2026.2Q 는 p17 이 50·52(2,716.42)만 인쇄하고 51 은 대시도 아닌 공란이라 처음엔 보류(50·52 만 = RED 2)했으나 owner 승인(10-12 「1 승인」)으로 50·52 + 51 = 0(항등식 52 = 50 + 51 도출, 원문 공란)을 적재(`provenance_derived_cells.json`). 마이브라운 무변경. HEAD 대비 바뀐 칸·새 키 = 계획 정확히 일치(4칸 + 16행, 뮌헨 +3행), K-ICS 게이트 RED 56 · blocking 0 · exit 0 불변(YELLOW 1935 → 1936, 새 RED 0).
  남은 것 없음(git log 확인): validation 골든 갱신 완료(`470e146` · `b8b949a`), publishing xlsx `K-ICS공시` +19행 · 4칸 · public_exports 재동기화 완료(`538cbe7` · `fda6752`). 커밋 `acd351a`(퍼시픽 · 악사) · `33635d1`(뮌헨). 근거 `data/_derived/kics_followups_20261012/`(`proof_vs_head.txt` · `sim_*.txt` · 계획 `plans/`).

## 열린 일

- [ ] **신종·후순위 분류 2차 후속(30회차, 티켓 `20261012T2000Z`)**: ① 원문 대조 — DB손보 제3회(2026-02-11 4,420억)·제5회(300억)는 건별 직접 근거가 없고(owner 지시), 증권신고서(W16)·한신평 보고서(W18)·DB 발췌 원문 후보(W2)는 검색 요약 기준이라 PDF/본문을 열어 확인(WebSearch 로는 불가) ② 등재부 `issuer_type=tier1` 로 병기된 2건(교보 2024-11-12 · 하나생명 제1회)의 발행사 처리 근거 문서(경영공시 해설·증권신고서) - 우리 type=tier2 와 어긋나는 유일 케이스 ③ 2026-06-30 이후 신규 발행(하나생명 2026-09-15 1,500억 보완자본 · 교보생명 2026-09 3,000~5,000억 스텝업)은 2026.3Q 라운드에서 목록에 올림. 산출 `data/_derived/capital_securities_classification_census_20261012/`(`r2_*` · `*_r2.*` · `census_securities_final.csv`).
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
