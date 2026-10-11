# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-11 IFRS17 섹션 3 모바일 단순형 재도입 · ? 팝오버 가려짐 수정 · 시장지도 재보·보증 절반 · 상각 축 단위 · 전망 제외 사유 완료(커밋 6f92fb0·44c7afc·후속, 미배포)** — 모바일(≤640px) = 기말 CSM 막대(주축)+신계약 CSM 선(보조축), 눈금은 숫자만·단위는 축 제목(조원/억원). 좌우 축 폭 61·64px → 34~55px(삼성생명 375px 그림 영역 184→245px).
  원인(?): `.panel.revealed` 의 `animation … forwards` 가 패널마다 쌓임 맥락을 만들어 아래 패널이 팝오버를 덮음 → `common.css` 에서 forwards 제거, 팝오버 z-index 1950, 하단이 잘리면 위로 뒤집기/터치는 스크롤(theme.js `flipHelpPop`). index 재보·보증 높이 246→122px(`RE_MIN_SHARE` 0.07). 상각 차트 눈금·툴팁은 데이터가 억원인데 백만원으로 보던 오류 수정, 전망 빈 상태 문구는 `row.exclusion_reason`. 남은 것: 없음(배포는 owner GO).
- **2026-10-11 K-ICS 「자산·부채 듀레이션」 별도 섹션 + 시나리오별 금리부 자산·부채 표 완료(K-ICS.html·검증 2종 기대 섹션 수 4→5, 커밋·미배포)** — 듀레이션 카드·산식 「?」·비고를 금리 민감도에서 떼어 `#sec-dur`(금리 민감도 바로 아래, 공유 버튼·목차 5번째). 표 = 열 6시나리오(충격전·금리상승·금리하락·평탄화·경사화·평균회귀) × 행 금리부자산·금리부부채·순자산, 칸 아랫줄에 충격전 대비 변화(금액·%).
  단위: 마스터 `kics_duration_gap.json` 열은 **이미 억원**이라 환산 안 함(티켓의 「백만원×0.01」은 사실과 다름 — 빌더가 ÷100 해서 적재, 삼성생명 자산−부채 156,916.32 = 항목41 순자산가치). 자체 분기 선택(2023.2Q~, 금리 민감도는 2024.4Q~). 검증 헤드리스 25조합(5사×480·768·1280·라이트/다크) 콘솔 오류 0·가로 넘침 0, 테스트 83 통과, `check_share_screenshot.py` 통과. 남은 것: 없음(배포는 owner GO).
- **2026-10-11 다운로드 목록에 시트 3개 추가 + K-ICS 자본비율 전망 빈 상태 문구 정정 완료(`download-survey.js`·`K-ICS.html`, 커밋·미배포)** — `SHEETS` 에 보험계약부채(ILP)·자본성증권발행현황(CAPSEC)·금리듀레이션갭(DGAP) 추가(후자 둘은 공개 시트인데 목록에서만 빠져 있었음, 의도된 비공개 아님). 전망 패널 「(19사 cohort 외)」 는 숫자 없는 사실 문구로 교체, 서울보증은 「보험료배분접근법만 적용해 제외」(자본성증권 없어서가 아님).
  검증 헤드리스 8조합(4페이지×1280·375) 15개 라벨 잘림·겹침·가로 넘침 0, 새 3시트 다운로드 xlsx 시트·행수 일치, `test_deploy_assets`+`test_push_gate_wiring` 77 통과. 남은 것: 서울보증 제외 이유를 데이터가 말하게 하려면 publishing 이 전망 파일에 제외 사유를 담아야 함(지금은 이름으로 분기).

## publishing 이 배포 전에 해야 할 일 (2026-10-10 designer)

