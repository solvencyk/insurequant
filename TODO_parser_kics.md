# Insurequant Parser TODO — K-ICS lane (Stage 2)

> 갱신 2026-10-12 · 프롬프트 `docs/agents/claude-agent-parser.md` + 도메인 `docs/domains/claude-agent-kics.md` · 이력 `docs/changelog_parser_kics.md`
> 2026-10-07 정리 전 전문은 `docs/todo_archive_parser_kics.md` 맨 위에 있다. IFRS17 레인은 `TODO_parser_ifrs17.md`(별도 세션).

## Status (최신 3개)

- **2026-10-12 (32회차) 「최신 공시 직전 컬럼 우선」 적용(티켓 `20261012T2200Z`) — 드라이런 채택 후보 26블록 중 확실 기준 통과 16블록 65칸 적용(전 33 · 적용후 미러 22 · 파생 27·28 10) · 10블록 보류 · 예외 2건 해제**: 칸 단위 + 옛값 가드 + 임시 파일 교체로 `kics_disclosure.json` 을 바꿨고 HEAD 대비 바뀐 칸이 계획과 정확히 일치한다(행 추가·삭제 0, `git diff --numstat` 65/65). 보류 = 후속 공시 두 곳이 그 칸에서 어긋난 9블록 + `recalc_kics_derived` 가 되돌리는 1블록(ABL생명 2024.3Q 항목 22: 인쇄 1 은 확실하나 항목 22 영 규칙이 되돌림), 나머지 62블록은 드라이런 범주 그대로(`held_blocks.csv` 72행). 5칸은 재작성이 아니라 마스터가 자기 공시 인쇄와 달랐던 칸(악사 2025.1Q · 2026.1Q, 흥국생명 2024.4Q, AIA 2026.1Q, 롯데 2023.4Q 활자 오류).
  게이트: K-ICS RED 56 → 54(롯데 2025.1Q · NH농협 2024.3Q 항목 13 이 닫혀 해소, 새 RED 0, blocking 0, exit 0), 데이터계약 RED 0 · YELLOW 152 → 164, `validate_master_tables --no-build` 출력 전후 동일, xlsx `K-ICS공시` 65칸만 동기화(드리프트 0). 영속화 = 재작성 장부 `kics_restatement_ledger.json` 29칸 as_restated + 결정 기록 · `_TIER2_ISSUER_INCONSISTENT` 22 → 20(원장 `CONTRADICTED`) · 사본 재빌드 시뮬레이션: `fill_*` 재실행이 되돌리는 재작성 28칸 + 활자 오류 1칸을 게이트가 RED 29 로 잡음, `recalc` 영향 0.
  남은 것: validation(골든 `test_kics_rules_golden` `--update` 이유 「31 finding 이동: RED 56→54 · YELLOW 1936→1934 · GREEN +4」 · 입력지문 INPUTS_MOVED ×4(+3바이트) · 시험 4건: `test_tier2_issuer_inconsistent_exemption` 3(등재 수 22→20 · 롯데 2025.1Q 대상 교체 · 갈래 박제 대상 소멸) + `test_rule_coverage_manifest` 재작성 census 10→39) · publishing(`public_exports`) · owner(보류 72블록). 근거 `data/_derived/kics_latest_prior_apply_20261012/`(`applied_blocks.csv` · `held_blocks.csv` · `plans/`). 커밋 = 이 문서와 같은 커밋.
- **2026-10-12 (31회차) 「최신 공시 직전 컬럼 우선」 원칙 드라이런(티켓 `20261012T1900Z`) — 읽기 전용 · 마스터 · 등재부 · 골든 · xlsx · HTML 변경 0**: 예외 전수 185건(등재부 항목 행 192)을 ⓐ 6 · ⓑ 43 · ⓒ 64 · ⓓ 48 · ⓔ 24 로 분류했다. 등재부 선언만으로는 ⓐ 가 0건이었고 열 간 실측으로 tier2 박제 6건(롯데 2023.1Q · 2025.1Q, NH농협 2024.3Q, 코리안리 2024.2Q · 3Q · 4Q)이 ⓐ 로 올랐다. 롯데 2025.1Q · NH농협 2024.3Q 는 이후 공시 둘이 재분류항목을 정정해 인쇄해 룰이 닫힌다(예외 해소), 코리안리 3분기는 최신 열이 기본/보완자본만 고쳐 다른 룰을 깬다(둘 다 실패).
  (회사 × 분기) 587블록 중 열 간 차이 88(±1억 반올림 32): 결정표(오너 2026-10-12) 최신 채택 42(진짜 재작성 40 · 예외 해소 2) · 현행 유지 31 · 둘 다 실패 5 · 룰 사각 10, 티켓 범주 채택 후보 26블록 87칸 · 완전성 부족 45 · 룰 사각 8 · gold 충돌 1 · 현행 유지 7+1. 「직전 컬럼에 검증 단위가 다 있다」 실측: 홀수분기 최신 열 84.1% · 짝수분기 최신 열(2분기 뒤 공시의 직전 반기 열) 72.4%, 바로 다음 공시의 직전 열만 보면 짝수분기 0/247(간이공시라 세부 표 없음).
  남은 것: owner(최신 우선 정책 · ±1억 임계 · 박제 2건 해제 · 코리안리 3분기 · 빈 버킷 5건) · 적용은 별도 티켓(계획 `plans/*.json` 88개, 해제 후 게이트). 근거 `data/_derived/kics_latest_prior_precedence_dryrun_20261012/`(`summary.md`). 커밋 = 이 문서와 같은 커밋.
