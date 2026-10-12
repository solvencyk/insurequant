# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-12 모바일 섹션 공유 이미지 가로 확장 제거 완료(theme.js, 커밋·미배포)** — 폰(화면 폭 520px 미만 또는 coarse pointer)의 섹션 이미지는 표 폭만큼 넓히지 않고 화면의 섹션 폭 그대로(차트가 폭을 가득 채움, 표는 보이는 열까지). 데스크톱 widen 은 그대로, 페이지 전체 이미지 경로 불변.
  375px 로 뮌헨 손해율 가정·삼성생명 NB·코리안리 섹션 이미지 폭 379px(전엔 약 1000px), 데스크톱 뮌헨 손해율 가정 1104px 로 불변. 시험 4종 통과. 남은 것: 없음.
- **2026-10-12 공유 버튼 사용 기록 → 수집기 shares 탭 완료(theme.js·compare.html·privacy.html·insurequant_collector.gs, 커밋·미배포)** — 링크 복사·페이지 전체·섹션 스크린샷마다 익명 1건(page·action·section·company·device·result). iq_internal 0건·연타 1건·forms-config 없음 무오류. **owner 가 구글 Apps Script 에서 .gs 새 버전 배포를 해야 shares 탭이 생긴다(전까지는 downloads 탭에 섞여 들어감).** 검증 `scripts/check_share_log.py`.
- **2026-10-12 IFRS17 섹션 8에 보험금 예실차비율 표 추가 완료(IFRS17.html, 커밋·미배포)** — 손해율 가정 표 아래에 예상손해율·실제손해율·보험금 예실차비율(공시 이름 그대로, 연도 열, %·%p, 음수 △, 마스터 값 그대로), 설명은 ? 팝오버만. 사업구분이 있는 코리안리는 공동재보험/전통형재보험 블록으로 나눔(88개 공시 중 2곳뿐). `ae` 없음(서울보증 등)·구판 패널이면 표 전체 생략.
  스위스리·뮌헨·삼성생명·코리안리·예별·카카오페이 375px·1280px 콘솔 0·가로 넘침 0, 시점 토글(2025.4Q/2024.4Q) 동작. 시험 3종 통과. 검증 `scripts/shot_lr_ae.py`. 남은 것: 없음(배포는 새 판 패널과 함께).

- **2026-10-12 IFRS17 통합 현황 박스에 요약 4칸 이동 + NB CSM 배수 차트 아래 표 완료(IFRS17.html, 커밋 46d4a3a 외 1건·미배포)** — 제목 박스(패널 1개)가 기준 토글과 요약 4칸을 함께 담고 나머지 섹션은 그 아래 별도 패널(전엔 회색 바깥 패널 안에 중첩). 섹션 6 차트 아래 표(월납월초보험료·신계약 CSM·신계약 CSM 배수, 연도=연누계·분기=당분기, 차트와 같은 시점). 삼성생명·라이나 375px·1280px 콘솔 0·가로 넘침 0. 남은 것: 없음.
- **2026-10-12 K-ICS 듀레이션 섹션 컬럼명·주석 정리 완료(K-ICS.html, 커밋·미배포)** — 표 컬럼 충격전·평균회귀·금리상승·금리하락·금리평탄·금리경사(공시 이름·순서, `DUR_SCEN`), 표 아래 자료 줄·갭 카드 주석·비고 전부 ? 팝오버 안으로. 충격전 순자산=자산−부채 일치, 375px 가로 스크롤·콘솔 0. 남은 것: 없음.
- **2026-10-12 index 모바일 재보험·보증 그룹도 상위 5 + 더보기 완료(index.html, 커밋·미배포)** — K-ICS 리스트·CSM 버블 리스트 모두 섹터 키 맵 상태로 일반화. 375px 에서 재보험 `더보기 (4개사)`/`접기` 동작, 생보·손보 회귀 0, 콘솔 0. 남은 것: 버블 리스트는 재보험·보증사 NB 배수가 생기면 자동 적용.
- **2026-10-12 index KPI 「업계 총 기말 CSM」 카드에서 부가 문구·? 팝오버 제거 완료(index.html, 커밋·미배포)** — 값+라벨만(다른 KPI 와 동일). 값 계산 불변(142조), 데스크톱·모바일 높이 동일, 콘솔 0. 남은 것: 없음.
- **2026-10-11 재보사 7곳 PL 항목 4 라벨 「원수」 제거 + 패널 렌더 점검 완료(IFRS17.html, 커밋·미배포)** — 전업 재보험사(뮌헨·스위스리아시아·제네럴·하노버·알지에이·스코리·퍼시픽라이프리)는 보험손익 구성의 「원수 CSM상각」→「CSM 상각」(위험조정·예실차·기타 손익 포함), 막대·툴팁·표·캡션·제목·aria 모두. 매핑은 `IFRS17.html` `PL_RE_ONLY`/`PL_RE_LABEL`(화면 라벨 한 곳, 마스터 항목명 불변), 라이나·코리안리는 그대로.
  렌더: 값이 항목 4 하나뿐인 4Q 버킷(연말)·항목 4 도 없는 중간분기 모두 열어 봤고 현재 「값 있으면 막대, 없으면 회색 미공시」 관례가 그대로 읽혀 브리지는 안 바꿈(누적 잔차 막대 없음, 앵커가 0 에서 다시 시작). 스크린샷 `artifacts/designer/reinsurer_csm_amort/`(gitignore), 검증 `scripts/shot_pl_panel3.py`. 남은 것: 투자손익·영업외 항목이 비어 법인세 막대가 순이익과 안 맞는 건 재보사·26사 공통 기존 현상(parser 가 17·21 을 채우면 해소).
