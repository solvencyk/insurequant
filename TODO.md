# Insurequant TODO — cross-stage

> 갱신 2026-10-19 · 사실(게이트·inbox·커버리지)은 `scripts/status_report.py --fast` 가 정본이고, 이 파일은 의도만 적는다.
> stage 별 TODO·프롬프트·이력 위치는 `CLAUDE.md` §1. 2026-10-07 정리 전 전문은 `docs/todo_archive_root.md` 맨 위에 있다.

## Status (최신 3개)

- **2026-10-19 밤 손해율 비교 단위 선택기 · 접근성 5건 · 오류 제보 내부 접속 제외 · 반올림 통일 완료(push `a8d9f193` 풀 훅 gate-clear · main 배포 `5221a1b4` 완료, 라이브 7파일 바이트 일치 · compare/IFRS17 라이브 단위 선택기 확인).** 비교 단위 선택기(compare · IFRS17 8절: 생보 4 · 손보 4 · 재보 4 단위, 기본 생보 Non-Par 무배당건강 · 손보 Non-Par 무배당상해, 단위 없는 회사는 빈 칸+사유, 위험보험료 100억원 미만 칸 흐림), `report-widget.js` 내부 방문 수집기 제외, 접근성 C1 ? 팝오버 마우스 유예 · C2 포커스 · C3 입력창 테두리 · C4 다크 placeholder · C6 모바일 선 표식(C5 · C7 · C18 차트 색은 owner 가 하지 않기로).
  데이터: 백만원 공시사 위험보험료가 100배 작게 실리던 이중 환산 정정, 손해율 반올림 half-up 통일(**compare 손해율·중앙값 93칸이 0.1 올라 IFRS17 표시와 일치**), `loss_curve.alt_co`, 마스터 대조 검산 `tests/test_loss_unit_panels_vs_master.py`(prepush 배선). 독립 검증: 데이터 5,328칸 · UI 727상태 · 배포본 회귀 82건 위반 0.
  남은 것: C16 · 일본 오류 제보 위젯 제외(보류) · 변액사망 n/a 문구를 ? 팝오버로 옮길지. 이 후속 워크플로우는 약 8시간이 걸렸다(경위 `docs/claude-changelog.md`).
- **2026-10-19 owner 승인 반영 · 후속 처리 완료(작업 브랜치 push `8851145b` 풀 훅 gate-clear · main 배포 `f96f06b0` 완료, 라이브 6파일 바이트 일치 · compare/IFRS17 라이브 기본 Non-Par 확인).** 팝업 시작일 10-31 · 손해율 기본 Non-Par · IFRS17 현재가치 반올림 수정 · 다운로드 방명록 내부 접속 제외 · 문서 결정 7건(Status 5줄 · xlsx 단서 · 별첨/손보 경로 정정 · archive 이동 · 동시 에이전트/배포 주체 규칙) · compare·privacy 접근성 감사 18건.
  규칙(owner 2026-10-19): 동시 에이전트 수는 메모리·CPU 여유로 정함. main 배포는 기본이 오케스트레이터 직접(구두 GO 뒤), push 가 막히면 2회 시도 뒤 owner 에게 Termux 명령·배치파일 제시. owner 결정 대기: 구분×포트폴리오 평면 8개 단위 선택기 · a11y 색 변경 5건 · 10-13 이월 4건.
- **2026-10-18 TODO 일괄 처리 완료(10-19 에 push·main 배포까지 완료).** 손해율 가정 구분 선택기(compare·IFRS17 8절) · 3분기 안내 팝업(theme.js) · 작업 폴더 정리(격리 1259개 10.5GB, git status 체감 5초 → 1초 미만) · 문서 낡은 서술·깨진 참조 113건 정정 · 사업성 평가 보고서 · reach out 후보 28건(미추적 파일, 당시 발송 안 함. 이 중 7건은 10-19 07:30 에 소개 메일이 나감).
  독립 검증: 손해율 곡선은 마스터 재계산과 최대 0.05pp 차이(IFRS17 현재가치 5칸만 0.054pp, 이중 반올림), 팝업은 5페이지 위반 0. 남은 것: 현재가치 이중 반올림(publishing)·스위스리 Indirect-Par 21~25년 159.27 원문 확인(parser)·문서 규칙 충돌 owner 판단(아래 「owner 결정 대기」). 푸시 전 풀 훅을 미리 돌려 통과 확인(RED 0 · 오프라인 시험 951 통과, 5분 46초 포함 약 11분) — 푸시 때 같은 훅이 다시 돈다. 배포는 owner GO 뒤.

## 열린 일

