# Insurequant Validation TODO (Stage 3)

> 갱신 2026-10-13 (28차 K-ICS 최신 공시 직전 컬럼 적용 독립 검수) · 프롬프트 `docs/agents/claude-agent-validation.md` · 이력 `docs/changelog_validation.md`
> 2026-10-07 정리 전 전문(V1~V19 블록 포함)은 `docs/todo_archive_validation.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-13 (28차) K-ICS 「최신 공시 직전 컬럼」 적용 65칸 독립 검수 + 골든 정리 (티켓 `20261013T0010Z`, 커밋 `74a415bf` 대상)** — 원본 PDF 직접 재판독: primary 33칸 33/33 일치(10쪽은 240dpi 렌더링 육안), 미러 22칸·파생 10칸 재계산 일치, 마스터 diff = 정확히 65칸(레코드 30,011 불변). 보류 10블록 전부 사유 타당.
  게이트: K-ICS exit 0 RED 56→54(풀린 KR0003 2025.1Q·KR0032 2024.3Q 다리 RED 2건, 새 RED 0, 이동 31 finding 전부 적용 16블록 안) · 데이터계약 RED 0 · master_tables `--no-build` 직전 판과 동일 · xlsx 드리프트 0 · 매니페스트 102 통과.
  갱신: `kics_rules_golden`(YELLOW 1,936→1,934 · GREEN 13,705→13,709 · RED 56→54) · 입력지문 4종(+3바이트) · 시험 2파일(등재부 census 10→39, tier2 면제 22→20). 남은 것: PL·17BS 골든 미실행(parser-ifrs17 동시 작업, 빌더가 kics_disclosure 는 이름·티커만 읽음) · 관찰 3건은 changelog 28차.
- **2026-10-12 (27차) 소진율·전망 복원 독립 감사 (티켓 `20261012T2040Z`, 읽기 전용 — 마스터·HTML·게이트 코드 무수정)** — 기준 `dbbffcb5`+`24a3dd6c`(HEAD `8fe48b1b` 도 대상 파일 동일): 47사 독립 재계산 기본자본 47/47 · 한도 47/47 · 초과분 47/47 · 보완자본(문자 그대로) 45/47(나머지 2 = 항목 54 예외, 문서화됨), 전망 7사 손계산 차이 0, 화면 47사 · 375px · 공개 시트 3종 불일치 0.
  발견: 전망 0% 자름이 노트에 거짓 개선을 인쇄(예별 +41.8%p · 롯데 +5.4%p) · 도넛 툴팁 6사 잘림 · 기본자본 인정한도 33사가 15% 인쇄 · DB손보 콜일자 엇갈림 · 하나손해 원장 미갱신. 재현물 `data/_derived/capsec_audit_20261012/`(`e6_screen_results_dbbffcb5.txt`), 발주 publishing `20261012T2235Z` · designer `20261012T2236Z`.
  남은 것: 두 stage 답변 후 재측정 · owner 결정 4건(아래 열린 일 첫 항목).
- **2026-10-12 (26차) 골든 갱신 + AIG R3 박제 등재 (티켓 `20261012T1400Z`)** — 이동 원인은 parser-kics `acd351a` 하나뿐(직전 마스터로 돌리면 K-ICS 골든 5키 전부 일치, 입력지문 4종은 `kics_disclosure.json` 한 파일 +5,195바이트). `--update`: `kics_rules_golden`(YELLOW 1,935→1,936 · GREEN 13,684→13,703 · SKIP 3,345→3,325 · RED 56 불변) · `builder_input_fingerprints`(4종).
  무이동 확인(실행): dividend · post_transition · master_tables · viz 2종 · PL(`RUN_PL_GOLDEN=1`, 186초) · 17BS(419초) · deploy_assets 12 · push_gate_wiring 65 · prepush_scope 65 · golden_input_fingerprint 23. AIG KR0029 2024.4Q `R3_CROSS_CHECK` 10배 규칙: `R3_PINNED_EXEMPTIONS`(값 박제 item8 31.0억·item20 291,767.640554백만) + 읽는 쪽 `check_r3` + 변이시험 11건(`tests/test_ilp_r3_pinned_exemption.py`, 훅 묶음 편입). 포트폴리오 검증기 RED 2→1(남은 1 = KR1102 2026.1Q `R2_CENSUS`, owner 결정 대기·미등재).

## 열린 일

- [ ] **27차 독립 감사 후속** — ① publishing `20261012T2235Z` · designer `20261012T2236Z` 답변을 받으면 같은 스크립트로 재측정(`AUDIT_REV=HEAD`, 순서 `b1`→`c2`→`d1`→`d2`→`e2`→`e7`~`e9` + 브라우저 `e3`·`e4`·`e5`; 사용법은 `data/_derived/capsec_audit_20261012/e4_tooltip_audit.js` 머리 주석).
  ② **owner 결정 4건**(publishing 티켓 §결정 대기): DB손보 제3·4·5회 8,820억 분류(발행사 표 X 검정은 보완자본형 쪽, 등재부는 owner 지시로 기본자본형 — 뒤집으면 기본자본 소진율 151.6→75.0) · 코리안리 제5·6회·농협생명 제5회·푸본 600억(X 검정으로 판정 불가) · 보완자본 분자의 항목 54 인쇄값 대 발행연도(메리츠 0.2→32.2, 흥국생명 10.6→37.0; `TODO.md` ③) · 기본자본 두 갈래(기발행 15% / 신규 10%) 결합 규칙과 IBK TAC 위치.
  ③ **전망 JSON 내부 정합 룰 제안**(게이트 코드는 이번에 안 건드림): 모든 해 `ratio_pct = capital_eok / scr_eok × 100`(±0.011), 어긋나면 `capacity_exhausted` 동시 true 일 때만 허용 + 화면 노트가 잘린 값으로 변화를 인쇄하지 않음을 시험으로(`d2_forward_internal_consistency.py` 가 초안). ④ 화면 대 JSON·툴팁 폭 감사는 수동 브라우저 3스크립트다 — 반복 도구(헤드리스)로 만들지 UH-26 과 함께 판단.
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
