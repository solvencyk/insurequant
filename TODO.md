# Insurequant TODO — cross-stage

> 갱신 2026-10-24 · 사실(게이트·inbox·커버리지)은 `scripts/status_report.py --fast` 가 정본이고, 이 파일은 의도만 적는다.
> stage 별 TODO·프롬프트·이력 위치는 `CLAUDE.md` §1. 밀린 Status·끝난 항목은 `docs/todo_archive_root.md` 맨 위에 있다(2026-10-24 정리 포함).

## Status (최신 3개)

- **2026-10-24 이웃 옛 판 칸 점검 1~4차 적재·배포 완료(branch push `d58d0852` 게이트 통과 · main `8eb01df`, 라이브 6파일 바이트 일치 · build_id `74a9353f` · 콘솔 오류 0).**
  parser `fc41f505`·`a20976cf`·`fb3960f9`·`f25ed8b8`(22~25차): ABL·동양·현대해상·한화생명·NH농협손보·DB생명·농협생명·KB라이프·KB손보 PL 값 174칸 + 단일분기 215칸, 롯데 CSM 2023.4Q 단일분기 3칸 비움(CSM `null_dangi` 장치 신설), 박제·핀·잔차·예외 0, 독립 재독 통과.
  publishing `74a9353f`·`d58d0852`: xlsx `손익분해PL` 389 · `CSM워터폴` 3 · `panel_compare` 2값 · public_exports. 화면 노출은 IFRS17.html 3번 패널 44셀뿐(compare·index 0).
  남은 것: owner 결정 5건(아래 「owner 결정 대기(2026-10-24)」) · KDB생명 재적재 · 단일분기 항등식 게이트(`TODO_validation.md`). 경위 `docs/changelog_parser_ifrs17.md` 22~25차 · `docs/changelog_publishing.md` 2026-10-24.
- **2026-10-23 최신 비교열 적재 3묶음 배포 완료(READY-25 · 21버킷 → main `72999c88`, owner 결정 D1~D3 4사 → main `7e00a62a`; 라이브 9파일 바이트 일치 · build_id `0d10810a` → `cf67ce7e`).**
  parser `5419a817`(11사 21버킷 PL 값 84 + 단일분기 110) · `afea4342`(READY-25: 9사 PL 440 + CSM 55, KB라이프 abs() 부호 결함 수정) · `b1187788`(KB라이프·롯데·ABL·현대해상 FY2023 PL 209 + CSM 58). validation `d8899bd9`(죽은 등재 7줄 철거 + `PL_OCI_VS_BS_AOCI` 공란 계수 수정) · `90be97e7`(롯데 FY2023 WFY 면제 등재, owner D2).
  KDB생명 KR0072 는 3Q·4Q 가 연결 기준 혼합이라 owner 결정(10-23)으로 보류(HEAD 값 유지). publishing: xlsx READY-25 분 `CSM워터폴` 132 · `손익분해PL` 1,045 · `신계약CSM배수` 20, 4사 분 124 · 466 · 24 + NB 마스터 셀 단위 갱신(`0d10810a` · `cf67ce7e`).
- **2026-10-22 교보생명 KR0073 재작성 기준 적재 · 7사 19버킷 최신 비교열 · jp 레인 분리 배포 완료(main `1a73d4c2` → `66af419c` → `80ba3c1d`, 라이브 바이트 일치 · build_id `5f818b59` → `9dfd28f9` → `acdb2fe9`).**
  교보: parser `3e53aef8`(CSM·PL 한 기준) · `5f818b59`(2023.3Q 단일분기) · `e01f1395`(OCI 13칸) · `59e6e459`(BS 2023.4Q·ILP), validation `9f69ffcf`(`tax22_src` 룰이 최신 비교열 판 인정). 7사 19버킷 `acdb2fe9`. jp 레인은 `da2c8572` 로 이 브랜치에서 제거(`lane/jp`·`../iq_jp`), 배포 스크립트에 `--only <prefix>` 추가(`2fa7a046`).
  남은 것: 교보 BS 티어 B/C/ALT 보류 · 단일분기 이음매 후보 4칸(`TODO_parser_ifrs17.md`).

## 열린 일