- [x] **정리 fan-out 1차(owner 2026-10-16, 2026-10-18 완료·로컬 커밋)** — 캐시·빈 폴더 43개 삭제, 1259개(10.5GB: pytest 임시 폴더 4.4GB · 게이트 보고서 6.3GB · `data/_derived` 111MB 등)를 `C:/Users/sangwook.cho/insurequant_quarantine_20261018`(MOVED.json·README.txt)로 이동(삭제 아님), 추적 백업 2개 제거, 문서 낡은 서술·깨진 참조 113건 정정(보관본·이력은 무수정 확인). 격리 폴더는 owner 가 직접 삭제함(2026-10-19). 남긴 것: `artifacts/kics_validation/report_*.json` 53개(문서가 이름을 언급), `scripts/_probes` 임시 이름 추적 스크립트 21개, 개인 파일. 문서끼리 규칙이 어긋난 곳은 바로 아래 항목.
- [ ] **문서 규칙 잔여(2026-10-19)** — 해소: 동시 에이전트 수(메모리·CPU 여유로 정함) · 배포 주체/경로(기본 오케스트레이터 직접, 막히면 Termux·배치파일 제시) · 별첨 수집 범위(경영공시 별첨 수집, DART 별첨 금지) · 손보 수집 경로(2026.2Q 는 사별 사이트 스크립트) · master xlsx 문구(`CLAUDE.md` §8 에 sync 스크립트의 수식·피벗 REFUSE 단서 추가) · Status 항목 5줄 · 끝난 `handoff` 2개와 `mockups/compare` 를 `docs/archive/` 로. 남은 것: `docs/roadmap.md`·`docs/strategy-monetization.md`(5월 스냅샷) 갱신은 사업성 평가 2차와 함께, compare·privacy 접근성 점검 결과 반영(`docs/a11y_baseline.md`).
- [ ] **26년 3분기 업데이트 안내 팝업(owner 2026-10-16, 문구 승인 2026-10-19; main 배포 `f96f06b0` 완료, 10-31 전에는 안 뜸)** — `theme.js` 맨 위 `NOTICE`(id 2026-3Q · owner 문구 네 줄 그대로 · **showFrom 2026-10-31 · hideAfter 2026-12-31**). 방문자 로컬 날짜 기준이라 한국 0시 동시 점등이 필요하면 별도 처리. 5페이지 · 브라우저당 1회 · 분석 호출 없음 · 새 배포 파일 없음. `tests/regression_*.py` 3종은 팝업이 켜지는 기간에 `iq_notice_seen=2026-3Q` 사전 주입 필요. 다음 분기는 `NOTICE` 의 id · 날짜 · 문구만 바꾼다.
- [ ] **reach out(owner 2026-10-16)** — 1차 8통은 2026-10-14 22:15 ~ 10-15 13:00 에 나갔다(Gmail 확인, 대상 기자 6 · 애널리스트 1 · 연구원 1): 극호평 1 · 호평 2 · 무응답 4 · 전송 실패 1, 회신 3건은 모두 이메일 답장. 2차는 10-19 07:30 에 8통(후보 28건 중 소개 7통 = 언론 4 · 증권사 3(전송 성공 6), 인용 기사 감사 1통)이 나갔고 08:07 기준 반송 1(주소 없음) · 회신 0. 후보 파일은 루트 미추적(이메일 포함이라 커밋 금지)이고 발송·회신 현황의 정본은 그 파일 맨 위 표. 남은 것: 반송 1곳 주소 재확인 · 2차 회신이 오면 같은 표에 적고 사업성 평가 2차 입력으로 쓴다.
- [ ] **손해율 가정 구분 단위 비교(owner 2026-10-16)** — ① 구현 완료·main 배포 `f96f06b0` 완료: 구분 선택기(합계 · Non-Par · Indirect-Par · Direct-Par, 공시 이름 그대로), **기본 Non-Par(owner 2026-10-19)**, compare 손해율 카드 · IFRS17 8절. IFRS17 현재가치 이중 반올림도 고침(빌더 `viz_build_persistency_lossratio_panels.py`, `panel_loss_ratio.json` 206 → 282KB, 전 칸 표시값 차이 0.05pp 이하, 티켓 `20261018T0700Z` answered). 단일 구분 회사도 합계와 그 구분 두 선택지를 보인다.
  ② 조사 `docs/loss_ratio_comparable_unit_20261019.md`(독립 검증 통과): Non-Par 한 줄만으로는 생보가 아직 왜곡(건강 95 대 사망 67, 회사별 비중 차이로 선이 중앙 4pp 어긋남). 최소 비교 단위 = 구분×포트폴리오 한 줄(생보 4개: Non-Par 건강 · Non-Par 사망 · Indirect-Par 사망 · Direct-Par 변액사망 / 손보 4개: Non-Par 상해 · 질병, Indirect-Par 상해 · 질병), 이 단위에서 비중 어긋남 중앙 0.1~0.3pp. 스위스리 Non-Par 는 4개 하위가 섞여 16년 이후 구성 효과가 최대 △20pp 라 재보사는 세그먼트×포트폴리오로 따로 봐야 한다.
  ③ 구현·검증 완료(owner 2026-10-19 「선택기는 조사 추천대로」; main 배포 `5221a1b4` 완료): 평면 단위 12개, 기본 생보 Non-Par 무배당건강 · 손보 Non-Par 무배당상해, 단위 없는 회사는 빈 칸+사유, 100억원 미만 칸 흐림. ④ validation 티켓 `20261019T0200Z`: 카카오페이손보 잎 합 85.7 대 공시 합계 행 100.0(한 칸 14.3pp), 이상치 4건 원문 대조.
