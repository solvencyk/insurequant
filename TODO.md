# Insurequant TODO — cross-stage

> 갱신 2026-10-11 · 사실(게이트·inbox·커버리지)은 `scripts/status_report.py --fast` 가 정본이고, 이 파일은 의도만 적는다.
> stage 별 TODO·프롬프트·이력 위치는 `CLAUDE.md` §1. 2026-10-07 정리 전 전문은 `docs/todo_archive_root.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-11 작업 브랜치 push 완료(`6841689`, 훅 gate-clear: RED 0 · offline tests 692 통과).** 재보사 8곳 K-ICS(단계 1~12)·index/compare 3분류·IFRS17 섹션 3 콤보(발생사고요소 실값, 2023/2024 연말 백필, 재작성 3사 †)·모바일 손해율 curve(안 A)·금리민감도/듀레이션갭 재보사.
  라이브 `main` 배포는 owner 가 폰 Termux 에서 `scripts/android_push_and_deploy.sh --from-origin --branch fix/csm-product-segmented-columns` 실행(배포 후 `public_exports/manifest.json` `build_id`=`6fadc86` 확인, 회사망은 `curl --ssl-no-revoke`). **주의: `data/loss_ratio/risk_premium_vs_expected_claims.json`(77MB)이 커밋 `78471c0` 로 원격에 올라갔다(GitHub 50MB 경고) — 이력 정리·LFS·.gitignore 판단 필요.**
- **2026-10-10 LIC(발생사고요소) 적재 + 백필.** `insurance_liability_portfolio.json` 항목 10~15 + 2024.4Q·2023.4Q 백필(BEL·RA 는 2025.1Q 이전에도 공시, DART 주석 2023.1Q~), 재작성 3사(라이나·미래에셋·KB라이프) FY2024 비교열 통일(사이드카 `ilp_restated_comparative.json`), IBK연금 2-4 정정 48칸.
- **2026-10-07 문서·inbox 정리.** TODO 8개를 열린 일 위주로 다시 썼다(정리 전 전문은 각 `docs/todo_archive_*.md` 맨 위).
  K-ICS 예외 등재부 → `docs/kics_gate_exceptions.md`, 분기 라운드 절차 → `docs/flows/kics_quarterly_round.md`. inbox 활성 10 → 4.
  서브에이전트 모델을 `sonnet`/`opus` 별칭으로 바꿔 최신 모델을 따라가게 했다.

## 열린 일

- [ ] **밤샘 스윕(owner 2026-10-11 취침 중, 오케스트레이터 자율 진행)** — 원칙: 동시 에이전트 ≤3, 완료 알림마다 다음 대기열 발사, 같은 마스터를 두 에이전트가 쓰지 않는다, 예외 등재·이력 정리 등 owner 승인 사항은 하지 않고 보고만, 끝나면 커밋 + 작업 브랜치 push(훅 통과 시), **라이브 `main` 배포는 owner 기상 후**(폰 Termux 또는 명시 지시).
  1파 실행 중: designer D1(`inbox/designer/20261011T0300Z__*` 모바일 curve 색·YTD 손익·테스트 선언) · parser-ifrs17 P1(`inbox/parser/20261011T0310Z__*` BS·PL granularity 전수 재채움, 하나손보 선례) · parser-ifrs17 P2(`…T0320Z__*` ILP 나머지 분기·LIC 2·3단계·재보사 4-6-2).
  2파 대기(티켓 작성 완료): **designer D3(`inbox/designer/20261011T0350Z__*` IFRS17 섹션 3 모바일을 데스크톱 콤보 그대로 + 「보험계약부채 시계열」 이름 변경, 앞 단순형 지시 취소 — D1 종료 직후 D2 보다 먼저)** · designer D2(`inbox/designer/20261011T0400Z__*` 공유 스크린샷 전체 복구 + 섹션별 공유 버튼) · publishing(`inbox/publishing/20261011T0410Z__*` 재보사 Forward Outlook·자본성증권 소진율, 스코리 우하향) · parser-kics(`inbox/parser/20261011T0420Z__*` IRR 6셀·퍼시픽 금리민감도·스위스리 2023.2Q·추출기 재현성) · parser-ifrs17 P3(`…T0430Z__*` 재보사 CSM_amortization·sensitivity·waterfall).
  **보험계약부채 마스터 시트(owner 2026-10-11 승인: 「발생사고요소도 마스터 테이블 만들어야지」, `inbox/publishing/20261011T0500Z__*`) — ILP 확정 후 publishing 이 xlsx `보험계약부채` 시트·`public_exports/보험계약부채.json`·다운로드 목록 반영.** 마무리 순서: P1 보고의 별첨 필요 목록 → downloader 발주 → validation(최종 게이트·LIC 검산기·등재 후보 보고만) → publishing 2차(xlsx 시트·`public_exports`·패널 재빌드 `viz_build_csm_combo_panel.py`/`viz_build_compare_panel.py`) → 커밋 → push 훅.
  owner 확인 대기: ① `data/loss_ratio/risk_premium_vs_expected_claims.json`(77MB) 원격 이력 처리(강제 push 필요 여부) ② 기존 `RS1/RS2/RS5_EXCEPTIONS` 새 장치 이전 ③ 스위스리아시아 2023.3Q 적재(새 RED 2 → 등재) ④ KR0100 R3·KR0029 「10배 규칙」 예외 등재 ⑤ compare 선 대비(키컬러 전환으로 해소될 수 있음).
- [ ] **신규 도메인: 채널별 유지율 · 손해율 추이 + 사별 비교 기능(owner 팀장 요청 2026-10-07)** — 추출 진행 중.
  인수인계 `docs/handoff_20261007_persistency_lossratio_compare.md`(상태·census·남은 순서), 명세는 `inbox/parser/20261007T0*` 티켓 3개.
  비교 기능은 owner 의 핵심 지표 목록 대기.
- [ ] **재보사 K-ICS 스윕(KR1101~KR1108) 후속(2026-10-11 완료·push, 계약 `docs/handoff_20261008_reinsurer_pipeline.md`)** — 남은 것: ① 스위스리아시아 2023.2Q 는 새 완성본 전기 열로 적재 가능(새 RED 0)·2023.3Q 는 새 RED 2(룰 4·`8_life_census`) — owner 결정, 적재하면 census 면제 등재를 풀어야 함 ② 퍼시픽 2023.1Q·2Q 는 비율만 인쇄돼 버킷 불가 ③ 퍼시픽 금리민감도 2024.4Q·2025.2Q 는 MD 에 있고 마스터에 없음(12행)·KR1107 비율 정밀값 4칸 ④ **기존 6셀 IRR 잔액 시나리오 열 뒤바뀜**(카카오페이손보 2023.2Q·2023.4Q·2024.4Q·2025.2Q·2026.2Q, 하나손보 2025.2Q — 라이브에 이미 있음, 하나손보 2025.2Q 자산듀레이션 2.25 대 원문 열 순서 4.78) → 고칠지 owner ⑤ 수작업 정정 8쌍은 추출기를 다시 돌리면 되살아남(추출기 보강 티켓) ⑥ 같은 분기에 raw PDF 가 둘이면 일부 도구가 옛 파일을 고름 ⑦ `RS1/RS2/RS5_EXCEPTIONS` 를 새 장치(`rs_pinned_exemptions`)로 옮길지 owner ⑧ 재보사 IFRS17 지표(다음 round, 아래).
- [ ] **재보사 IFRS17 지표 적재(다음 round, owner 2026-10-10)** — CSM 상각 스케줄·가정민감도·요약 PL/BS·4-6-2 포트폴리오. 정찰 `data/disclosure/_meta/reinsurer_ifrs17_scout_20261010.md`(우선순위 ①~④, 감사보고서 CSM 변동표는 변환이 먼저).
- [ ] **IFRS17 섹션 3 콤보 후속(콤보 자체는 2026-10-11 push 완료)** — owner 지시 「이 round 끝나면 나머지 시점 백필 전부」: ① LIC/LRC 백필 2024.1Q~3Q(약 1일, DART 69셀 닫힘)·2023.1Q~3Q(약 0.5일, 경영공시 항목 1~8 은 원천 없음) ② LIC 2단계(단일열 회사 간접 계산값 항목 16·17, 사전시험 105셀 중 28셀 통과) ③ 3단계(라이나 PDF 5셀·처브 3셀·하나손보 별첨·예별 2025.4Q 는 0 을 안 지어 넣음) ④ LIC 검산기가 재작성 3셀에서 사이드카 값을 앵커로 쓰도록(지금 R-LIC1 RED 3, 의도된 결과) ⑤ 포트폴리오 검증기 RED 4(KR0100 R3 3 + KR0029 2024.4Q 「10배 규칙」 1) 판단 ⑥ 롯데손보 2026.2Q 항목 9=1 확인 ⑦ 추출기 공통 결함 7개 ⑧ compare 선 대비 2.1~2.6:1(키컬러 전환과 묶어 owner 확인, `TODO_designer.md`). 사이드카: 2-4 가 LIC 포함인 ABL·KDB생명·푸본현대(`ilp_includes_lic.json`).
- [ ] **PC 부하 실측(owner 2026-10-10, 틈날 때)** — docling 변환 1건의 최대 메모리·소요를 에이전트가 쉬는 시간에 재서 보고. 현재 RAM 15.5GB(증설 불가)·8코어, owner 희망 RAM 32GB·12코어(즉시 교체 아님). 한도: 동시 에이전트 ≤3 · docling ≤2.
- [ ] **2026.3Q 정기경영공시 라운드** — 2Q 는 8/29~31 에 게시됐으니 3Q 는 11월 말 예상. 절차 `docs/flows/kics_quarterly_round.md`
  (라벨·스크립트를 3Q 로 바꿔 쓴다). owner 가 부르기 전에는 시작하지 않는다.
- [ ] **J-ESR 10월 말 재census**(기한 2026-10-31 직후) → `TODO_jp.md`.
- [ ] **inbox 열린 4건** — parser 3(PL 부모 #2 결측 26버킷 · 메리츠 2026.2Q item2/3 적용후 stale 외 · 금리민감도 phase 31칸)
  + publishing 1(자본성증권 step_up·잔액기준일·한화 item54). 남은 일은 각 티켓 맨 아래 「현황」.
- [ ] **PL 골든 실패** — `RUN_PL_GOLDEN=1` 에서 `sha256_coverage` 만 어긋난다(라이나 KR0074 2023.4Q coverage 1행). → `TODO_parser_ifrs17.md`.
- [ ] **KR0004 2025.4Q 비교 단절 주의** — 같은 계열(예별 = 구 MG)이지만 2025-09-03 계약이전으로 DART 와 경영공시 규모가 52배 다르다. → `TODO_parser_ifrs17.md`.

## 보류 (재개 조건이 오면 연다)

- F18 IR factsheet 정형화 + DART↔IR 교차검증 — owner 2026-08-30 "꼭 필요할 때만". raw 130파일, parsed 6파일.
- F13 재보험 영업 지표 — downloader F8(손보협회 비교공시) 수집이 선행.
- 중장기 제품·수익화 트랙 — `docs/roadmap.md`.

## 정책 (cross-stage)

| # | 결정 | 날짜 |
|---|---|---|
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료** | 2026-05-24 |
| 5 | API keys: repo root `.env` only (gitignored). Never commit/log key values | 2026-05-24 |
| 6 | Bond Call rule: issue + 5y for ALL bonds. Past 5y = assume `called` (갱신: 콜 지난 미상환분은 `TODO_publishing.md` 2026-09-23) | 2026-05-24 |
| 7 | Pushing: subagent **reports + recommends only**. 라이브 `main` 배포는 owner GO | 2026-05-30 |
| 8 | DART attachments (별첨/감사보고서 zip): **don't fetch**. Body XML has all IFRS17 disclosures | 2026-05-30 |

## 참조 (필요할 때만 연다)

- K-ICS 게이트 documented exceptions: `docs/kics_gate_exceptions.md`
- 분기 라운드 절차: `docs/flows/kics_quarterly_round.md`
- Status 이력·정리 전 전문: `docs/todo_archive_root.md`