- [ ] **owner 결정 대기(2026-10-24, 모두 아직 결정되지 않음)** — 근거·선택지는 `TODO_parser_ifrs17.md` 열린 일.
  - ① KDB생명 KR0072 재적재: A(2023.3Q·4Q 12칸은 HEAD 별도 값 유지 + 3Q 단일분기 6칸 `null_dangi`) / B(FY2023 6항목을 연결로 통일) / C(칸 단위로 비움), parser 의견 A. 재적재 때 항목 23 BLIND 재선언을 같은 커밋에 묶고 티켓 `1255Z`(항목 5·6·9·10·11)도 같은 라운드에 옮긴다. parser 티켓 `20261023T1255Z` · `20261023T1320Z` 는 열려 있고 지금은 HEAD 값이 유지된다.
  - ② KB라이프 KR0099 2024.1Q~3Q CSM 연쇄: 최신 비교열로 옮기면 연쇄가 안 닫혀 data_contract RED 2 → 8(`CSM_CONTINUITY_FY_BOUNDARY` 3 + `CSM_AMORT_IDENTITY_BREAK` 3) → 게이트 면제·박제를 등재할지.
  - ③ 흥국화재 KR0005 PL 항목 16 2024.3Q·4Q 2칸: 값이 빌더 소스와 같아 gold 로 실으면 마스크 칸이 돼 원장 박제 2건이 필요하다.
  - ④ 동양 KR0087 재보험 항목 9·10 부호 규약: 생산은 −|값|, owner gold(2024.4Q·2025.1Q)는 순자산(부채) 관점 인쇄 부호를 뒤집은 값.
  - ⑤ 동양 2024.4Q 항목 11 = 5,758 이 항목 8 과 같다(owner gold 12 가 이를 끼고 닫힘). 2025.1Q gold 11(3,361)·12 와 같이 재검토.
  - 같은 계열 별건: KB손보 KR0010 항목 16 원문 6칸(2024.3Q~2025.4Q)은 싣으려면 새 박제 6건이 필요하다(티켓 `20261024T0100Z` 는 resolved, 결정만 남음).
  - 그 밖에 열려 있는 것: 단일분기 항등식 게이트(지금 켜면 RED 94, `TODO_validation.md`) · 교보 BS 티어 B/C/ALT 보류(`TODO_parser_ifrs17.md`) · 이웃 칸 점검에서 손댄 칸의 약 28% 는 비교하지 못했다(3,703칸 중 67% 비교, 2025.3Q 제외 71.9%; 근거 `data/_derived/remaining_20261022/e25_followups/sweep_neighbors*/`).
