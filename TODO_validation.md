# Insurequant Validation TODO (Stage 3)

> 갱신 2026-10-12 (26차 골든 갱신 + AIG R3 등재) · 프롬프트 `docs/agents/claude-agent-validation.md` · 이력 `docs/changelog_validation.md`
> 2026-10-07 정리 전 전문(V1~V19 블록 포함)은 `docs/todo_archive_validation.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-12 (26차) 골든 갱신 + AIG R3 박제 등재 (티켓 `20261012T1400Z`)** — 이동 원인은 parser-kics `acd351a` 하나뿐(직전 마스터로 돌리면 K-ICS 골든 5키 전부 일치, 입력지문 4종은 `kics_disclosure.json` 한 파일 +5,195바이트). `--update`: `kics_rules_golden`(YELLOW 1,935→1,936 · GREEN 13,684→13,703 · SKIP 3,345→3,325 · RED 56 불변) · `builder_input_fingerprints`(4종).
  무이동 확인(실행): dividend · post_transition · master_tables · viz 2종 · PL(`RUN_PL_GOLDEN=1`, 186초) · 17BS(419초) · deploy_assets 12 · push_gate_wiring 65 · prepush_scope 65 · golden_input_fingerprint 23. AIG KR0029 2024.4Q `R3_CROSS_CHECK` 10배 규칙: `R3_PINNED_EXEMPTIONS`(값 박제 item8 31.0억·item20 291,767.640554백만) + 읽는 쪽 `check_r3` + 변이시험 11건(`tests/test_ilp_r3_pinned_exemption.py`, 훅 묶음 편입). 포트폴리오 검증기 RED 2→1(남은 1 = KR1102 2026.1Q `R2_CENSUS`, owner 결정 대기·미등재).
- **2026-10-12 (25차) owner 승인 등재 — 재보사 인쇄된 0 7칸 · 서울보증 PL 2칸 · 마이브라운 거짓 양성 1칸 (티켓 `20261012T1010Z`)** — `HOLE-PL` 2->0(`pl_src_absent:3ok`), 데이터계약 RED 2->2(손해율 xlsx 동기화 대기 = publishing 몫, 신규 0) · K-ICS 게이트 exit 0 RED 56 불변(finding 0 추가·0 삭제).
  읽는 쪽 확인: 7칸은 복원을 가정한 시뮬레이션에서 RED 0·`OWNER_CONFIRMED` 7(대조군 등재부 비움=RED 7) · 마이브라운은 5칸 적재 가정에서 새 RED 0(대조군 RED 2) · 서울보증은 사이트 판 census 가 매니페스트 자리(새 사유 `SITE_ROLLED_OFF`). 변이시험 4파일 85건 통과(신규 2파일 `test_pl_source_absent_site_rolled_off`·`test_tier2_stale_false_positive_exemption` 훅 묶음 편입)·selftest 102/102, 골든 `--update` 1종(master_tables: `coverage_hole 2PL->0PL`·`pl_src_absent 1ok->3ok` 두 토큰뿐).
  등재 안 한 것: 뮌헨 2026.2Q 50·52(원문에 **있음**, p17 -> parser-kics) · CSM 워터폴 대 ILP(대조하는 게이트 룰이 없어 등재할 줄이 0 -> 룰 설계가 선행). 남은 것: 7칸 복원(parser-ifrs17 `--restore7 --apply`) · 마이브라운 5칸 적재(parser-kics) · 오케스트레이터 티켓 종결.
- **2026-10-12 재보사 PL 계보 허용 + 마감 골든 3종 `--update` — 데이터계약 RED 102→0(전부 `CONCEPT_MIXED_DISCLOSURE_INTO_DART`, 신규 0)** — `PL_DISCLOSURE_REINSURER_LINEAGE`(how=`disclosure_summary_pl_reinsurer`, 항목 17·20·21)을 「DART 계보 PL 셀이 없는 회사」(데이터 조건 · 8곳 KR1101~KR1108)·income_statement·쪽·**항목별** 인쇄값이 있을 때만 §3d 에서 뺀다(102셀/299값).
  변이시험 pytest 14건 + selftest 92→102(Q11 가족)·훅 묶음 편입. 골든 `--update`: master_tables(재보사 적재 반영)·17BS(+49칸, 빌더 산출=마스터 sha)·입력지문 / PL·viz 2종·kics·post_transition·dividend 는 무이동. 훅 대체 `prepush_check.py --full` = **gate-clear exit 0**(데이터계약 RED 0 · K-ICS clear · 도메인 7종 pass · 지문 pass · JS clear · inbox 위반 0 · 오프라인 795 통과 1 skip). 남은 것: owner 결정표(티켓 §5).

## 열린 일

- [ ] **최종 라운드 후속(22차)** — 소유자 결정 15건(런로그 Step 5) · 법정준비금 `run_components`(R-RSV-4/12) 데이터계약 배선(현재 단독 RED 10, parser-ifrs17 선행) ·
  CSM 워터폴 대 ILP CSM 잔액 교차 게이트 `CSM_WATERFALL_VS_ILP_CSM_STOCK`(제안만 -- owner 는 기준 차이 등재를 승인했으나 **룰이 없어 등재할 줄이 0**; 새 룰 설계가 선행, 287칸 중 6칸+롯데 군집, `data/_derived/validation_registrations_20261012/csm_wf_vs_ilp_basis_diff_cells.md`) · 연속성 게이트 밴드 0.5%가 숨기는 롯데 2023.4Q −105억.
- [ ] **`CSM_WATERFALL_VS_ILP_CSM_STOCK` 룰 설계 범위(설계 선행, Opus 몫)** — 입력: `CSM_waterfall.json` 기말 CSM(항목 6) 대 `insurance_liability_portfolio.json` 항목 3+6(억원), 공유 (회사,분기) 287칸. 허용오차 후보 `max(1억, 0.5%)`(262칸 1억 이내·281칸 통과·6칸 초과). 예외 형태: 재작성 칸(`ilp_restated_comparative.json`·워터폴 재작성 기록)은 기준 명시 YELLOW, 계약이전(예별 2025.4Q)은 칸 박제, 값 박제(AIG R3 `R3_PINNED_EXEMPTIONS` 형태)와 INERT/DRIFT RED 포함. 롯데손해 2023.4Q~2024.3Q 군집·2024.3Q 잔차 −23 은 설명 안 되므로 등재로 덮지 말고 칸별 분류. 칸 목록 `data/_derived/validation_registrations_20261012/csm_wf_vs_ilp_basis_diff_cells.md`.
- [ ] **재보사 push 차단 최종 확인** — 단계 10 에서 훅의 게이트를 하나씩 다 쟀다(전부 exit 0, 런로그 `_12.md` §5). 남은 것은 오케스트레이터의
  `prepush_check.py --full` 1회 실측. 교훈: 단계 종결 전 도메인 게이트까지 훅 전체를 잰다(단계 8 은 데이터계약만 재서 3·4 를 놓쳤다).
- [ ] **기존 키 집합 등재부를 박제 장치로 옮길지** — `RS1_EXCEPTIONS`(예별 2024.4Q)·`RS2_EXCEPTIONS`·`RS5_EXCEPTIONS`(17)는 근거 재확인 없이 영원히 빠진다.
  단계 10 장치(`rs_pinned_exemptions`)로 옮기면 매 실행 재검산된다. 등재 변경이라 owner 결정 사항(이번 범위 밖, 손대지 않음).

- [ ] **유지율 VP 재검증** — parser 가 `inbox/parser/20261007T1001Z__validation__MULTI_2023.2Q-2026.2Q__persistency_validation_findings.md`
  를 answered 하면 RED-1(KR0004 2026.2Q 단위)·YELLOW-2/4/6/8 재확인, MI 보강 티켓(KR0051·KR1000)·downloader KR0150 도 같이. 재현 스크립트는 보고서 머리 경로.
- [ ] **금리위험 순자산가치 등식 게이트** — `자산총계 − 부채총계 == item41~46`(또는 형제 시나리오 배율 plausibility).
  AIA 2024.4Q 항목46 100배가 `max(base−steep,0)` 뒤에 숨어 `36_irr` 가 구조적으로 못 봤고 듀레이션갭 역검산만 잡았다(2026-10-06).
- [ ] **UH-26 배포 페이지 런타임 스모크(헤드리스)** — 배선 전에 타당성부터: CDN 4종 로컬 캐시 SRI 일치, 브라우저 없는 클론에서
  "미검사" 를 verdict 에 찍기, 4페이지 로드 시간. 근거 `inbox/_resolved/20260921T0630Z`.
- [ ] **적용후 `36_irr` 19건 미평가**(`POST_SCENARIO_ABSENT`, 적용후 41~46 결측) — 백필 대상인지 판정.
- [ ] **`AFTER_IDENT_ISSUER_INCONSISTENT` 가 `_exemption_registries()` 에 없다** — 근거 원장 검사를 안 받는다(parser 관측 2026-09-21).
- [ ] **매니페스트 잔여** — `tests/test_rule_coverage_manifest.py` 의 `coverage_holes(pl, …)` 가 resolver 없이 불린다 · `zleg_exc` 미인쇄(12차 잔여).
- [ ] **RS6 known holes 정리** — parser 가 `inbox/parser/20260921T1400Z` §A 를 채우면 `RS6_KNOWN_HOLES`·매니페스트 `RATE_SENS_*` 갱신.
- [ ] **공개 다운로드 잔여 노출 4건** — publishing 이 고치기로 하면 jargon 룰 패턴 확장(`TODO_publishing.md`).

## 휴면 (2026-06~08 개설, 3개월 넘게 진척 없음 — 재개 전에 게이트로 다시 잰다)

V1 DART↔IR 교차검증(IR 파싱 대기) · V2 삼성화재 IR 연간 벤치마크 · V3 시장위험 적재 단위 확인 · V4 QoQ 레지스트리 잔여
(precedence·누적 변환) · V5 누적 항목 등록 · V7 롯데 NB override·한화손해 stale carryover · V8 미래에셋 CSM상각·롯데 생명장기 결측 ·
V9 저배수 4사·메트라이프 영업이익 · V12 CSM 민감도 경영공시 기준 재추출. 원문은 archive.

## 규칙

- documented exception 은 owner 만 등재한다 — 등재부 `docs/kics_gate_exceptions.md` + 코드 레지스트리 + `data/_gold/kics_exemption_provenance.json`.
  서브에이전트가 자체 waiver 를 쓰지 않는다.
- loopback max 5회, 넘으면 `escalate`. RED 패키지에 `suspected_source` 를 적는다. 룰셋 정본 `docs/agents/kics-json-validation-rules.md`.