- **2026-10-11 index KPI 「업계 총 기말 CSM」 같은 분기 합산 완료(index.html, 커밋·미배포)** — 원천 `panel_csm_combo.json`(csm_gen+csm_vfa)의 기준 분기(값 있는 회사가 80% 이상인 가장 늦은 분기) 합: 2026.2Q 47사 142.2조(표시 142조, 모집단=시장지도 KPI 와 같은 47사, 값 없는 하노버는 직전 분기 값으로 대체·팝오버에 명시), 라벨 아래 「2026.2Q 기준 · 47사」(데이터 도출)와 「?」 정의 팝오버.
  패널 로딩 실패·구판(해당 분기 없음)이면 옛 `totalClosingCsmEok()`(회사별 최신 분기 합)로 폴백(헤드리스 404·열 누락·분기 제거 시험 통과). `.rise` 애니메이션 fill `both`→`backwards`(팝오버 가려짐 방지). 남은 것: 새 판 패널(48사·14분기)이 라이브에 먼저 가야 142조, 다른 CSM 합계 표기는 없음.
- **2026-10-11 IFRS17 섹션 3 모바일 단순형 재도입 · ? 팝오버 가려짐 수정 · 시장지도 재보·보증 절반 · 상각 축 단위 · 전망 제외 사유 완료(커밋 6f92fb0·44c7afc·후속, 미배포)** — 모바일(≤640px) = 기말 CSM 막대(주축)+신계약 CSM 선(보조축), 눈금은 숫자만·단위는 축 제목(조원/억원). 좌우 축 폭 61·64px → 34~55px(삼성생명 375px 그림 영역 184→245px).
  원인(?): `.panel.revealed` 의 `animation … forwards` 가 패널마다 쌓임 맥락을 만들어 아래 패널이 팝오버를 덮음 → `common.css` 에서 forwards 제거, 팝오버 z-index 1950, 하단이 잘리면 위로 뒤집기/터치는 스크롤(theme.js `flipHelpPop`). index 재보·보증 높이 246→122px(`RE_MIN_SHARE` 0.07). 상각 차트 눈금·툴팁은 데이터가 억원인데 백만원으로 보던 오류 수정, 전망 빈 상태 문구는 `row.exclusion_reason`. 남은 것: 없음(배포는 owner GO).

## publishing 이 배포 전에 해야 할 일 (2026-10-10 designer)

- **재보사 PL 항목 4 라벨(2026-10-11)**: 새 배포 파일 없음(`IFRS17.html` 만). 화면 변경 = 전업 재보험사 7곳 보험손익 구성 라벨 「원수 CSM상각」→「CSM 상각」 등. 이 라벨은 `PL_breakdown.json` 에 항목 4 가 있어야 막대·표 행으로 보이니 마스터가 먼저/같이 가야 한다(없으면 회색 「미공시」).
- **2026-10-11 오후 변경 묶음**: 새 배포 파일 없음(`IFRS17.html`·`K-ICS.html`·`index.html`·`common.css`·`theme.js`). 화면 변경 = IFRS17 섹션 3 모바일 단순형, 4페이지 공통 「?」 팝오버가 패널 아래로 열려도 가려지지 않음(`common.css` 패널 reveal 애니메이션 정리 — 데스크톱 패널 표시 변화 없음), index 시장지도 재보험·보증 그룹 면적 절반·제목 문구 삭제, IFRS17 상각 차트 눈금(100배 작게 찍히던 라이브 증상) 정정. K-ICS 전망 빈 상태 문구는 `kics_forward_capital.json` 의 KR0150 행(`status=excluded`·`exclusion_reason`)을 읽으므로 **그 JSON 이 라이브에 먼저/같이 가야 한다**(없으면 「대상이 아닙니다」 일반 문구).
- **index KPI 업계 총 기말 CSM(2026-10-11)**: `data/csm_combo/panel_csm_combo.json` 을 index 가 새로 fetch(이미 배포 파일 목록에 있음, 새 파일 없음). 라이브가 구판 패널이면 KPI 는 옛 방식(분기 혼합 139~141조)으로 폴백하니 새 판 패널과 같이 올릴 것 — 그래야 2026.2Q 142조가 나온다.
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