- [ ] **26년 3분기 업데이트 안내 팝업(owner 2026-10-16, 문구 승인 2026-10-19; main 배포 `f96f06b0` 완료, 10-31 전에는 안 뜸)** — `theme.js` 맨 위 `NOTICE`(id 2026-3Q · owner 문구 네 줄 그대로 · **showFrom 2026-10-31 · hideAfter 2026-12-31**). 방문자 로컬 날짜 기준이라 한국 0시 동시 점등이 필요하면 별도 처리. 5페이지 · 브라우저당 1회 · 분석 호출 없음 · 새 배포 파일 없음. `tests/regression_*.py` 3종은 팝업이 켜지는 기간에 `iq_notice_seen=2026-3Q` 사전 주입 필요. 다음 분기는 `NOTICE` 의 id · 날짜 · 문구만 바꾼다.
- [ ] **reach out(owner 2026-10-16)** — 1차 8통은 2026-10-14 22:15 ~ 10-15 13:00 에 나갔다(Gmail 확인, 대상 기자 6 · 애널리스트 1 · 연구원 1): 극호평 1 · 호평 2 · 무응답 4 · 전송 실패 1, 회신 3건은 모두 이메일 답장. 2차는 10-19 07:30 에 8통(후보 28건 중 소개 7통 = 언론 4 · 증권사 3(전송 성공 6), 인용 기사 감사 1통)이 나갔고 08:07 기준 반송 1(주소 없음) · 회신 0. 후보 파일은 루트 미추적(이메일 포함이라 커밋 금지)이고 발송·회신 현황의 정본은 그 파일 맨 위 표. 남은 것: 반송 1곳 주소 재확인 · 2차 회신이 오면 같은 표에 적고 사업성 평가 2차 입력으로 쓴다.
- [ ] **문서 규칙 잔여(2026-10-19, 2026-10-24 정리)** — 남은 것: `docs/roadmap.md`·`docs/strategy-monetization.md`(5월 스냅샷) 갱신은 사업성 평가 2차와 함께. 해소분은 `docs/todo_archive_root.md` 맨 위.
- [ ] **손해율 가정 구분 단위 비교 — validation 티켓만 남음(owner 2026-10-16)** — 구현·검증·배포는 끝났다(main `f96f06b0` · `5221a1b4`, 전문 `docs/todo_archive_root.md` 맨 위). 열린 것: validation 티켓 `inbox/validation/20261019T0200Z…` — 카카오페이손보 잎 합 85.7 대 공시 합계 행 100.0(한 칸 14.3pp)과 이상치 4건 원문 대조. 조사 `docs/loss_ratio_comparable_unit_20261019.md`.
- [ ] **접근성 감사 잔여(owner 2026-10-19 「접근성 추천대로」)** — C1 · C2 · C3 · C4 · C6 구현·검증 완료(main 배포 `5221a1b4` 완료, 티켓 `20261019T1400Z` · `docs/a11y_baseline.md` §5e). **하지 않기로 한 것: C5 · C7 · C18(차트 색).** 2차(owner 2026-10-19 「C8~C17 진행」): C8 · C9 · C10 · C11 · C12 · C13 · C14 · C15 · C17 구현·독립 검증 완료(push `7fc4971f` 풀 훅 gate-clear · main 배포 `3a91a4ea` 완료, 라이브 4파일 바이트 일치). 열림: C16 터치 대상 크기(WCAG 2.1 대 2.2 목표를 owner 가 정해야 함), C10 의 「링크 없이 Tab 15번 이하」(링크 쓰면 3번; 레일을 한 정지점으로 묶으려면 방향키 탐색 설계 필요), 선택 상자 테두리 1.27:1(범위 밖), IFRS17 다크 모드 삼성 키컬러 선 1.59:1(색 변경이라 owner 승인 사항).
- [ ] **사업성 평가 1차(owner 2026-10-16, 2026-10-18 완료)** — `docs/business_assessment_20261018.md`(독립 검수로 근거 없는 주장 정정). 결론: reach out 효과는 아직 판단 불가(호의적 반응 3, 모두 이메일 답장이고 인용·링크 약속 없음, 연락 이후 유입 측정 0; 10-19 조선비즈 10-18 기사가 인슈어퀀트를 출처로 인용 — 소개 메일 명단 밖 매체), 방명록 신규는 연락 이전부터 줄어든 추세(초기 3주 주 4.7건 → 최근 3주 2.3건), 병목은 노출이라는 가설. GA4·서치콘솔 수치는 이 환경에서 못 읽는다 — owner 가 주별 신규 이용자(첫 사용자 소스/매체별)·발송 매체 도메인 세션·서치콘솔 노출/클릭을 주면 2차를 돌린다. 실제 발송일은 Gmail 로 확인했고(1차 10-14 22:15 ~ 10-15 13:00, 2차 10-19 07:30) 평가 문서의 reach out 집계도 그 값으로 정정했다. 발송 링크에 utm 을 붙일지도 결정 필요.
- [ ] **owner 결정 대기 · 별건(2026-10-12 저녁 목록의 남은 것, 2026-10-24 정리)** — 해소된 것과 원문은 `docs/todo_archive_root.md` 맨 위.
  - ② `자본성증권발행현황` 공개본의 `비고`(「10%/15% 판정 미확정」 전 행 동일 문구)·`출처`(내부 파일 경로) 열을 뺄지(`TODO_publishing.md` 공개 다운로드 잔여 문구 4건과 같은 건)
  - ④ 흥국생명 2025.4Q 항목 6 outlier(1,020 대 2,796)·한화생명 항목 54(17,932 대 원장 14,711) 별건 점검
  - ⑤⑥⑦ CSM 워터폴 대 ILP 룰 설계 · 법정준비금 R-RSV-4 미배선 · `RS1/RS2/RS5_EXCEPTIONS` 이전은 validation 몫이라 `TODO_validation.md` 에만 둔다
  - ⑧ 77MB loss_ratio 이력 blob(파일은 `.json.gz` 1MB 로 줄임; 이력 정리·LFS 는 보류, 강제 push 금지)
  - ⑨ `downstream_kpis.json` 은 옛 상각 스케줄 정정(`cf66dce`) 미반영 213칸이 어긋나 있어 재빌드 보류(어느 HTML 도 안 읽음)
  - ⑩ 사전 push 훅이 길다 — 배포 건조 실행 시험이 시험당 5~10분(PC 의 git 호출이 호출당 약 3초) → 원인(워킹트리 크기·Defender)·시험 경량화 검토
  전체 표: `data/disclosure/_meta/final_validation_runlog_20261011.md`.
