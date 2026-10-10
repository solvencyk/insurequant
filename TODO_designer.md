# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-11 공유 스크린샷: 헤더 메뉴=페이지 전체 복구 + 섹션별 공유 버튼 완료(theme.js·common.css·K-ICS/IFRS17/compare, 미커밋·미배포)** — 원인: 8c997cb(2026-10-08)가 본문 6000px 초과 시 「지금 화면만」으로 막아 둠(K-ICS·IFRS17·모바일은 거의 다 초과). 임계값 폐기, 캔버스 한도는 scale 자동 하향(한 변 16,000px·터치 면적 1,600만 px, 하한 0.75 밑이면 위쪽만+안내).
  섹션 버튼: K-ICS 4·IFRS17 9·compare 카드 전부(마크업 `data-share-section`), 이미지에 제목(페이지·섹션·회사)+출처. 검증 `scripts/check_share_screenshot.py`(1280·375·라이트·다크 통과), 회귀 `tests/test_share_screenshot.py`(`RUN_SHARE_SHOT=1` 이면 브라우저 검사). 남은 것: 아주 긴 페이지(약 2만 px 초과) 이어 붙이기는 제안만(현재 모든 페이지 1.3만 px 이하).
- **2026-10-11 IFRS17 섹션 3: 모바일도 데스크톱 콤보 그대로 + 긴 설명 「?」 + 이름 「보험계약부채 시계열」 완료(IFRS17.html 만, 미커밋·미배포)** — 직전 모바일 단순형(막대+선)은 철회. ≤640px 도 같은 묶음 누적 콤보(패널 가장자리까지·높이 420px·범례 위 가로 9px·x 라벨 회전 없음, 분기 `25.2Q`·축 제목 짧게). 설명은 두 환경 모두 한 줄 + 「?」(차트 아래 경고 한 줄은 모바일 약 19자 + 「외 N건」), DART 원문 설명 110자 초과도 접음.
  데스크톱 차트 78조합 해시 동일(`83c990fa`), 375px·1280px 라이트·다크 확인, 콘솔 오류 0. 남은 것: `viz_build_csm_combo_panel.py --check` FAIL(패널≠신규 빌드) — 다른 세션이 포트폴리오 마스터·사이드카를 막 바꾼 입력 변화(내 변경 무관), 그 작업 뒤 publishing 이 패널 재빌드.
- **2026-10-11 사별 비교: 모바일 손해율 curve 재정비 + 손익 연 누계(YTD) 전환 + 테스트 선언 완료(compare.html·theme.js·IFRS17.html 1곳·빌더·테스트, 미커밋·미배포)** — curve 는 카드 폭 100%·선 끝 라벨 없음·실선, 회사 구분은 색만. 색=회사 키컬러(맵을 theme.js `IQTheme.keyColors` 로 올림, IFRS17 동작 동일), 없거나 선택 회사끼리 CIEDE2000 20 미만이면 파스텔 팔레트. 데스크톱 curve 도 같은 색.
  보험손익·당기순이익·투자손익은 PL `값`(연 누계)으로 바꿨고 카드 제목은 「… · 연 누계」, 최신 공시 줄에 「상반기(1~2Q) 누계」 표기. ROE 값은 불변(연환산 배수 1Q×4·2Q×2·3Q×4/3·4Q×1 확인). `test_push_gate_wiring` 2건 통과(선언 보정). 남은 것: publishing 이 `insurance_liability_portfolio.json` xlsx 시트 신설(아래).

## publishing 이 배포 전에 해야 할 일 (2026-10-10 designer)

- **공유 스크린샷(2026-10-11)**: 새 배포 파일·CDN 없음. 바뀐 배포 파일 = `theme.js`·`common.css`·`K-ICS.html`·`IFRS17.html`·`compare.html`(html2canvas 1.4.1·SRI 는 기존 그대로). 검증 스크립트 `scripts/check_share_screenshot.py` 는 배포 대상 아님.
- **`data/company_segment.json` 을 배포 파일 목록에 추가** — `scripts/android_push_and_deploy.sh` 의 `NEW_FILES`(154행)에 없으면 라이브 index·compare 가 재보사를 생보/손보에 섞어 보이거나 3구분이 안 된다(index 는 로드 실패 시 콘솔 경고만 남기고 옛 2구분으로 폴백). `tests/test_push_gate_wiring.py` 출처 표에 이 파일(마스터 아님, 수기 매핑)을 넣을지는 publishing 판단.
- **재보험·보증 3분류 반영 완료** — 8곳이 든 `kics_disclosure.json` 배포 선행 조건 충족. 같이 올릴 파일: `index.html` · `K-ICS.html` · `compare.html` · `IFRS17.html`(이름 약칭 1줄) · `공시보고서.html`(약칭 1줄) · `report-widget.js`(약칭) · `data/company_segment.json` · `data/compare/panel_compare.json`(`viz_build_compare_panel.py` 재실행 필수 — kics_disclosure.json 이 바뀌면 값이 움직인다) · `scripts/viz_build_compare_panel.py`.
- **IFRS17 섹션 3 콤보(이식 완료)**: 배포 파일에 `data/csm_combo/panel_csm_combo.json` 추가(`scripts/android_push_and_deploy.sh` `NEW_FILES`, 라이브 keep-list) + `IFRS17.html`. 배포 직전 `viz_build_csm_combo_panel.py` 재실행/`--check`(포트폴리오·CSM_waterfall·IFRS17_BS 마스터와 사이드카 `data/_derived/ilp_includes_lic.json` 이 바뀌면 값이 움직인다 — 사이드카는 빌더 입력이지 화면이 fetch 하는 파일이 아니라 keep-list 대상 아님). 새 배포 파일 없음(패널 JSON 내용만 바뀜). 발생사고요소 실값 반영 완료(2026-10-10 늦게). 2026-10-11: 패널에 열 `lrc_dart`(항목 14) 추가·2-4 구성이 없는 분기 CSM 대조 제외(불일치 14→3) — 포트폴리오 마스터가 바뀌면 `viz_build_csm_combo_panel.py` 재실행 후 `--check`. 테스트 배선은 `tests/test_push_gate_wiring.py` 에 반영됨. 알려진 화면 이슈: 예별손보 2025.4Q 는 경영공시 2-4 CSM 이 CSM_waterfall 과 다름(화면에 안내).
- **사별 비교 모바일 손해율 curve·손익 YTD(2026-10-11)**: 새 배포 파일 없음(`compare.html`·`theme.js`·`IFRS17.html`·`data/compare/panel_compare.json`·`scripts/viz_build_compare_panel.py`). `theme.js` 가 바뀌므로 4페이지 공통 배포 파일 목록에 포함. **보험손익·당기순이익·투자손익 숫자가 당분기에서 연 누계로 바뀐다(화면 변경, 카드·도움말에 「연 누계(YTD)」 명시)** — 라이브 반영은 owner GO. `loss_curve.note` 문구는 이미 중립이라 고칠 것 없음.
- **IFRS17 섹션 3 이름·모바일(2026-10-11)**: 사용자에게 보이는 이름이 「CSM 시계열」 → 「보험계약부채 시계열」(앵커 `#sec-hist` 불변), 모바일도 데스크톱과 같은 콤보, 긴 설명은 「?」 팝오버. 새 배포 파일 없음(`IFRS17.html` 만). 배포 직전 `viz_build_csm_combo_panel.py --check` 가 FAIL 이면(2026-10-11 현재 다른 세션이 포트폴리오 마스터·사이드카를 수정 중) 그 작업이 끝난 뒤 패널을 재빌드한다.
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
