# Insurequant Validation TODO (Stage 3)

> 갱신 2026-10-13 (29차 소진율·전망 재측정 + 콜일 규칙 정정 확인 + 28차 K-ICS 최신 공시 직전 컬럼 적용 독립 검수) · 프롬프트 `docs/agents/claude-agent-validation.md` · 이력 `docs/changelog_validation.md`
> 2026-10-07 정리 전 전문(V1~V19 블록 포함)은 `docs/todo_archive_validation.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-13 (29차) 소진율·전망 재측정 (티켓 `20261012T2040Z`, 대상 HEAD `6fd00720` -> 후속 확인 `20a700a9`, 읽기 전용 — 마스터·HTML·게이트 코드 무수정)** — 새 규칙(기발행 차감 = 원장 2022-12-31 이전 잔액, 콜 경과 제외)으로 보완자본 소진율 47사 독립 재계산 **47/47 일치** · 기본자본 47/47(결속 갈래 없는 33사 한도 10%, 하나생명 238.2 · 교보 70.1 · DB손보 151.6 불변) · 전망 7사 손계산 35점 차이 0(총자본·기본자본 경로 이전 판과 동일, 행 변경은 KR0050 `confidence` 뿐) · 타임라인·공개 시트 4종 불일치 0 · 화면 47사 x 1280/375 불일치 0(예별·롯데 노트 거짓 개선 제거, 툴팁 잘림 0, 공유 이미지 15사 정상).
  불일치 1건(원장 `past_call_outstanding` 플래그가 행 `as_of` 기준이라 콜 경과 3건이 차감에 남음)은 **해소**: publishing `7e6e55d0`·`20a700a9`(첫 콜일 <= 분자 기준일)를 독립 재측정으로 확인 - 47/47 일치, 메리츠 30.8→37.5 · 아이엠라이프 56.9→70.4 · KB라이프 0.0→0.8, 그 밖 변동 0(44사 불변), 기본자본·전망·타임라인·원장·`K-ICS.html` 바이트 동일, 화면 47사 x 1280/375 불일치 0, 티켓 `20261013T0205Z` resolved(`_resolved/`). 재현물 `data/_derived/capsec_audit_20261012/`(`h1h_delta_vs_previous_20a700a9.txt`·`e11_public_sheet_delta_20a700a9.txt`).
  남은 것: 공유 감사 티켓 `20261012T2040Z` 종결(오케스트레이터 몫) · owner 결정 잔여 5건(아래 열린 일).
- **2026-10-13 (28차) K-ICS 「최신 공시 직전 컬럼」 적용 65칸 독립 검수 + 골든 정리 (티켓 `20261013T0010Z`, 커밋 `74a415bf` 대상)** — 원본 PDF 직접 재판독: primary 33칸 33/33 일치(10쪽은 240dpi 렌더링 육안), 미러 22칸·파생 10칸 재계산 일치, 마스터 diff = 정확히 65칸(레코드 30,011 불변). 보류 10블록 전부 사유 타당.
  게이트: K-ICS exit 0 RED 56→54(풀린 KR0003 2025.1Q·KR0032 2024.3Q 다리 RED 2건, 새 RED 0, 이동 31 finding 전부 적용 16블록 안) · 데이터계약 RED 0 · master_tables `--no-build` 직전 판과 동일 · xlsx 드리프트 0 · 매니페스트 102 통과.
  갱신: `kics_rules_golden`(YELLOW 1,936→1,934 · GREEN 13,705→13,709 · RED 56→54) · 입력지문 4종(+3바이트) · 시험 2파일(등재부 census 10→39, tier2 면제 22→20). 남은 것: PL·17BS 골든 미실행(parser-ifrs17 동시 작업, 빌더가 kics_disclosure 는 이름·티커만 읽음) · 관찰 3건은 changelog 28차.
- **2026-10-12 (27차) 소진율·전망 복원 독립 감사 (티켓 `20261012T2040Z`, 읽기 전용 — 마스터·HTML·게이트 코드 무수정)** — 기준 `dbbffcb5`+`24a3dd6c`(HEAD `8fe48b1b` 도 대상 파일 동일): 47사 독립 재계산 기본자본 47/47 · 한도 47/47 · 초과분 47/47 · 보완자본(문자 그대로) 45/47(나머지 2 = 항목 54 예외, 문서화됨), 전망 7사 손계산 차이 0, 화면 47사 · 375px · 공개 시트 3종 불일치 0.
  발견: 전망 0% 자름이 노트에 거짓 개선을 인쇄(예별 +41.8%p · 롯데 +5.4%p) · 도넛 툴팁 6사 잘림 · 기본자본 인정한도 33사가 15% 인쇄 · DB손보 콜일자 엇갈림 · 하나손해 원장 미갱신. 재현물 `data/_derived/capsec_audit_20261012/`(`e6_screen_results_dbbffcb5.txt`), 발주 publishing `20261012T2235Z` · designer `20261012T2236Z`.
  남은 것: 없음(두 stage 가 고쳤고 29차에서 재측정, 위 항목).

## 열린 일

- [ ] **29차 재측정 후속** — ① 다음 변경 때 같은 순서로 재측정(콜일 규칙 확인 끝남; `h1_tier2_recompute_47.py` 기본 규칙 = 첫 콜일 <= 분자 기준일, 이전 핀은 `H1_PRIMARY=flag`; `h1h`·`e11` 은 이전 핀 대비 변동 목록): `a2_dump_inputs` -> `h1_tier2_recompute_47` -> `h2_tier1_check` -> `d1_forward_handcalc` -> `d2_forward_internal_consistency` -> `h4_expected` -> `e7`~`e10` + 브라우저 `h5`·`h6`·`h7`·`h8`(사용법은 각 파일 머리 주석; 페이지가 CSP 로 `eval` 불가라 `<script src>` 주입, 유휴 창은 rAF 가 안 돌아 공유 이미지 검사는 `Chart.defaults.animation=false`).
  ② owner 결정 잔여: 코리안리 제5·6회 · 농협생명 제5회 · 푸본 600억(발행사 표 X 검정으로 판정 불가) · 기본자본 두 갈래(기발행 15% / 신규 10%) 결합 규칙 · IBK TAC 위치 · 아이엠라이프 전환우선주 차감 방식(해석에 따라 16.0~70.4%) · 악사 JPY 후순위 콜일 추정 확인(29.2% 가 그 추정 위에 있다). 해소: DB손보 제1~5회 기본자본형 확정, 기발행 차감 = 원장 2022년 이전(owner 2026-10-12 밤).
  ③ **전망 JSON 내부 정합 룰 제안**(게이트 코드는 이번에도 안 건드림): 모든 해 `ratio_pct = capital_eok / scr_eok x 100`(+-0.011), 어긋나면 `capacity_exhausted` 가 같이 true 일 때만 허용(`d2_forward_internal_consistency.py` 초안; 화면 쪽은 designer `scripts/check_kics_forward_note.py` 가 이미 막는다). ④ 화면 대 JSON·툴팁 폭·공유 이미지 감사는 수동 브라우저 스크립트(`h5`~`h8`)다 - 반복 도구(헤드리스)로 만들지 UH-26 과 함께 판단.
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