- [ ] **다운로드 방명록 내부 접속 제외(owner 2026-10-19 승인; 구현·검증 완료·main 배포 `f96f06b0` 완료)** — `download-survey.js` 가 `iq_internal=1`(주소 또는 localStorage)이면 수집기로 행을 보내지 않는다. 일반 방문은 종전과 동일. 오류 제보(`report-widget.js`)도 같은 제외 구현·검증 완료(owner 2026-10-19, main 배포 `5221a1b4` 완료). 일본 사이트 `jp/report-widget.ja.js` 적용은 보류(owner 2026-10-19).
- [ ] **접근성 감사 잔여(owner 2026-10-19 「접근성 추천대로」)** — C1 · C2 · C3 · C4 · C6 구현·검증 완료(main 배포 `5221a1b4` 완료, 티켓 `20261019T1400Z` · `docs/a11y_baseline.md` §5e). **하지 않기로 한 것: C5 · C7 · C18(차트 색).** 2차(owner 2026-10-19 「C8~C17 진행」): C8 · C9 · C10 · C11 · C12 · C13 · C14 · C15 · C17 구현·독립 검증 완료(push `7fc4971f` 풀 훅 gate-clear · main 배포 `3a91a4ea` 완료, 라이브 4파일 바이트 일치). 열림: C16 터치 대상 크기(WCAG 2.1 대 2.2 목표를 owner 가 정해야 함), C10 의 「링크 없이 Tab 15번 이하」(링크 쓰면 3번; 레일을 한 정지점으로 묶으려면 방향키 탐색 설계 필요), 선택 상자 테두리 1.27:1(범위 밖), IFRS17 다크 모드 삼성 키컬러 선 1.59:1(색 변경이라 owner 승인 사항).
- [ ] **사업성 평가 1차(owner 2026-10-16, 2026-10-18 완료)** — `docs/business_assessment_20261018.md`(독립 검수로 근거 없는 주장 정정). 결론: reach out 효과는 아직 판단 불가(호의적 반응 3, 모두 이메일 답장이고 인용·링크 약속 없음, 연락 이후 유입 측정 0; 10-19 조선비즈 10-18 기사가 인슈어퀀트를 출처로 인용 — 소개 메일 명단 밖 매체), 방명록 신규는 연락 이전부터 줄어든 추세(초기 3주 주 4.7건 → 최근 3주 2.3건), 병목은 노출이라는 가설. GA4·서치콘솔 수치는 이 환경에서 못 읽는다 — owner 가 주별 신규 이용자(첫 사용자 소스/매체별)·발송 매체 도메인 세션·서치콘솔 노출/클릭을 주면 2차를 돌린다. 실제 발송일은 Gmail 로 확인했고(1차 10-14 22:15 ~ 10-15 13:00, 2차 10-19 07:30) 평가 문서의 reach out 집계도 그 값으로 정정했다. 발송 링크에 utm 을 붙일지도 결정 필요.
- [x] **DB손보 제1~5회 신종 = 기본자본형 확정(owner 2026-10-12 밤).** 독립 감사의 X 검정(2026.1Q+2Q 합산 재분류 증가 +8,915 대 기본자본형 기대 +5,942)이 보완자본형 쪽으로 기울었으나, owner: 「해약환급금준비금 규모가 늘어 보완자본도 늘어난 것 — 기본자본으로 냅둬」. 등재부 유지(소진율 151.6), 뒤집지 않는다(근거 기사 + 이 결정). 재감사 때 이 항목을 다시 플래그하지 말 것.
- [x] **보완자본 소진율 분자의 경과조치 기발행분 차감 = 2023년 이전 발행분만(owner 2026-10-12 밤, 47사 전체).** owner: 「기발행은 그 시점까지 발행한 전체 물량 같다, 2023년 이전 것까지만 소진율 차감」. 구현: 차감액 = min(공시 인쇄 항목 53·54, 채권 원장의 2022-12-31 이전 발행 잔액), 미래에셋·DB생명 개별 예외는 일반 규칙으로 흡수. 기대 변화 메리츠 0.2→32.2·흥국생명 10.6→37.0·농협생명 18.8→21.1·농협손해 103.9→102.8(감사 실측). publishing(`a8ba3ca`) 진행, 티어1 기발행 갈래(항목 53 15%)는 이번에 바꾸지 않고 보고만.
- [ ] **owner 결정 대기(2026-10-12 저녁 갱신)** — 해소됨: 라이나 CSM 2023.1Q·2Q 보류 유지(승인), 뮌헨 KR1101 2026.2Q 항목 50·51(=0 파생)·52 적재(`33635d1`), 스위스리 KR1102 2026.1Q ILP 합계 전체 행 합 적재(`4147fc1`), AIG KR0029 2024.4Q R3 등재(`470e146`), 소진율·전망 3시트 비공개(`3c83f58`: 공개본·루트 JSON 3개를 배포 시 main 에서 `git rm`, 저장소에는 보관), `자본성증권발행현황` 공개본에서 한도·인정액 계산 열 7개 제외(`3c83f58`).
  남은 것: ① (해소 2026-10-13) 소진율·전망 재공개 완료(비공개 목록 비움, 메커니즘 유지) ② `자본성증권발행현황` 공개본의 `비고`(「10%/15% 판정 미확정」 전 행 동일 문구)·`출처`(내부 파일 경로) 열을 뺄지 ③ (해소 2026-10-13) 기발행 차감 = 원장 2022-12-31 이전·콜 미경과 잔액으로 통일(메리츠 37.5 · 흥국생명 37.0) ④ 흥국생명 2025.4Q 항목 6 outlier(1,020 대 2,796)·한화생명 항목 54(17,932 대 원장 14,711) 별건 점검 ⑤ CSM 워터폴 대 ILP 기준 차이 룰 설계(Opus 몫; 입력 `CSM_waterfall.json` 기말 CSM·`insurance_liability_portfolio.json` 항목 3+6, 허용오차 `max(1억, 0.5%)`, 재작성 칸 YELLOW·계약이전 칸 값 박제, 롯데 군집 칸별 분류 — `TODO_validation.md`) ⑥ 법정준비금 R-RSV-4 미배선 ⑦ `RS1/RS2/RS5_EXCEPTIONS` 이전 ⑧ 77MB loss_ratio 이력 blob(파일은 `.json.gz` 1MB 로 줄임; 이력 정리·LFS 는 보류, 강제 push 금지) ⑨ `downstream_kpis.json` 은 옛 상각 스케줄 정정(`cf66dce`) 미반영 213칸이 어긋나 있어 재빌드 보류(어느 HTML 도 안 읽음) ⑩ 사전 push 훅이 길다 — 배포 건조 실행 시험이 시험당 5~10분(PC 의 git 호출이 호출당 약 3초) → 원인(워킹트리 크기·Defender)·시험 경량화 검토.
  전체 표: `data/disclosure/_meta/final_validation_runlog_20261011.md`. 밤샘 스윕 지시·진행 상세는 `docs/todo_archive_root.md` 맨 위.
