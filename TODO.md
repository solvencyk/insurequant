# Insurequant TODO — cross-stage

> 갱신 2026-10-12 · 사실(게이트·inbox·커버리지)은 `scripts/status_report.py --fast` 가 정본이고, 이 파일은 의도만 적는다.
> stage 별 TODO·프롬프트·이력 위치는 `CLAUDE.md` §1. 2026-10-07 정리 전 전문은 `docs/todo_archive_root.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-13 새벽 작업 브랜치 push `5414c81e`(풀 훅 gate-clear) · main 배포 `970259b8` 완료.** owner 결정으로 소진율 도넛·Forward Outlook 복원(발행현황 패널 유지 · 3시트와 루트 JSON 3개 재공개) — 위 오후 「내림」 결정은 번복됨. 신종 분류는 발행사 처리 기준(하나생명·교보 2024-11 기본자본형 · DB손보 기본자본형 확정), 보완자본 분자의 기발행 차감 = 원장의 2022-12-31 이전·콜 미경과 잔액(47사 독립 감사 PASS),
  「최신 공시 직전 컬럼」은 검산이 확실히 닫히는 것만 적용(K-ICS 16블록 65칸 · IFRS17 249셀 · 박제 예외 해제 · 재작성 장부 +29, 독립 검수 일치). 예별·롯데 전망의 가짜 개선 제거(자본잠식 해는 선을 안 그림 · 음수 △).
  배포: owner 취침 중 지시(「라이브 push 까지 쭉」)로 PC 의 격리 sparse 클론에서 `android_push_and_deploy.sh --from-origin --branch fix/csm-product-segmented-columns` 실행(기존 24개 갱신·신규 6개), 라이브 확인 완료(manifest build_id `99c7ead7` · 하나생명 기본자본 238.2 · 메리츠 보완자본 37.5 · 콘솔 오류 0). 별건 follow-up `inbox/parser/20261012T1820Z…`(푸본현대·흥국화재 2023.1Q 1Q 값, 삼성화재 2024.1Q 항목 13·14, 삼성생명 BS 단절). 아침 결정: 흥국화재·악사 콜 경과 방향 · 아이엠라이프 원장(전환우선주·기준일) · 코리안리·농협생명·푸본 4건 분류.
- **2026-10-12 오후 작업 브랜치 push 직전(HEAD `0f143d2` 이후).** owner 결정: K-ICS 소진율 도넛·Forward Outlook 을 화면에서 내림(신종 분류 판단이 들어가는 숫자는 건조하게 못 뽑는다 — 유료화 후보) → 발행연도별 신종·후순위채 누적 막대 + 큼직한 셀 2개(최근 발행금리·총발행액 '23~·가장 가까운 콜 1건), 기본자본소진율·보완자본소진율·자본비율전망 3시트는 다운로드 목록에서 임시로 내림(파일·시트 그대로, `download-survey.js` 주석 해제로 복구).
  공유 버튼 이용 기록(`shares` 탭) 라이브(`deploy/design-20261012`), IFRS17 「보험금 예실차비율」 독립 섹션 + 시트 신설, 재보사 PL 7칸 복원·처브 BS/ILP·분할표·퍼시픽/악사 K-ICS 칸 보정, 손해율 재보사 세그먼트 표준화 + 85MB→1MB(.gz). 남은 것: validation 골든·AIG R3 등재(`T1400Z`) → `git push origin fix/csm-product-segmented-columns`(풀 훅 ≈10분) → owner 폰 배포.
- **2026-10-12 아침 작업 브랜치 push(HEAD `6233594` 이후, 훅 gate-clear).** owner 취침 중 재보사 전면 재스윕: 손해율 가정 7곳(master_loss_ratio +1,904·예실차 37→44사)·PL 투자손익/영업외 +303·BS +49·CSM 계열(RGA·하노버 2025.4Q 등)·자본성증권 재확인(0 이 맞음). 화면: K-ICS 시나리오 컬럼명(공시 이름)·듀레이션 주석 ? 안으로·IFRS17 통합 현황 박스·NB 표·보험금 예실차비율 표·모바일 재보험 접기. 훅 소요 26분→약 11분(PDF 텍스트 캐시).
  라이브 `main` 배포는 owner 폰(`bash scripts/android_push_and_deploy.sh --from-origin --branch fix/csm-product-segmented-columns`, `bash` 필수). 결정 대기는 아래 「owner 결정 대기」.

## 열린 일

- [x] **DB손보 제1~5회 신종 = 기본자본형 확정(owner 2026-10-12 밤).** 독립 감사의 X 검정(2026.1Q+2Q 합산 재분류 증가 +8,915 대 기본자본형 기대 +5,942)이 보완자본형 쪽으로 기울었으나, owner: 「해약환급금준비금 규모가 늘어 보완자본도 늘어난 것 — 기본자본으로 냅둬」. 등재부 유지(소진율 151.6), 뒤집지 않는다(근거 기사 + 이 결정). 재감사 때 이 항목을 다시 플래그하지 말 것.
- [x] **보완자본 소진율 분자의 경과조치 기발행분 차감 = 2023년 이전 발행분만(owner 2026-10-12 밤, 47사 전체).** owner: 「기발행은 그 시점까지 발행한 전체 물량 같다, 2023년 이전 것까지만 소진율 차감」. 구현: 차감액 = min(공시 인쇄 항목 53·54, 채권 원장의 2022-12-31 이전 발행 잔액), 미래에셋·DB생명 개별 예외는 일반 규칙으로 흡수. 기대 변화 메리츠 0.2→32.2·흥국생명 10.6→37.0·농협생명 18.8→21.1·농협손해 103.9→102.8(감사 실측). publishing(`a8ba3ca`) 진행, 티어1 기발행 갈래(항목 53 15%)는 이번에 바꾸지 않고 보고만.
- [ ] **owner 결정 대기(2026-10-12 저녁 갱신)** — 해소됨: 라이나 CSM 2023.1Q·2Q 보류 유지(승인), 뮌헨 KR1101 2026.2Q 항목 50·51(=0 파생)·52 적재(`33635d1`), 스위스리 KR1102 2026.1Q ILP 합계 전체 행 합 적재(`4147fc1`), AIG KR0029 2024.4Q R3 등재(`470e146`), 소진율·전망 3시트 비공개(`3c83f58`: 공개본·루트 JSON 3개를 배포 시 main 에서 `git rm`, 저장소에는 보관), `자본성증권발행현황` 공개본에서 한도·인정액 계산 열 7개 제외(`3c83f58`).
  남은 것: ① (해소 2026-10-13) 소진율·전망 재공개 완료(비공개 목록 비움, 메커니즘 유지) ② `자본성증권발행현황` 공개본의 `비고`(「10%/15% 판정 미확정」 전 행 동일 문구)·`출처`(내부 파일 경로) 열을 뺄지 ③ (해소 2026-10-13) 기발행 차감 = 원장 2022-12-31 이전·콜 미경과 잔액으로 통일(메리츠 37.5 · 흥국생명 37.0) ④ 흥국생명 2025.4Q 항목 6 outlier(1,020 대 2,796)·한화생명 항목 54(17,932 대 원장 14,711) 별건 점검 ⑤ CSM 워터폴 대 ILP 기준 차이 룰 설계(Opus 몫; 입력 `CSM_waterfall.json` 기말 CSM·`insurance_liability_portfolio.json` 항목 3+6, 허용오차 `max(1억, 0.5%)`, 재작성 칸 YELLOW·계약이전 칸 값 박제, 롯데 군집 칸별 분류 — `TODO_validation.md`) ⑥ 법정준비금 R-RSV-4 미배선 ⑦ `RS1/RS2/RS5_EXCEPTIONS` 이전 ⑧ 77MB loss_ratio 이력 blob(파일은 `.json.gz` 1MB 로 줄임; 이력 정리·LFS 는 보류, 강제 push 금지) ⑨ `downstream_kpis.json` 은 옛 상각 스케줄 정정(`cf66dce`) 미반영 213칸이 어긋나 있어 재빌드 보류(어느 HTML 도 안 읽음) ⑩ 사전 push 훅이 길다 — 배포 건조 실행 시험이 시험당 5~10분(PC 의 git 호출이 호출당 약 3초) → 원인(워킹트리 크기·Defender)·시험 경량화 검토.
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
