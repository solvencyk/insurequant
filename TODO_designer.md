# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-11 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-11 사별 비교 모바일 손해율 가정 curve 카드 완료(compare.html 만, 미커밋·미배포)** — 640px 이하에서 한 차트에 선택 회사 곡선을 겹친 정적 SVG(선 끝 라벨·업계 중앙값 점선) + 「회사·현재가치」 표. 「짚은 시점」 열·터치 가이드는 뺐다. 데스크톱 Chart.js 와 다른 모바일 카드는 그대로.
  선 색은 데스크톱 curve 와 같은 `PAL_LINE[선택 순서]`(데스크톱이 회사 키컬러가 아니라 선택 순서 팔레트라 그쪽을 따름). 선 모양(실선·파선·점선)으로 색 외 구분, 상한 `MOB_LINES=4`곳(현재 최대 선택 4곳이라 안 걸림). 남은 것: owner 확인 2건(아래 열린 일).
- **2026-10-10 IFRS17 섹션 3 콤보: 기간이 상단 「기준」을 따르고 컨트롤 줄 제거 완료(IFRS17.html 만, 미커밋·미배포)** — 분기=최신 분기까지 연속 5분기 / 연도=직전 3개 연말(회사에 데이터가 있는 해만)+최신 분기(연말은 「2025」처럼 연도 표기, 섹션 1·2 와 같음). 최신 분기·기간은 데이터에서 도출(하드코딩 없음).
  패널(경영공시 2-4)에 행이 없고 CSM_waterfall 기말 CSM 만 있는 시점은 「CSM 만」 막대(나머지 「—」·안내문은 데이터 유무로 판단). 지금 CSM 만 나오는 시점 = 2023.4Q·2024.4Q(패널이 2025.1Q~). 패널 백필 후 `viz_build_csm_combo_panel.py` 한 번 재실행하면 화면은 코드 수정 없이 BEL·RA 를 그린다. 신계약 CSM 선: 분기=당분기 증분, 연도=연 누계(2026.2Q=1~2분기 누계, 툴팁·안내에 적음). VFA 표시·PAA 접기·발생사고요소 막대·세로축 생략 컨트롤과 그 코드·CSS 삭제(기본값 고정).
- **2026-10-10 IFRS17 섹션 3 콤보 오른쪽 막대를 발생사고요소 실공시값으로 교체 완료(미커밋·미배포)** — 마스터 항목 10~13 실값(실공시=꽉 찬 색 BEL·RA·미분리 / 계산값=같은 색 줄무늬, 항목 16·17 이 생기면 자동 / 추정=빗금) · 사이드카 3사(ABL·KDB생명·푸본현대)는 오른쪽 막대 없이 안내+표 「이 중 발생사고요소」 행 · 표에 「보험계약자산 상계 등 차이」 행(? 설명 포함).
  빌더 `lic_cells()` 한 곳, 패널 31KB(새 파일 없음). 실공시가 없는 분기 추정은 그 회사의 공시 분기에서 추정이 15% 넘게 틀리면 그리지 않음(AIG·악사·하나손보·라이나·메트라이프·카카오페이 등). 남은 것: LIC 2단계(항목 16·17) 적재 후 줄무늬 BEL·RA 가 실데이터로 확인되는 일.

## publishing 이 배포 전에 해야 할 일 (2026-10-10 designer)

- **`data/company_segment.json` 을 배포 파일 목록에 추가** — `scripts/android_push_and_deploy.sh` 의 `NEW_FILES`(154행)에 없으면 라이브 index·compare 가 재보사를 생보/손보에 섞어 보이거나 3구분이 안 된다(index 는 로드 실패 시 콘솔 경고만 남기고 옛 2구분으로 폴백). `tests/test_push_gate_wiring.py` 출처 표에 이 파일(마스터 아님, 수기 매핑)을 넣을지는 publishing 판단.
- **재보험·보증 3분류 반영 완료** — 8곳이 든 `kics_disclosure.json` 배포 선행 조건 충족. 같이 올릴 파일: `index.html` · `K-ICS.html` · `compare.html` · `IFRS17.html`(이름 약칭 1줄) · `공시보고서.html`(약칭 1줄) · `report-widget.js`(약칭) · `data/company_segment.json` · `data/compare/panel_compare.json`(`viz_build_compare_panel.py` 재실행 필수 — kics_disclosure.json 이 바뀌면 값이 움직인다) · `scripts/viz_build_compare_panel.py`.
- **IFRS17 섹션 3 콤보(이식 완료)**: 배포 파일에 `data/csm_combo/panel_csm_combo.json` 추가(`scripts/android_push_and_deploy.sh` `NEW_FILES`, 라이브 keep-list) + `IFRS17.html`. 배포 직전 `viz_build_csm_combo_panel.py` 재실행/`--check`(포트폴리오·CSM_waterfall·IFRS17_BS 마스터와 사이드카 `data/_derived/ilp_includes_lic.json` 이 바뀌면 값이 움직인다 — 사이드카는 빌더 입력이지 화면이 fetch 하는 파일이 아니라 keep-list 대상 아님). 새 배포 파일 없음(패널 JSON 내용만 바뀜). 발생사고요소 실값 반영 완료(2026-10-10 늦게). 테스트 배선은 `tests/test_push_gate_wiring.py` 에 반영됨. 알려진 화면 이슈: 예별손보 2025.4Q 는 경영공시 2-4 CSM 이 CSM_waterfall 과 다름(화면에 안내).
- **사별 비교 모바일 손해율 curve(2026-10-11)**: 새 배포 파일 없음(`compare.html` 만, 이미 라이브 keep-list). `data/compare/panel_compare.json` 의 `loss_curve.note` 문구 「현재가치 기준 손해율은 선에 넣지 않고 **범례 옆 숫자**로 적었습니다」가 모바일에서는 틀린다(모바일은 아래 표). 「…선에 넣지 않고 숫자로 적었습니다」처럼 중립 문구로 바꿔 주세요(`viz_build_compare_panel.py`, 카드 `?` 도움말에만 보임, 숫자 불변).
- 비교 모집단 변화(숫자 불변, 화면만): compare.html 「같은 유형 업계 중앙값」·손해율 가정 중앙값 — 손보 모집단에서 코리안리·서울보증 제외(이미 제외돼 있었음, 이제 재보험·보증은 아예 별도 유형). index KPI 「지급여력비율 중앙값·보험사 수」는 재보사 8곳이 들어와 47곳 기준. 재보사 8곳의 단독 순위·중앙값은 없음.

## 열린 일

- [ ] **사별 비교 손해율 curve 선 색(owner 확인)**: 데스크톱·모바일 공통 `PAL_LINE`(틸 `#4fb0a5`·살몬 `#ee8f72`·블루 `#7b9fe6`·머스터드 `#cdb04a`)이 흰 배경에서 선 대비 2.1~2.6:1(비텍스트 3:1 미달, 어두운 배경은 6.9:1 이상). 선 끝 라벨·선 모양·값 표가 있어 색만으로 구분하진 않는다. 「회사 키컬러가 있으면 그 색」 규칙은 IFRS17 에만 있고 compare 데스크톱은 안 쓴다 — 키컬러로 바꾸려면 데스크톱과 같이 바꿔야 한다(owner 팔레트 결정).

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
