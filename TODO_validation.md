# Insurequant Validation TODO (Stage 3)

> 갱신 2026-10-22 (31차 교보 KR0073 CSM·PL 재작성 기준 적재 `3e53aef8` 독립 검수 + tax22_src 룰 최신 비교열 판 인정 + 골든 정리) · 프롬프트 `docs/agents/claude-agent-validation.md` · 이력 `docs/changelog_validation.md`
> 2026-10-07 정리 전 전문(V1~V19 블록 포함)은 `docs/todo_archive_validation.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-22 (31차) 교보생명 KR0073 CSM·PL 「재작성 기준」 적재(`3e53aef8`) 독립 검수 + `tax22_src` 룰 수정 + 골든 정리 (대상 커밋 `3e53aef8`, 후속 `eea3f61c`)** — 원문 자체 재독(`vreader.py`, parser 코드 미사용): PL 항목 1·4·17·19·20·22·23·24·25·31 x 2023.1Q~2024.2Q 60/60 · CSM 항목 1~6 x 7분기 일치(0건 불일치), CSM 상각 대 PL 항목 4 짝 6/6 정확히 닫힘, 2024.3Q·4Q 누계 불변, 교보 밖 변경 0(마스터 · 출처표 · 골드 · 장부 전수 대조).
  룰: `tax22_src` 가 같은 분기 원공시 판 **또는** 다음 해 같은 기간 캐시 전기 열(`_tax22_prior_tier1`, 빌더와 같은 `_parse`) 중 하나와 맞으면 통과. 전 643버킷 시뮬: 닫힘 4(교보 2023.3Q~2024.2Q) · 깨짐 0 · 주입 탐지 282/282 불변, 변이시험 2종 신설(분기 제거 시 교보 4칸 RED 복귀). 게이트: tax22_src 278P/4F -> 282P/0F · 데이터계약 RED 0 · 골든 `master_tables`(pl_bridge · csm_amort_identity · qoq_warn 3필드, 교보 행만 원인 입증) + 입력지문 `viz_ifrs17_panels` 갱신.
  발견: **2023.3Q 단일분기(값_당분기) 재작성 기준 이음매** = parser 티켓 `20261021T1655Z`(PL 항목 24 마스터 83,882 대 공시 3개월 열 8,175 · CSM 단일분기 항등식 +960.03억; 판정: 누계 방식에선 불가피하나 값을 싣는 것은 비추천, 선택지 A·B·C 제시). 남은 것: 그 티켓 · 단일분기 항등식 룰 설계(아래 열린 일).
- **2026-10-13 (30차) IFRS17 「최신 비교열」 적용 249칸 독립 검수 + 골든 정리 (티켓 `20261012T2230Z`, 커밋 `b8c37fff` 대상)** — 원문(DART XML·경영공시 PDF)을 자체 코드로 재독: 249/249 일치(BS 65 · CSM 27 · PL 157, 3개월→누적 14칸은 누적 열 인쇄값 일치·한화손보 2칸은 PDF 두 판 일치), 마스터 변경 = 정확히 249칸, 골드 오버레이 +157/+27/+65 가 계획과 1:1(기존 owner 칸 변경 0), 예외 해제 10줄 모두 산수로 닫힘. 후속 `99c7ead7`(NB 12칸 · 콤보 8잎 · 비교 패널 전 잎 658×12 재계산) 일치.
  게이트: 데이터계약 RED 0 · `validate_master_tables --no-build` exit 2(기지 23건, 직전 29) · 연속성·ILP·NB·워터폴·xlsx 드리프트 0 · 골든 갱신 3종(master_tables SUMMARY · 17BS sha(빌더 산출 = 커밋 마스터 바이트) · 입력지문 2종). 발견: parser 티켓 `20261012T1820Z`(푸본현대 1Q 항목 18·19 · 흥국화재 1Q 항목 19 · 삼성화재 2024.1Q 항목 13·14 · 삼성생명 BS 2024.4Q/2025.1Q 기준 단절). 경영공시 PDF 미결정 116칸도 재독 116/116 일치.
- **2026-10-13 (29차) 소진율·전망 재측정 (티켓 `20261012T2040Z`, 대상 HEAD `6fd00720` -> 후속 확인 `20a700a9`, 읽기 전용 — 마스터·HTML·게이트 코드 무수정)** — 새 규칙(기발행 차감 = 원장 2022-12-31 이전 잔액, 콜 경과 제외)으로 보완자본 소진율 47사 독립 재계산 **47/47 일치** · 기본자본 47/47(결속 갈래 없는 33사 한도 10%, 하나생명 238.2 · 교보 70.1 · DB손보 151.6 불변) · 전망 7사 손계산 35점 차이 0(총자본·기본자본 경로 이전 판과 동일, 행 변경은 KR0050 `confidence` 뿐) · 타임라인·공개 시트 4종 불일치 0 · 화면 47사 x 1280/375 불일치 0(예별·롯데 노트 거짓 개선 제거, 툴팁 잘림 0, 공유 이미지 15사 정상).
  불일치 1건(원장 `past_call_outstanding` 플래그가 행 `as_of` 기준이라 콜 경과 3건이 차감에 남음)은 **해소**: publishing `7e6e55d0`·`20a700a9`(첫 콜일 <= 분자 기준일)를 독립 재측정으로 확인 - 47/47 일치, 메리츠 30.8→37.5 · 아이엠라이프 56.9→70.4 · KB라이프 0.0→0.8, 그 밖 변동 0(44사 불변), 기본자본·전망·타임라인·원장·`K-ICS.html` 바이트 동일, 화면 47사 x 1280/375 불일치 0, 티켓 `20261013T0205Z` resolved(`_resolved/`). 재현물 `data/_derived/capsec_audit_20261012/`(`h1h_delta_vs_previous_20a700a9.txt`·`e11_public_sheet_delta_20a700a9.txt`).
  남은 것: 공유 감사 티켓 `20261012T2040Z` 종결(오케스트레이터 몫) · owner 결정 잔여 5건(아래 열린 일).

## 열린 일

- [ ] **단일분기(값_당분기) 항등식 룰 설계 범위(룰 없음 -> 등재 금지, 설계만)** — 현재 어떤 게이트도 `기초_분기 + 신계약 + 이자 + 가정 + 상각 = 기말_분기`(값_당분기 기준)를 안 본다. 전 회사 333 버킷 실측 5건 어긋남(교보 2023.3Q +960.03 · 메리츠화재 2023.3Q +4,007.3 · 한화생명 2023.3Q −950.1 · KB라이프 2023.4Q −126.4 · 롯데손보 2024.4Q +105.3; `data/_derived/kyobo_validation_20261022/census_quarterly_closure.py`). 전부 3Q/4Q 에서 재작성 기준과 이전 분기 기준이 섞인 유형으로 보이나 회사별 원인은 미확인. 룰을 만들면 이 5건의 처리(수정 vs owner 등재)가 먼저 결정돼야 RED=0 이 된다. PL 쪽은 3개월 열 인쇄값 대조가 원문 필요라 전 회사 룰이 못 된다(교보만 `v_quarterly_3m.py` 로 실측).
  **2026-10-22 설계 측정 결과(룰 코드는 아직 안 건드림, `data/_derived/remaining_20261022/c_singleq/`)**: 룰 4개 초안(`SQ_CSM_ROLL` · `SQ_*_DERIV` · `SQ_PL_EQS` · `SQ_AMORT`; `validate_master_tables.py` 5절, 허용오차는 기존 식 재사용, 예외는 칸별 장부 `single_quarter_ledger.json`) 을 전 버킷 시뮬레이션하면 지금 켤 경우 RED 94(CSM 5 · PL 식 3 · 상각 1 · `null_dangi` 미등재 85버킷 430칸). 가장 작은 실패 105.3억 대 통과 최대 1.0억이라 임계는 넓다. 순서: ① parser 가 메리츠·한화생명·KB라이프·롯데손보 CSM·PL 을 같은 판으로 갱신(원문에서 닫힘 확인) ② KDB생명 2023.2Q · 현대해상 2025.3Q 재확인 ③ 430칸 `null_dangi` 등재 ④ 교보 2023.3Q +960.03억은 owner 결정(장부 핀 또는 공란, 공란은 `build_csm` 에 경로가 없음) ⑤ 그다음 룰 구현 + 골든 `--update`(새 SUMMARY 필드만 움직임, NEW=0 증명).
- [ ] **tax22_src 가 못 보는 잔여(참고)** — 교보 외 17사 51버킷에서 FS-API 다음 해 전기 열이 마스터(원공시 판)와 다르다(`sim_other_vintage_buckets.txt`). 2026-10-22 판정표(`remaining_20261022/d_census/`): 즉시 안전 0 · owner 결정 19 · 유지 32. 방침이 정해지면 그 19버킷이 다음 후보.
- [ ] **29차 재측정 후속** — ① 다음 변경 때 같은 순서로 재측정(콜일 규칙 확인 끝남; `h1_tier2_recompute_47.py` 기본 규칙 = 첫 콜일 <= 분자 기준일, 이전 핀은 `H1_PRIMARY=flag`; `h1h`·`e11` 은 이전 핀 대비 변동 목록): `a2_dump_inputs` -> `h1_tier2_recompute_47` -> `h2_tier1_check` -> `d1_forward_handcalc` -> `d2_forward_internal_consistency` -> `h4_expected` -> `e7`~`e10` + 브라우저 `h5`·`h6`·`h7`·`h8`(사용법은 각 파일 머리 주석; 페이지가 CSP 로 `eval` 불가라 `<script src>` 주입, 유휴 창은 rAF 가 안 돌아 공유 이미지 검사는 `Chart.defaults.animation=false`).
  ② owner 결정 잔여: 코리안리 제5·6회 · 농협생명 제5회 · 푸본 600억(발행사 표 X 검정으로 판정 불가) · 기본자본 두 갈래(기발행 15% / 신규 10%) 결합 규칙 · IBK TAC 위치 · 아이엠라이프 전환우선주 차감 방식(해석에 따라 16.0~70.4%) · 악사 JPY 후순위 콜일 추정 확인(29.2% 가 그 추정 위에 있다). 해소: DB손보 제1~5회 기본자본형 확정, 기발행 차감 = 원장 2022년 이전(owner 2026-10-12 밤).
  ③ **전망 JSON 내부 정합 룰 제안**(게이트 코드는 이번에도 안 건드림): 모든 해 `ratio_pct = capital_eok / scr_eok x 100`(+-0.011), 어긋나면 `capacity_exhausted` 가 같이 true 일 때만 허용(`d2_forward_internal_consistency.py` 초안; 화면 쪽은 designer `scripts/check_kics_forward_note.py` 가 이미 막는다). ④ 화면 대 JSON·툴팁 폭·공유 이미지 감사는 수동 브라우저 스크립트(`h5`~`h8`)다 - 반복 도구(헤드리스)로 만들지 UH-26 과 함께 판단.
- [ ] **최종 라운드 후속(22차)** — 소유자 결정 15건(런로그 Step 5) · 법정준비금 `run_components`(R-RSV-4/12) 데이터계약 배선(현재 단독 RED 10, parser-ifrs17 선행) ·
  CSM 워터폴 대 ILP CSM 잔액 교차 게이트 `CSM_WATERFALL_VS_ILP_CSM_STOCK`(제안만 -- owner 는 기준 차이 등재를 승인했으나 **룰이 없어 등재할 줄이 0**; 새 룰 설계가 선행, 287칸 중 6칸+롯데 군집, `data/_derived/validation_registrations_20261012/csm_wf_vs_ilp_basis_diff_cells.md`) · 연속성 게이트 밴드 0.5%가 숨기는 롯데 2023.4Q −105억.
- [ ] **`CSM_WATERFALL_VS_ILP_CSM_STOCK` 룰 설계 범위(설계 선행, Opus 몫)** — 입력: `CSM_waterfall.json` 기말 CSM(항목 6) 대 `insurance_liability_portfolio.json` 항목 3+6(억원), 공유 (회사,분기) 287칸. 허용오차 후보 `max(1억, 0.5%)`(262칸 1억 이내·281칸 통과·6칸 초과). 예외 형태: 재작성 칸(`ilp_restated_comparative.json`·워터폴 재작성 기록)은 기준 명시 YELLOW, 계약이전(예별 2025.4Q)은 칸 박제, 값 박제(AIG R3 `R3_PINNED_EXEMPTIONS` 형태)와 INERT/DRIFT RED 포함. 롯데손해 2023.4Q~2024.3Q 군집·2024.3Q 잔차 −23 은 설명 안 되므로 등재로 덮지 말고 칸별 분류. 칸 목록 `data/_derived/validation_registrations_20261012/csm_wf_vs_ilp_basis_diff_cells.md`.
- [ ] **재보사 push 차단 최종 확인** — 단계 10 에서 훅의 게이트를 하나씩 다 쟀다(전부 exit 0, 런로그 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_12.md` §5). 남은 것은 오케스트레이터의
  `prepush_check.py --full` 1회 실측. 교훈: 단계 종결 전 도메인 게이트까지 훅 전체를 잰다(단계 8 은 데이터계약만 재서 3·4 를 놓쳤다).
- [ ] **기존 키 집합 등재부를 박제 장치로 옮길지** — `RS1_EXCEPTIONS`(예별 2024.4Q)·`RS2_EXCEPTIONS`·`RS5_EXCEPTIONS`(17)는 근거 재확인 없이 영원히 빠진다.
  단계 10 장치(`rs_pinned_exemptions`)로 옮기면 매 실행 재검산된다. 등재 변경이라 owner 결정 사항(이번 범위 밖, 손대지 않음).

- [ ] **유지율 VP 재검증** — 티켓 `inbox/_resolved/20261007T1001Z__validation__MULTI_2023.2Q-2026.2Q__persistency_validation_findings.md`
  는 resolved 로 닫혔지만(2026-10-14 확인) 재검증 기록이 changelog 에 없다: RED-1(KR0004 2026.2Q 단위)·YELLOW-2/4/6/8 재확인, MI 보강 티켓(KR0051·KR1000)·downloader KR0150 도 같이. 재현 스크립트는 보고서 머리 경로.
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