- [ ] **신종자본증권·후순위채 분류 전수조사(내부, owner 2026-10-12)** — 화면에는 쓰지 않는다. 1·2차 분류 완료(parser-kics 30회차, 집계 대상 124건 전부 분류, 마스터·등재부 변경 0; 티켓 `20261012T1230Z`·`20261012T2000Z` 는 inbox/_resolved). 후속(원문 대조·2026.3Q 신규 발행)은 `TODO_parser_kics.md`. 산출 `data/_derived/capital_securities_classification_census_20261012/`(원문 확정/시계열 추정/불명 3단계, 기존 등재부 `data/bonds/capital_tier_registry.json` 과 불일치 목록).
- [ ] **신규 도메인: 채널별 유지율 · 손해율 추이 + 사별 비교 기능(owner 팀장 요청 2026-10-07)** — 추출은 끝났다(명세 티켓 3개 `inbox/_resolved/20261007T0*`, 마스터 유지율·손해율 적재, compare.html 라이브). 남은 것: 지표 컬럼 밀림 티켓 2건(`inbox/parser/20261007T1001Z` · `20261007T1300Z`)과 비교 기능 확장을 위한 owner 의 핵심 지표 목록.
  인수인계 `docs/archive/handoff_20261007_persistency_lossratio_compare.md`(상태·census·남은 순서).
- [ ] **재보사 K-ICS 스윕(KR1101~KR1108) 후속(2026-10-11 완료·push, 계약 `docs/archive/handoff_20261008_reinsurer_pipeline.md`)** — 남은 것:
  - ① 스위스리아시아 2023.2Q 는 새 완성본 전기 열로 적재 가능(새 RED 0)·2023.3Q 는 새 RED 2(룰 4·`8_life_census`) — owner 결정, 적재하면 census 면제 등재를 풀어야 함
  - ② 퍼시픽 2023.1Q·2Q 는 비율만 인쇄돼 버킷 불가
  - ③ 퍼시픽 금리민감도 2024.4Q·2025.2Q 는 MD 에 있고 마스터에 없음(12행)·KR1107 비율 정밀값 4칸
  - ④ **기존 6셀 IRR 잔액 시나리오 열 뒤바뀜**(카카오페이손보 2023.2Q·2023.4Q·2024.4Q·2025.2Q·2026.2Q, 하나손보 2025.2Q — 라이브에 이미 있음, 하나손보 2025.2Q 자산듀레이션 2.25 대 원문 열 순서 4.78) → 고칠지 owner
  - ⑤ 수작업 정정 8쌍은 추출기를 다시 돌리면 되살아남(추출기 보강 티켓)
  - ⑥ 같은 분기에 raw PDF 가 둘이면 일부 도구가 옛 파일을 고름
  - ⑦ `RS1/RS2/RS5_EXCEPTIONS` 이전 여부는 `TODO_validation.md`(「기존 키 집합 등재부를 박제 장치로 옮길지」)와 같은 건이라 거기서만 다룬다.
- [ ] **IFRS17 섹션 3 콤보 후속 잔여(2026-10-24 정리)** — 추출기 공통 결함 7개(원 ⑦; 2026-10-11 ILP 라운드 3 에서 일부 보강했으나 남은 것이 무엇인지는 이번 정리에서 확인하지 못함, 런로그 `data/disclosure/_meta/ilp_backfill_pre2025_runlog.md` §11~§16). 나머지 ①~⑥·⑧ 은 적재·결정으로 끝났다(`docs/todo_archive_root.md` 맨 위).
- [ ] **PC 부하 실측(owner 2026-10-10, 틈날 때)** — docling 변환 1건의 최대 메모리·소요를 에이전트가 쉬는 시간에 재서 보고. 현재 RAM 15.5GB(증설 불가)·8코어, owner 희망 RAM 32GB·12코어(즉시 교체 아님). 한도: 동시 에이전트는 그때 메모리·CPU 여유를 보고 정함(보통 4개 이내) · docling ≤2.
- [ ] **2026.3Q 정기경영공시 라운드** — 2Q 는 8/29~31 에 게시됐으니 3Q 는 11월 말 예상. 절차 `docs/flows/kics_quarterly_round.md`
  (라벨·스크립트를 3Q 로 바꿔 쓴다). owner 가 부르기 전에는 시작하지 않는다.