- [ ] **신종자본증권·후순위채 분류 전수조사(내부, owner 2026-10-12)** — 화면에는 쓰지 않는다. parser-kics 진행 중 `inbox/parser/20261012T1230Z…`, 산출 `data/_derived/capital_securities_classification_census_20261012/`(원문 확정/시계열 추정/불명 3단계, 기존 등재부 `data/bonds/capital_tier_registry.json` 과 불일치 목록).
- [ ] **신규 도메인: 채널별 유지율 · 손해율 추이 + 사별 비교 기능(owner 팀장 요청 2026-10-07)** — 추출 진행 중.
  인수인계 `docs/archive/handoff_20261007_persistency_lossratio_compare.md`(상태·census·남은 순서), 명세는 `inbox/parser/20261007T0*` 티켓 3개.
  비교 기능은 owner 의 핵심 지표 목록 대기.
- [ ] **재보사 K-ICS 스윕(KR1101~KR1108) 후속(2026-10-11 완료·push, 계약 `docs/archive/handoff_20261008_reinsurer_pipeline.md`)** — 남은 것:
  - ① 스위스리아시아 2023.2Q 는 새 완성본 전기 열로 적재 가능(새 RED 0)·2023.3Q 는 새 RED 2(룰 4·`8_life_census`) — owner 결정, 적재하면 census 면제 등재를 풀어야 함
  - ② 퍼시픽 2023.1Q·2Q 는 비율만 인쇄돼 버킷 불가
  - ③ 퍼시픽 금리민감도 2024.4Q·2025.2Q 는 MD 에 있고 마스터에 없음(12행)·KR1107 비율 정밀값 4칸
  - ④ **기존 6셀 IRR 잔액 시나리오 열 뒤바뀜**(카카오페이손보 2023.2Q·2023.4Q·2024.4Q·2025.2Q·2026.2Q, 하나손보 2025.2Q — 라이브에 이미 있음, 하나손보 2025.2Q 자산듀레이션 2.25 대 원문 열 순서 4.78) → 고칠지 owner
  - ⑤ 수작업 정정 8쌍은 추출기를 다시 돌리면 되살아남(추출기 보강 티켓)
  - ⑥ 같은 분기에 raw PDF 가 둘이면 일부 도구가 옛 파일을 고름
  - ⑦ `RS1/RS2/RS5_EXCEPTIONS` 를 새 장치(`rs_pinned_exemptions`)로 옮길지 owner
  - ⑧ 재보사 IFRS17 지표(다음 round, 아래).