- **2026-10-12 (30회차) 신종·후순위 분류 2차(티켓 `20261012T2000Z`) — 집계 대상 124건(신종 43 · 후순위 81) 전부 분류(미분류 0) · 마스터·등재부 변경 0**: 149행을 제외(owner) 17(이력 7 · 잔액 0 5 · 2026-06-30 목록에서 빠진 후순위 5) · 항목 6 대사용 기타 8(전환우선주 4 · 우선주 3 · DB생명 포함분 1; 아이엠라이프 전환우선주 포함)로 갈라내고 후순위 81건은 전부 tier2 기본값으로 두었다(예외 후보 4건은 검색에서 반대 근거 없음, 악사 JPY 는 공개 자료 자체가 없음). 신종 43건 = legacy_tfi 21 · tier1 5 · tier2 17 이며 1차 ⓑ 6건이 전부 ⓐ 로 올랐다: DB손보 5건 tier1 · 하나손보 2건(2024-05 · 2026-06-29 1,000억 6.20%) tier2 · 하나생명 제1회 tier2.
  DB 발췌의 원문 후보는 IB토마토 2026-07-09(1차의 W2)로 내용만 일치(문장 그대로는 미확인), 하나손보 「스텝업은 없으나 배당가능이익 부재」 문장은 못 찾아 owner 제공 발췌, 하나생명은 아시아경제 2023-04-05(W11)와 같은 서술이다. 등재부는 작업 중 publishing(`ef62969`)이 owner 확정으로 갱신해 HEAD 와 type 불일치 0(티켓 시점 기준 6건) · `issuer_type` 병기 2건(교보 2024-11 · 하나생명)만 남는다. DB 제3회(2026-02-11)는 건별 직접 근거 없이 owner 지시에 기대며 반대 방향 신호(W5 · W14 · 표 검정)는 한도 초과 재분류와 구분되지 않는다.
  남은 것: 증권신고서·신평 PDF 원문 대조(WebSearch 로는 불가; W16 · W18 은 요약 기반) · 2026-06-30 이후 신규 발행(하나생명 2026-09-15 1,500억 · 교보 2026-09)은 2026.3Q 라운드. 근거 `data/_derived/capital_securities_classification_census_20261012/`(`census_summary_r2.txt` · `census_securities_final.csv` 43행 · `r2_selfcheck.py` 20/20). 커밋 = 이 문서와 같은 커밋.

## 열린 일

- [ ] **「최신 공시 직전 컬럼 우선」 원칙 후속(31·32회차, 티켓 `20261012T1900Z` · `20261012T2200Z`)**: 적용분 16블록 · 예외 2건 해제는 32회차에 끝났다. 남은 것:
  - ① owner - 보류 72블록 중 후속 공시가 그 칸에서 흔들리는 9블록(하나손해 2023.1Q · 신한이지 2023.3Q · 삼성생명 2023.2Q · 2024.3Q · 푸본현대 2025.2Q · 메트라이프 2024.3Q · KB라이프 2024.2Q · 2024.4Q · 처브라이프 2025.2Q) 채택 여부 · 구성행 자리 바꿈 룰 사각 8블록 · 빈 버킷 채움 5건(스위스리 2023.3Q · 하노버 2023.4Q · 2024.1Q · 2025.3Q · RGA 2023.2Q) · 소급재작성 장부 `_policy` 기본값 전환 여부
  - ② validation - 코리안리 2024.2Q~4Q 박제 사유 재검토 · 골든 `--update` · 입력지문 · 시험 4건 정리(위 Status)
  - ③ parser - `recalc_kics_derived.py` 항목 22 영 규칙(`항목14 == 항목15 이고 항목23 == 0`)이 인쇄된 1 을 되돌려 ABL생명 2024.3Q 항목 22 = 1 적용을 보류했다. 규칙을 「반올림 노이즈일 때만」으로 좁히면 풀린다. 산출 `data/_derived/kics_latest_prior_apply_20261012/`(`applied_blocks.csv` · `held_blocks.csv` · `plans/` · `img/`) · 드라이런 `data/_derived/kics_latest_prior_precedence_dryrun_20261012/`.
- [ ] **신종·후순위 분류 2차 후속(30회차, 티켓 `20261012T2000Z`)**:
  - ① 원문 대조 — DB손보 제3회(2026-02-11 4,420억)·제5회(300억)는 건별 직접 근거가 없고(owner 지시), 증권신고서(W16)·한신평 보고서(W18)·DB 발췌 원문 후보(W2)는 검색 요약 기준이라 PDF/본문을 열어 확인(WebSearch 로는 불가)
  - ② 등재부 `issuer_type=tier1` 로 병기된 2건(교보 2024-11-12 · 하나생명 제1회)의 발행사 처리 근거 문서(경영공시 해설·증권신고서) - 우리 type=tier2 와 어긋나는 유일 케이스
  - ③ 2026-06-30 이후 신규 발행(하나생명 2026-09-15 1,500억 보완자본 · 교보생명 2026-09 3,000~5,000억 스텝업)은 2026.3Q 라운드에서 목록에 올림. 산출 `data/_derived/capital_securities_classification_census_20261012/`(`r2_*` · `*_r2.*` · `census_securities_final.csv`).
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
