# Insurequant TODO — cross-stage

> 갱신 2026-10-07 · 사실(게이트·inbox·커버리지)은 `scripts/status_report.py --fast` 가 정본이고, 이 파일은 의도만 적는다.
> stage 별 TODO·프롬프트·이력 위치는 `CLAUDE.md` §1. 2026-10-07 정리 전 전문은 `docs/todo_archive_root.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-07 문서·inbox 정리.** TODO 8개를 열린 일 위주로 다시 썼다(정리 전 전문은 각 `docs/todo_archive_*.md` 맨 위).
  K-ICS 예외 등재부 → `docs/kics_gate_exceptions.md`, 분기 라운드 절차 → `docs/flows/kics_quarterly_round.md`. inbox 활성 10 → 4.
  서브에이전트 모델을 `sonnet`/`opus` 별칭으로 바꿔 최신 모델을 따라가게 했다.
- **2026-10-06 AIA생명 2024.4Q 항목46 단위 정정(3607646 → 36076.46) + `PUBLIC_EXPORT_INTERNAL_JARGON` 신설.**
  라이브 `main` `420cdc3`(build_id `54ec835`, owner 폰 배포). 상세 `docs/changelog_parser_kics.md`·`docs/changelog_validation.md` 2026-10-06.
- **2026-09-22 금리 듀레이션갭 마스터 신설** — `kics_duration_gap.json`(39사 × 짝수분기 270셀, 분모 = 금리위험액 현황 자산총계)
  + 라이나생명 2023.4Q PL 20칸. 라이브 `22e2471`. 상세는 archive.

## 열린 일

- [ ] **신규 도메인: 채널별 유지율 · 손해율 추이 + 사별 비교 기능(owner 팀장 요청 2026-10-07)** — 추출 진행 중.
  인수인계 `docs/handoff_20261007_persistency_lossratio_compare.md`(상태·census·남은 순서), 명세는 `inbox/parser/20261007T0*` 티켓 3개.
  비교 기능은 owner 의 핵심 지표 목록 대기.
- [ ] **재보사 7곳 + 마이브라운(KR1101~KR1108) K-ICS 스윕 마무리(owner 2026-10-10)** — 단계 6(validation 재검증) 완료: 게이트 RED 71(blocking 35), 기존 39사 변경 0, 스코리는 `_TRANSITION_APPLIERS` 편입·골든 재생성 끝.
  계약 `docs/handoff_20261008_reinsurer_pipeline.md` §7, 실행 기록 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_{1a..6}.md`. 단계 7 parser 완료(2026-10-10): 게이트 RED 71→65·blocking 35→29, 신규 RED 0, 기존 39사 25,522행 HEAD 와 동일(오케스트레이터 재측정). 단계 8 validation 완료(2026-10-10): 룰 2·4·5·6 잔차 박제 장치 신설·승인 29건 등재·골든 재생성, 게이트 blocking RED 0, 기존 39사 변화 0. **작업 브랜치 push 는 훅이 아직 막는다**(owner 가 push 승인, 훅 우회 안 함): ① K-ICS census 결측 12칸(owner 결정 = 원천 부재 census 면제 장치 신설 → validation 단계 9 `inbox/validation/20261010T1300Z__*`, downloader 재확인 `inbox/downloader/20261010T1230Z__*` 결과 후 발사) ② 금리민감도 근거 25칸 + 퍼시픽 KR1107 2023.3Q·4Q 적재(owner 결정 = 적재 + 새 RED 3건 예외, handoff §7-12) → parser 단계 9 `inbox/parser/20261010T1230Z__*` ③ 예별 PL 3칸 → parser(ifrs17) `inbox/parser/20261010T1100Z__*KR0004*`(LIC 적재 뒤) ④ xlsx K-ICS공시 시트·public_exports → publishing `inbox/publishing/20261010T1100Z__*`.
  owner 승인 완료(2026-10-10, `docs/handoff_20261008_reinsurer_pipeline.md` §7-10): 자기모순 21건·원천 부재 8건 등재(룰 2·4·5·6 잔차 박제 장치는 새 설계라 Opus), 제네럴 보완자본→0, 스코리 27후 166.8 유지·22후 534.93, 제네럴 TIR/TER/TIRR=X, KR1107 2023.3Q·4Q 적재. parser 7단계(P1~P10) 재시작 후 validation 8단계(등재·장치·골든·pytest 분류 정리)가 이어진다.
  **배포 선행**: 재보사 8곳이 든 마스터는 designer 의 재보험사·보증 3분류(아래)가 끝나기 전에 라이브에 올리지 않는다. 커밋 미실시(워킹트리에 다른 세션 변경 혼재).