- **2026-10-11 오후 변경 묶음**: 새 배포 파일 없음(`IFRS17.html`·`K-ICS.html`·`index.html`·`common.css`·`theme.js`). 화면 변경 = IFRS17 섹션 3 모바일 단순형, 4페이지 공통 「?」 팝오버가 패널 아래로 열려도 가려지지 않음(`common.css` 패널 reveal 애니메이션 정리 — 데스크톱 패널 표시 변화 없음), index 시장지도 재보험·보증 그룹 면적 절반·제목 문구 삭제, IFRS17 상각 차트 눈금(100배 작게 찍히던 라이브 증상) 정정. K-ICS 전망 빈 상태 문구는 `kics_forward_capital.json` 의 KR0150 행(`status=excluded`·`exclusion_reason`)을 읽으므로 **그 JSON 이 라이브에 먼저/같이 가야 한다**(없으면 「대상이 아닙니다」 일반 문구).
- **공유 스크린샷(2026-10-11)**: 새 배포 파일·CDN 없음. 바뀐 배포 파일 = `theme.js`·`common.css`·`K-ICS.html`·`IFRS17.html`·`compare.html`(html2canvas 1.4.1·SRI 는 기존 그대로). 검증 스크립트 `scripts/check_share_screenshot.py` 는 배포 대상 아님.
- **`data/company_segment.json` 을 배포 파일 목록에 추가** — `scripts/android_push_and_deploy.sh` 의 `NEW_FILES`(154행)에 없으면 라이브 index·compare 가 재보사를 생보/손보에 섞어 보이거나 3구분이 안 된다(index 는 로드 실패 시 콘솔 경고만 남기고 옛 2구분으로 폴백). `tests/test_push_gate_wiring.py` 출처 표에 이 파일(마스터 아님, 수기 매핑)을 넣을지는 publishing 판단.
- **재보험·보증 3분류 반영 완료** — 8곳이 든 `kics_disclosure.json` 배포 선행 조건 충족. 같이 올릴 파일: `index.html` · `K-ICS.html` · `compare.html` · `IFRS17.html`(이름 약칭 1줄) · `공시보고서.html`(약칭 1줄) · `report-widget.js`(약칭) · `data/company_segment.json` · `data/compare/panel_compare.json`(`viz_build_compare_panel.py` 재실행 필수 — kics_disclosure.json 이 바뀌면 값이 움직인다) · `scripts/viz_build_compare_panel.py`.
- **IFRS17 섹션 3 콤보(이식 완료)**: 배포 파일에 `data/csm_combo/panel_csm_combo.json` 추가(`scripts/android_push_and_deploy.sh` `NEW_FILES`, 라이브 keep-list) + `IFRS17.html`. 배포 직전 `viz_build_csm_combo_panel.py` 재실행/`--check`(포트폴리오·CSM_waterfall·IFRS17_BS 마스터와 사이드카 `data/_derived/ilp_includes_lic.json` 이 바뀌면 값이 움직인다 — 사이드카는 빌더 입력이지 화면이 fetch 하는 파일이 아니라 keep-list 대상 아님). 새 배포 파일 없음(패널 JSON 내용만 바뀜). 발생사고요소 실값 반영 완료(2026-10-10 늦게). 2026-10-11: 패널에 열 `lrc_dart`(항목 14) 추가·2-4 구성이 없는 분기 CSM 대조 제외(불일치 14→3) — 포트폴리오 마스터가 바뀌면 `viz_build_csm_combo_panel.py` 재실행 후 `--check`. 테스트 배선은 `tests/test_push_gate_wiring.py` 에 반영됨. 알려진 화면 이슈: 예별손보 2025.4Q 는 경영공시 2-4 CSM 이 CSM_waterfall 과 다름(화면에 안내).
- **사별 비교 모바일 손해율 curve·손익 YTD(2026-10-11)**: 새 배포 파일 없음(`compare.html`·`theme.js`·`IFRS17.html`·`data/compare/panel_compare.json`·`scripts/viz_build_compare_panel.py`). `theme.js` 가 바뀌므로 4페이지 공통 배포 파일 목록에 포함. **보험손익·당기순이익·투자손익 숫자가 당분기에서 연 누계로 바뀐다(화면 변경, 카드·도움말에 「연 누계(YTD)」 명시)** — 라이브 반영은 owner GO. `loss_curve.note` 문구는 이미 중립이라 고칠 것 없음.
- **IFRS17 섹션 3 이름·모바일(2026-10-11)**: 사용자에게 보이는 이름이 「CSM 시계열」 → 「보험계약부채 시계열」(앵커 `#sec-hist` 불변), 모바일도 데스크톱과 같은 콤보, 긴 설명은 「?」 팝오버. 새 배포 파일 없음(`IFRS17.html` 만). 배포 직전 `viz_build_csm_combo_panel.py --check` 가 FAIL 이면(2026-10-11 현재 다른 세션이 포트폴리오 마스터·사이드카를 수정 중) 그 작업이 끝난 뒤 패널을 재빌드한다.
- **다운로드 목록 시트 3개·전망 문구(2026-10-11)**: 새 배포 파일 없음(`download-survey.js`·`K-ICS.html` 만 바뀜 — 둘 다 이미 배포 목록에 있음). 새 시트 3개는 `public_exports/` 스냅샷이 라이브에 올라가 있어야 내려받기가 된다(없으면 404 → 「다운로드 중 문제가 발생했습니다」). `export_public_sheets.MASTERS` 와 `SHEETS` 가 같은 15개가 됐으니 시트를 더 만들면 이 목록에도 넣어야 한다.
- **K-ICS 자산·부채 듀레이션 섹션(2026-10-11)**: 새 배포 파일 없음(`K-ICS.html` 만, 이미 fetch 하던 `kics_duration_gap.json` 사용 — main 에 있음). 화면 변경 = 금리 민감도 패널에서 듀레이션 카드가 빠져 새 패널(`#sec-dur`)로 이동, 시나리오별 금리부 자산·부채 표 추가, 목차 항목 1개 증가(5개). 열 단위는 억원(환산 없음). 이 파일이 있는 한 라이브 반영은 owner GO.
- **마스터 xlsx 시트 없음**: `insurance_liability_portfolio.json`(IFRS17 섹션 3 콤보의 원천)은 `build_master_xlsx.MASTERS` 에 시트가 없다. `tests/test_push_gate_wiring.py` 에 `MASTER_SHEET_PENDING` 으로 사실대로 선언해 둠 — 시트를 만들면 그 선언을 지워야 테스트가 통과한다(`data/company_segment.json` 은 분류표라 `NOT_A_MASTER`).
- 비교 모집단 변화(숫자 불변, 화면만): compare.html 「같은 유형 업계 중앙값」·손해율 가정 중앙값 — 손보 모집단에서 코리안리·서울보증 제외(이미 제외돼 있었음, 이제 재보험·보증은 아예 별도 유형). index KPI 「지급여력비율 중앙값·보험사 수」는 재보사 8곳이 들어와 47곳 기준. 재보사 8곳의 단독 순위·중앙값은 없음.