- [ ] **J-ESR 10월 말 재census**(기한 2026-10-31 직후) → `lane/jp` 브랜치 워크트리 `../iq_jp` 의 `TODO_jp.md`. 이 브랜치에는 jp 파일이 없다(`CLAUDE.md` §1).
- [ ] **inbox 열린 티켓** — 건수는 `status_report.py --fast` 로 센다(2026-10-24 정리 뒤 9건: parser 7 · validation 1 · publishing 1). parser 7건 = KDB 보류 2건(`20261023T1255Z` · `1320Z`) + 일부 처리된 3건(PL 부모 결측 · item4/12/13 미러 오염 · 금리민감도 phase) + 아직 손대지 않은 2건(지표 컬럼 밀림 `20261007T1001Z` · `1300Z`). publishing `20260923T1130Z`(자본증권 후속) · validation `20261019T0200Z`(손해율 잎 합 대 총계)도 열려 있다. 이날 BS/PL 공란 채움 3건 · IFRS17 적용 독립검수 후속 · a11y 는 잔여를 `TODO_parser_ifrs17.md` · `TODO_designer.md` 로 옮기고 종결했다. 남은 일은 각 티켓 맨 아래.
- [ ] **KR0004 2025.4Q 비교 단절 주의** — 같은 계열(예별 = 구 MG)이지만 2025-09-03 계약이전으로 DART 와 경영공시 규모가 52배 다르다. → `TODO_parser_ifrs17.md`.

## 보류 (재개 조건이 오면 연다)

- F18 IR factsheet 정형화 + DART↔IR 교차검증 — owner 2026-08-30 "꼭 필요할 때만". raw 130파일, parsed 6파일.
- F13 재보험 영업 지표 — downloader F8(손보협회 비교공시) 수집이 선행.
- 중장기 제품·수익화 트랙 — `docs/roadmap.md`.
- 일본 사이트 오류 제보 위젯(`jp/report-widget.ja.js`)의 내부 접속 제외 — owner 2026-10-19 보류. jp 는 `lane/jp`(`../iq_jp`)에서만 작업한다.

## 정책 (cross-stage)

| # | 결정 | 날짜 |
|---|---|---|
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료** | 2026-05-24 |
| 5 | API keys: repo root `.env` only (gitignored). Never commit/log key values | 2026-05-24 |
| 6 | Bond Call rule: issue + 5y for ALL bonds. Past 5y = assume `called` (갱신: 콜 지난 미상환분은 `TODO_publishing.md` 2026-09-23) | 2026-05-24 |
| 7 | Pushing: subagent **reports + recommends only**. 라이브 `main` 배포는 owner GO | 2026-05-30 |
| 8 | DART attachments (별첨/감사보고서 zip): **don't fetch**. Body XML has all IFRS17 disclosures | 2026-05-30 |
| 9 | DB손보 제1~5회 신종 = **기본자본형 확정**(owner 「해약환급금준비금 규모가 늘어 보완자본도 늘어난 것 — 기본자본으로 냅둬」). 등재부 유지(소진율 151.6), 재감사 때 다시 플래그하지 않는다 | 2026-10-12 |
| 10 | 보완자본 소진율 분자의 경과조치 기발행분 차감 = **2023년 이전 발행분만**(47사 전체): 차감액 = min(공시 인쇄 항목 53·54, 채권 원장의 2022-12-31 이전 발행 잔액). 티어1 기발행 갈래(항목 53 15%)는 바꾸지 않음. 2026-10-13 에 콜 미경과 잔액으로 통일(메리츠 37.5 · 흥국생명 37.0) | 2026-10-12 |
| 11 | 차트 색 변경 안 함: a11y 감사 C5 · C7 · C18(사별 비교 손해율 선 색 포함) — 값 표에 수치가 같이 표시됨 | 2026-10-19 |

## 참조 (필요할 때만 연다)

- K-ICS 게이트 documented exceptions: `docs/kics_gate_exceptions.md`
- 분기 라운드 절차: `docs/flows/kics_quarterly_round.md`
- Status 이력·정리 전 전문: `docs/todo_archive_root.md`
