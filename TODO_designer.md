# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-19 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-19 접근성 2차 C8~C15 · C17 완료(push `7fc4971f` · main 배포 `3a91a4ea` 완료, 라이브 4파일 바이트 일치; owner 「C8~C17 진행」)** — compare 카드 제목 h3 → h2(+ `aria-label` 로 접근 이름 최대 840 → 16자, 모양 불변), 섹션 공유 버튼 이름을 섹션별로 고유하게, compare · privacy `<main>` + 포커스 때만 보이는 건너뛰기 링크, 감소 모션에서 Chart.js 애니메이션 · smooth 스크롤 끔(index · K-ICS · IFRS17 차트도 같이), 경과조치 · 중앙값 조작 뒤 `#live` 문구, 테마 토글 `aria-pressed` 제거(바뀌는 레이블만), compare 넓은 화면 손해율 카드에 화면 밖 현재가치 표, privacy 표 영역 `role=region`.
  검사: `scripts/check_a11y_compare_privacy.py --step 3` 4,287 단언 통과, 별도 검증자 25분 상자(제목 모양 HEAD 와 차이 0 · 6페이지 공유 버튼 이름 중복 0 · 건너뛰기 링크 · 감소 모션 · 첫 화면 24조합은 노이즈 이내). 남은 것: C16(WCAG 2.1 대 2.2 목표 결정) · C10 링크 없이 Tab 30번(링크 쓰면 3번).
- **2026-10-19 밤 손해율 비교 단위 선택기 · 오류 제보 내부 접속 제외 · a11y C1·C2·C3·C4·C6 완료(push `a8d9f193` · main 배포 `5221a1b4` 완료; owner 승인)** — 선택기: compare 손해율 카드 · IFRS17 8절 select 하나(구분 · 생보 · 손보 · 재보), 단위 없는 회사는 n/a 줄, 100억원 미만 칸 흐린 점선, 주소 `g=` 는 구분 이름과 단위 키 모두. `report-widget.js` 는 `iq_internal=1` 이면 수집기로 안 보냄. a11y: ? 팝오버 마우스 유예(`common.css` `.is-grace` + `theme.js` `pointerleave` 0.4초), 칩 제거·추가 뒤 포커스, 입력창 `--control-border` · placeholder `--muted`, 모바일 손해율 선 표식.
  독립 검증: 220+507 상태 · 회귀 82건 · 44상태 HEAD 대비 스타일 차이는 입력창 테두리·placeholder·팝오버 다리뿐. 버린 것: ? 옆 삼각형 호버 영역(오른쪽 끝에서 문서를 가로로 넓힘). 남은 것: C8~C17 · 일본 오류 제보 위젯 · n/a 문구를 ? 팝오버로 옮길지.
- **2026-10-19 안내 팝업 시작일 10-31 · 손해율 기본 Non-Par · 방명록 내부 접속 제외 · a11y 감사 완료(main 배포 `f96f06b0` 완료; owner 승인)** — 팝업 `NOTICE.showFrom` 2026-10-31(독립 검증 47/47), 선택기 기본 Non-Par(마스터 재계산 0.05pp 이내), `download-survey.js` 가 `iq_internal=1` 방문을 수집기로 보내지 않음. compare·privacy 감사 18건(중간 6 · 낮음 9 · 참고 3)을 `docs/a11y_baseline.md` 와 티켓 `20261019T1400Z` 에.
  남은 것: a11y 티켓 수정(? 팝오버 마우스 접근 · 포커스 유실 · 모바일 손해율 선 마커 등 코드 문제 먼저, 색 변경 5건은 owner 승인 뒤) · 구분 단위 평면 8개 선택기(owner 결정 대기, `TODO.md`) · 배포 때 HTML 2개 + `panel_compare.json` + `panel_loss_ratio.json` + `theme.js` + `download-survey.js` 한 묶음.

## publishing 이 배포 전에 해야 할 일

- 2026-10-13 main `970259b8` 배포로 전부 끝났다(`data/company_segment.json`·`data/csm_combo/panel_csm_combo.json`·`data/compare/panel_compare.json`·`kics_duration_gap.json` 이 origin/main 에 있음, ILP 시트는 `public_exports/보험계약부채.json` 로 공개됨). 전문은 `docs/todo_archive_designer.md` 맨 위.

## 열린 일

- [ ] **사별 비교 손해율 curve 선 색(owner 확인)**: 키컬러 없는 회사의 파스텔 선(틸 `#4fb0a5`·살몬 `#ee8f72`·블루 `#7b9fe6`·머스터드 `#cdb04a`)은 흰 배경에서 2.1~2.6:1(비텍스트 3:1 미달, 어두운 배경은 6.8:1 이상). owner 지시가 「파스텔」이라 그대로 뒀고, 키컬러 선만 대비 3:1 이 되게 같은 색상에서 밝기를 옮긴다(KB 노랑→`#b88700`). 값 표의 색 견본이 선과 같은 색이라 색만으로 구분하진 않는다. 농협생명은 맵에 `NH농협생명` 으로만 있어 compare 가 `'NH'+약칭` 별칭으로 찾는다(IFRS17 은 별칭 없음). **owner 2026-10-19: a11y 감사 C7 로도 올라왔으나 하지 않기로 결정(값 표에 수치가 같이 표시됨).**

- [ ] **LIC 2단계(항목 16·17) 적재 후**: 화면은 이미 준비됨(줄무늬 「계산값」 BEL·RA, 합성 데이터로 확인) — 실데이터가 들어오면 빌더 재실행·`--check` 후 화면만 재확인. index 트리맵 재보험·보증은 손해 아래 칸(3열 가로 배치가 필요하면 알려 주세요). 후속 후보: 「CSM 확대(CSM만 자동 스케일)」 토글(owner 정정으로 지금은 안 만듦).

- [ ] **듀레이션갭 3개 분기 도달 불가** — publishing 과 같이(`TODO_publishing.md`).
- [ ] **팔레트 B 에서 내 판단으로 바꾼 +/△ 색**(올리브 `#4b7f2a`·벽돌 `#b4443a`) — owner 확인 대기.
- [ ] **jp ESRランキング 범례 8개** — owner 판단 대기(2026-09-15b).

## owner 결정 대기 · 휴면

KEYCOLOR/COMPANY-ACCENT 방향 재검토 · MOB-KICS·MOB-IFRS17 owner 권고 2건(가로 스크롤 범위 · 640px 외 breakpoint) · MOB-IFRS17 패널 1~6 정책 ·
VIS-CHARTLEGEND(IFRS17 상각·index 버블 범례) · M3 차트 미세조정 · F17 Panel 3 Tier2(parser 결정 대기) · F16 Panel 5 caption(가능한 회사 명시).

## 참고

- 페이지 5개: `index.html`(시장지도·버블) · `K-ICS.html` · `IFRS17.html`(7패널, 1=재무상태표 T계정) · `공시보고서.html`(배당현황) · `compare.html`(사별 비교).
- 차트: Chart.js(IFRS17 패널 2~6) · ECharts(CSM 워터폴·treemap·버블). 색은 `IQTheme.chart()` 로 CSS 변수를 읽는다(라이브러리는 `var()` 를 못 먹는다).
- 로컬 미리보기 `python -m http.server 8000`. 프리뷰 창은 `window` scroll 이벤트를 안 뿜는다 — 스크롤 스파이는 합성 이벤트로 검증.
