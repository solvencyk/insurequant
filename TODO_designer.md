# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-10 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-10 IFRS17 섹션 3 콤보 차트·표 이식 완료(IFRS17.html, 미배포·미커밋)** — 묶음 누적 막대(왼쪽 잔여보장요소 CSM=회사 키 컬러·BEL/RA/PAA 탁한 톤, 오른쪽 발생사고요소 **추정**)+보조축 신계약 CSM+세로축 일부 생략(~)+VFA 합산(기본)/한 덩어리 토글, 아래에 값 표(CSM·BEL·RA·PAA·잔여보장요소 합계·발생사고요소(추정)·보험계약부채(BS)).
  owner 정정: CSM 증감 띠·증감 행은 만들지 않음 / CSM 색은 회사 키 컬러 그대로(없으면 사이트 에메랄드, 밝히거나 섞지 않음) / 값 표는 BEL→RA→CSM 순(차트는 CSM 이 맨 아래). 패널 `data/csm_combo/panel_csm_combo.json`(`scripts/viz_build_csm_combo_panel.py --check`), 발생사고요소 추정은 빌더 `lic_estimate()` 한 곳(실공시 확보 시 교체). 목업 파일은 삭제.
- **2026-10-10 재보험·보증 3분류 반영 완료** — index 시장지도(트리맵·목록·필터·버블)와 compare.html 이 `data/company_segment.json`(코드→구분 매핑, 마스터 셀 무변경)으로 생명/손해/재보험·보증 3구분. 재보험·보증은 접기 없이 전부 표시, 업계 중앙값은 만들지 않음.
  재보사 8곳은 K-ICS·compare·IFRS17(데이터 없는 회사는 드롭다운에 안 나옴)·검색창에서 깨짐 없음 확인. 남은 것: publishing 배포 선행 항목(아래).
- **2026-10-08 (5차) 사별 비교 차트·편집·공유 + 모바일 공통 수정** — 넓은 화면 유지율=파스텔 묶음 막대·손해율 가정=경과차년 꺾은선(Chart.js), 지표 요약 표 삭제, 헤더 공유 메뉴(링크 복사·스크린샷), 지표 편집(드래그앤드롭·추가 지표 6개), 탭 순서(사별 비교 맨 앞),
  index 버블맵 '추정' 기본 해제, 모바일 가로 넘침(숨은 ? 팝오버)·스크롤 스냅 해제·섹션 햄버거·팝업 폭·툴팁 바깥 탭 닫기·K-ICS 첫 열 고정. 상세 `docs/changelog_designer.md` 2026-10-08 (5차).
  owner 가 사용 사례 검증을 직접 하기로 해서 독립 QA 는 돌리지 않았다. 남은 것: 모바일 실기기 확인, 다운로드 팝업 제목의 모바일 글자(지금은 '테이블 다운로드(.xlsx)' 그대로).

## publishing 이 배포 전에 해야 할 일 (2026-10-10 designer)

- **`data/company_segment.json` 을 배포 파일 목록에 추가** — `scripts/android_push_and_deploy.sh` 의 `NEW_FILES`(154행)에 없으면 라이브 index·compare 가 재보사를 생보/손보에 섞어 보이거나 3구분이 안 된다(index 는 로드 실패 시 콘솔 경고만 남기고 옛 2구분으로 폴백). `tests/test_push_gate_wiring.py` 출처 표에 이 파일(마스터 아님, 수기 매핑)을 넣을지는 publishing 판단.
- **재보험·보증 3분류 반영 완료** — 8곳이 든 `kics_disclosure.json` 배포 선행 조건 충족. 같이 올릴 파일: `index.html` · `K-ICS.html` · `compare.html` · `IFRS17.html`(이름 약칭 1줄) · `공시보고서.html`(약칭 1줄) · `report-widget.js`(약칭) · `data/company_segment.json` · `data/compare/panel_compare.json`(`viz_build_compare_panel.py` 재실행 필수 — kics_disclosure.json 이 바뀌면 값이 움직인다) · `scripts/viz_build_compare_panel.py`.
- **IFRS17 섹션 3 콤보(이식 완료)**: 배포 파일에 `data/csm_combo/panel_csm_combo.json` 추가(`scripts/android_push_and_deploy.sh` `NEW_FILES`, 라이브 keep-list) + `IFRS17.html`. 배포 직전 `viz_build_csm_combo_panel.py` 재실행/`--check`(포트폴리오·CSM_waterfall·IFRS17_BS 마스터가 바뀌면 값이 움직인다). 테스트 배선은 `tests/test_push_gate_wiring.py` 에 반영됨. 알려진 화면 이슈: 예별손보·IBK연금 2025.4Q 는 경영공시 2-4 CSM 이 CSM_waterfall 과 다름(화면에 안내), AIG 는 잔여보장요소가 음수라 발생사고요소 추정이 크게 보임(안내).
- 비교 모집단 변화(숫자 불변, 화면만): compare.html 「같은 유형 업계 중앙값」·손해율 가정 중앙값 — 손보 모집단에서 코리안리·서울보증 제외(이미 제외돼 있었음, 이제 재보험·보증은 아예 별도 유형). index KPI 「지급여력비율 중앙값·보험사 수」는 재보사 8곳이 들어와 47곳 기준. 재보사 8곳의 단독 순위·중앙값은 없음.

## 열린 일

- [ ] **발생사고요소 실 BEL·RA 확보 시**: 빌더 `lic_estimate()` 교체 + 화면 오른쪽 막대를 BEL/RA 두 조각으로(정찰 `data/disclosure/_meta/lic_scout_20261010.md`). index 트리맵 재보험·보증은 손해 아래 칸(3열 가로 배치가 필요하면 알려 주세요). 후속 후보: 「CSM 확대(CSM만 자동 스케일)」 토글(owner 정정으로 지금은 안 만듦).

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
