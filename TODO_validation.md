# Insurequant Validation TODO (Stage 3)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-validation.md` · 이력 `docs/changelog_validation.md`
> 2026-10-07 정리 전 전문(V1~V19 블록 포함)은 `docs/todo_archive_validation.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-11 (21차) 재보사 단계 10 — 금리민감도 RS1·RS5 근거 박제 면제 장치 `rs_pinned_exemptions` 신설 + owner 승인 5건** — 금리민감도 게이트
  RED 5→**0**, K-ICS 게이트 exit 0(finding 변화 0) · 데이터계약 RED 0 · 라이브 아티팩트 RED 0. 변이시험 70건(훅 묶음 편입). 하노버 적용후 12행 독립 검산 통과. 미커밋.
  남은 것: 오케스트레이터의 `prepush_check.py --full` 1회. 런로그 `reinsurer_runlog_KR1101-1108_12.md`.
- **2026-10-10 (20차) 재보사 단계 9 — census 원천부재 면제 장치 `_CENSUS_SOURCE_ABSENT` 신설 + 8칸 · KR1107 2023.3Q 문서 미수집 · 예별 PL YTD 셀 등재** — K-ICS 게이트
  RED 57 · blocking 0 · census 0 · **exit 0**, 데이터계약 RED 3(xlsx). 골든 4종·입력지문 재생성(기존 39사 슬라이스 불변). 미커밋.
  push 훅은 BLOCKED: xlsx·public_exports(publishing) · 듀레이션 갭 46·금리민감도 40(parser 신규 발주). 런로그 `reinsurer_runlog_KR1101-1108_10.md` §6.
- **2026-10-10 (19차) 재보사 단계 8 — 룰 2·4·5·6 잔차 박제 장치 `_IDENT_ISSUER_INCONSISTENT` 신설 + owner 승인 29건 등재** — K-ICS 게이트
  RED 65→57 · blocking 29→**0** · 설명 안 되는 RED 0(exit 2 는 census 헤드라인 전용 12칸). 기존 39사 finding 변화 0, 골든 2종 `--update`.
  미커밋. 남은 것: census 12칸 owner 결정 · pytest (다) 발주분 · 포트폴리오 R3 KR0100 3건 owner 판단. 런로그 `reinsurer_runlog_KR1101-1108_8.md`.

## 열린 일

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
