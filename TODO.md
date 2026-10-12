# Insurequant TODO — cross-stage

> 갱신 2026-10-12 · 사실(게이트·inbox·커버리지)은 `scripts/status_report.py --fast` 가 정본이고, 이 파일은 의도만 적는다.
> stage 별 TODO·프롬프트·이력 위치는 `CLAUDE.md` §1. 2026-10-07 정리 전 전문은 `docs/todo_archive_root.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-12 오후 작업 브랜치 push 직전(HEAD `0f143d2` 이후).** owner 결정: K-ICS 소진율 도넛·Forward Outlook 을 화면에서 내림(신종 분류 판단이 들어가는 숫자는 건조하게 못 뽑는다 — 유료화 후보) → 발행연도별 신종·후순위채 누적 막대 + 큼직한 셀 2개(최근 발행금리·총발행액 '23~·가장 가까운 콜 1건), 기본자본소진율·보완자본소진율·자본비율전망 3시트는 다운로드 목록에서 임시로 내림(파일·시트 그대로, `download-survey.js` 주석 해제로 복구).
  공유 버튼 이용 기록(`shares` 탭) 라이브(`deploy/design-20261012`), IFRS17 「보험금 예실차비율」 독립 섹션 + 시트 신설, 재보사 PL 7칸 복원·처브 BS/ILP·분할표·퍼시픽/악사 K-ICS 칸 보정, 손해율 재보사 세그먼트 표준화 + 85MB→1MB(.gz). 남은 것: validation 골든·AIG R3 등재(`T1400Z`) → `git push origin fix/csm-product-segmented-columns`(풀 훅 ≈10분) → owner 폰 배포.
- **2026-10-12 아침 작업 브랜치 push(HEAD `6233594` 이후, 훅 gate-clear).** owner 취침 중 재보사 전면 재스윕: 손해율 가정 7곳(master_loss_ratio +1,904·예실차 37→44사)·PL 투자손익/영업외 +303·BS +49·CSM 계열(RGA·하노버 2025.4Q 등)·자본성증권 재확인(0 이 맞음). 화면: K-ICS 시나리오 컬럼명(공시 이름)·듀레이션 주석 ? 안으로·IFRS17 통합 현황 박스·NB 표·보험금 예실차비율 표·모바일 재보험 접기. 훅 소요 26분→약 11분(PDF 텍스트 캐시).
  라이브 `main` 배포는 owner 폰(`bash scripts/android_push_and_deploy.sh --from-origin --branch fix/csm-product-segmented-columns`, `bash` 필수). 결정 대기는 아래 「owner 결정 대기」.
- **2026-10-11 밤 작업 브랜치 push 직전(HEAD `17b526d` 이후).** 재보사 PL 항목 4(CSM 상각) 17버킷 + 라이나 CSM 백필 9분기(워터폴 54칸·상각 +20행·값_당분기 20칸) + PL 항목 4 라이나 9버킷, 상각 스케줄 표 선택 버그 수정(18사 2025.4Q 172칸), 게이트 §3d 항목 4 계보 허용 + owner 승인 등재 4건, 재보사 PL 라벨 「원수」 제거, xlsx·NB(라이나 실제 배수)·패널·공개본 재동기화.
  남은 것: validation 사전 정리(`T2200Z`, 골든 `--update`) → `git push origin fix/csm-product-segmented-columns`(훅 ≈18분) → owner 폰 배포. owner 결정 대기는 아래 「owner 결정 대기」.

## 열린 일

- [ ] **owner 결정 대기(2026-10-12 갱신)** — ① 라이나 CSM 2023.1Q·2Q 보류 유지 vs 옛 기준 적재(`data/_derived/csm_backfill_lina_20261011/held_rows_waterfall.json`) ② 뮌헨 KR1101 2026.2Q 항목 50·52: 원문 p17 에 인쇄됐으나 항목 51 이 공백(대시 아님)이라 51=0(=52−50 항등)을 파생 적재할지(계획은 parser-kics 의 `plans/`, 미적용) ③ 스위스리 KR1102 2026.1Q ILP 합계(인쇄 합계가 Indirect-Par 행 제외) 파생 적재 vs 등재 ④ 소진율·전망 3시트의 임시 비공개 해제 시점·유료화 설계 ⑤ `자본성증권발행현황` 시트의 기본/보완 인정액 열(한도 충전 산식 기반)을 공개로 둘지 ⑥ 메리츠·흥국생명 「기발행 후순위채무」 차감 수정(도넛 철회로 보류: 0.2→30.8·10.6→37.0) ⑦ 흥국생명 2025.4Q 항목 6 outlier(1,020 대 2,796)·한화생명 항목 54(17,932 대 원장 14,711) 별건 점검 ⑧ CSM 워터폴 대 ILP 기준 차이 룰 설계(Opus 몫; 입력·허용오차·예외 형태는 validation 메모) ⑨ 법정준비금 R-RSV-4 미배선 ⑩ `RS1/RS2/RS5_EXCEPTIONS` 이전 ⑪ 77MB loss_ratio 이력 blob(파일은 `.json.gz` 1MB 로 줄임; 이력 정리·LFS 는 보류, 강제 push 금지) ⑫ `downstream_kpis.json` 은 옛 상각 스케줄 정정(`cf66dce`) 미반영 213칸이 어긋나 있어 재빌드 보류(어느 HTML 도 안 읽음).
  전체 표: `data/disclosure/_meta/final_validation_runlog_20261011.md`. 밤샘 스윕 지시·진행 상세는 `docs/todo_archive_root.md` 맨 위.
- [ ] **신종자본증권·후순위채 분류 전수조사(내부, owner 2026-10-12)** — 화면에는 쓰지 않는다. parser-kics 진행 중 `inbox/parser/20261012T1230Z…`, 산출 `data/_derived/capital_securities_classification_census_20261012/`(원문 확정/시계열 추정/불명 3단계, 기존 등재부 `data/bonds/capital_tier_registry.json` 과 불일치 목록).
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