## 열린 일

- [ ] **사별 비교 손해율 curve 선 색(owner 확인)**: 키컬러 없는 회사의 파스텔 선(틸 `#4fb0a5`·살몬 `#ee8f72`·블루 `#7b9fe6`·머스터드 `#cdb04a`)은 흰 배경에서 2.1~2.6:1(비텍스트 3:1 미달, 어두운 배경은 6.8:1 이상). owner 지시가 「파스텔」이라 그대로 뒀고, 키컬러 선만 대비 3:1 이 되게 같은 색상에서 밝기를 옮긴다(KB 노랑→`#b88700`). 값 표의 색 견본이 선과 같은 색이라 색만으로 구분하진 않는다. 농협생명은 맵에 `NH농협생명` 으로만 있어 compare 가 `'NH'+약칭` 별칭으로 찾는다(IFRS17 은 별칭 없음).

- [ ] **LIC 2단계(항목 16·17) 적재 후**: 화면은 이미 준비됨(줄무늬 「계산값」 BEL·RA, 합성 데이터로 확인) — 실데이터가 들어오면 빌더 재실행·`--check` 후 화면만 재확인. index 트리맵 재보험·보증은 손해 아래 칸(3열 가로 배치가 필요하면 알려 주세요). 후속 후보: 「CSM 확대(CSM만 자동 스케일)」 토글(owner 정정으로 지금은 안 만듦).

- [ ] **듀레이션갭 3개 분기 도달 불가** — publishing 과 같이(`TODO_publishing.md`).
- [ ] **팔레트 B 에서 내 판단으로 바꾼 +/△ 색**(올리브 `#4b7f2a`·벽돌 `#b4443a`) — owner 확인 대기.
- [ ] **jp ESRランキング 범례 8개** — owner 판단 대기(2026-09-15b).

## owner 결정 대기 · 휴면

KEYCOLOR/COMPANY-ACCENT 방향 재검토 · MOB-KICS·MOB-IFRS17 owner 권고 2건(가로 스크롤 범위 · 640px 외 breakpoint) · MOB-IFRS17 패널 1~6 정책 ·
VIS-CHARTLEGEND(IFRS17 상각·index 버블 범례) · M3 차트 미세조정 · F17 Panel 3 Tier2(parser 결정 대기) · F16 Panel 5 caption(가능한 회사 명시).

## 참고

- 페이지 4개: `index.html`(시장지도·버블) · `K-ICS.html` · `IFRS17.html`(7패널, 1=재무상태표 T계정) · `공시보고서.html`(배당현황).
- 차트: Chart.js(IFRS17 패널 2~6) · ECharts(CSM 워터폴·treemap·버블). 색은 `IQTheme.chart()` 로 CSS 변수를 읽는다(라이브러리는 `var()` 를 못 먹는다).
- 로컬 미리보기 `python -m http.server 8000`. 프리뷰 창은 `window` scroll 이벤트를 안 뿜는다 — 스크롤 스파이는 합성 이벤트로 검증.