- [ ] **재보사 IFRS17 지표 적재(다음 round, owner 2026-10-10)** — CSM 상각 스케줄·가정민감도·요약 PL/BS·4-6-2 포트폴리오. 정찰 `data/disclosure/_meta/reinsurer_ifrs17_scout_20261010.md`(우선순위 ①~④, 감사보고서 CSM 변동표는 변환이 먼저).
- [ ] **IFRS17 섹션 3 콤보 후속(콤보 자체는 2026-10-11 push 완료)** — owner 지시 「이 round 끝나면 나머지 시점 백필 전부」:
  - ① LIC/LRC 백필 2024.1Q~3Q(약 1일, DART 69셀 닫힘)·2023.1Q~3Q(약 0.5일, 경영공시 항목 1~8 은 원천 없음)
  - ② LIC 2단계(단일열 회사 간접 계산값 항목 16·17, 사전시험 105셀 중 28셀 통과)
  - ③ 3단계(라이나 PDF 5셀·처브 3셀·하나손보 별첨·예별 2025.4Q 는 0 을 안 지어 넣음)
  - ④ LIC 검산기가 재작성 3셀에서 사이드카 값을 앵커로 쓰도록(지금 R-LIC1 RED 3, 의도된 결과)
  - ⑤ 포트폴리오 검증기 RED 4(KR0100 R3 3 + KR0029 2024.4Q 「10배 규칙」 1) 판단
  - ⑥ 롯데손보 2026.2Q 항목 9=1 확인
  - ⑦ 추출기 공통 결함 7개
  - ⑧ compare 선 대비 2.1~2.6:1(키컬러 전환과 묶어 owner 확인, `TODO_designer.md`). 사이드카: 2-4 가 LIC 포함인 ABL·KDB생명·푸본현대(`ilp_includes_lic.json`).
- [ ] **PC 부하 실측(owner 2026-10-10, 틈날 때)** — docling 변환 1건의 최대 메모리·소요를 에이전트가 쉬는 시간에 재서 보고. 현재 RAM 15.5GB(증설 불가)·8코어, owner 희망 RAM 32GB·12코어(즉시 교체 아님). 한도: 동시 에이전트는 그때 메모리·CPU 여유를 보고 정함(보통 4개 이내) · docling ≤2.
- [ ] **2026.3Q 정기경영공시 라운드** — 2Q 는 8/29~31 에 게시됐으니 3Q 는 11월 말 예상. 절차 `docs/flows/kics_quarterly_round.md`
  (라벨·스크립트를 3Q 로 바꿔 쓴다). owner 가 부르기 전에는 시작하지 않는다.
- [ ] **J-ESR 10월 말 재census**(기한 2026-10-31 직후) → `TODO_jp.md`.
- [ ] **inbox 열린 10건(`status_report.py --fast` 2026-10-14 실측: parser 9 · publishing 1)** — 목록은 status_report 로 본다(이 줄의 옛 「4건」 서술은 낡았다).
  옛 4건 = parser 3(PL 부모 #2 결측 26버킷 · 메리츠 2026.2Q item2/3 적용후 stale 외 · 금리민감도 phase 31칸) + publishing 1(자본성증권 step_up·잔액기준일·한화 item54). 남은 일은 각 티켓 맨 아래 「현황」.
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