- [x] **index 시장지도 3컬럼: 생보 / 손보 / 재보험사·보증(owner 2026-10-10)** — designer 반영 완료(미커밋·미배포): `data/company_segment.json` 매핑으로 index·compare 3구분, 새 8곳은 K-ICS·compare·IFRS17·검색창에서 깨짐 없음 확인. 재보사 배포 선행 조건은 충족. 남은 것은 publishing 이 `scripts/android_push_and_deploy.sh` `NEW_FILES` 에 `data/company_segment.json` 을 넣는 일(`TODO_designer.md` 「publishing 이 배포 전에 해야 할 일」).
- [ ] **재보사 IFRS17 지표 적재(다음 round, owner 2026-10-10)** — CSM 상각 스케줄·가정민감도·요약 PL/BS·4-6-2 포트폴리오. 정찰 `data/disclosure/_meta/reinsurer_ifrs17_scout_20261010.md`(우선순위 ①~④, 감사보고서 CSM 변동표는 변환이 먼저).
- [ ] **IFRS17.html 섹션 3 CSM 시계열 → 묶음·누적 막대 + 보조축 선 콤보(owner 2026-10-10)** — 분기마다 막대 2개: 왼쪽 잔여보장요소(아래부터 CSM(주축 0 시작) · BEL · RA · 가능한 회사는 PAA·VFA 누적) + 오른쪽 **발생사고요소(BEL · RA 누적)**, 보조축 꺾은선 = 신계약 CSM. 참고 그림 `docs/design_refs/combo_stacked_column_line_reference_20261010.png`.
  **designer 이식 완료(2026-10-10, IFRS17.html·`data/csm_combo/panel_csm_combo.json`, 미커밋·미배포)**: owner 채택 목업 + 값 표, CSM 증감 띠는 owner 정정으로 제외, 오른쪽 막대(발생사고요소)는 BS 항목 20 − 잔여보장요소의 「추정」 자리 표시(빌더 `lic_estimate()` 한 곳). 배포 시 `NEW_FILES` 에 패널 JSON 추가 필요.
  **발생사고요소 BEL·RA 는 마스터에 없다** — 정찰 완료(`data/disclosure/_meta/lic_scout_20261010.md`): 출처 = DART XML 「잔여보장·발생사고 변동」 주석표, 직접값 159셀(24사×5분기+39사 4Q) 중 123셀이 BS 항목 20 과 닫힘, 비상장 15사 5분기 75셀은 원천 부재, BS−2-4 총액 추정은 DB손보·롯데·메리츠·하나손보에서 부정확, ABL·KDB생명·푸본현대는 2-4 가 이미 LIC 포함. 적재는 owner 결정으로 **단계 적재 + 단일열 회사 간접 계산값 사용**, 새 마스터 없이 `insurance_liability_portfolio.json` 항목 10번부터 추가(억원). 1단계(A1·A2 101셀) parser 진행 중(`inbox/parser/20261010T0945Z__*`), 2단계(단일열 간접 도출)·3단계(비상장 4Q)는 1단계 보고 후. `insurance_liability_portfolio.json`(2025.1Q~2026.2Q)은 **잔여보장요소(LRC)만**이라 BS 보험계약부채보다 작다.
  LRC 데이터 선행은 2026-10-10 에 처리: 빈 9칸·값 의심 4건(ABL 2025.2Q 단위 100배 포함)·스캔본 13칸·하나생명 2026.2Q(상세 줄 합 43,549억, owner 승인)·아이엠라이프 2025.1Q(최신 공시 정정값, owner 승인)를 채우고(백업 `data/_derived/ilp_backup_20261010_pre_merge.json`), DB손보·AIG·서울보증 2026.2Q 가 2026.1Q 사본이던 것도 정정. 남은 것: ① 롯데손보 2026.2Q 항목 9=1 확인(마스터에 1 선례 없음, 2025.1Q~2026.1Q 항목 9 는 비어 있음) ② KR0100 R3 3건(특별계정 때문, IFRS17 레인에서 item20 정의 정리 또는 예외 등재) ③ 검증기 정비 — 스캔 3사 `DOCUMENTED_EXCEPTIONS` 삭제·재보사(KR11xx) R2 census 46건 제외(다음 round 전까지) ④ 추출기 공통 결함 7개(pdfplumber 단독·헤더 위치·5자리 공백 분리·단위 머리말·이미지 헤더 등, 런로그 `ilp_gap_runlog_textlayer_20261010.md`). 검증기는 push 게이트가 아님.
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
