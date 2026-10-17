# Insurequant Designer TODO (Stage 5)

> 갱신 2026-10-18 · 프롬프트 `docs/agents/claude-agent-designer.md` · 이력 `docs/changelog_designer.md`
> 2026-10-07 정리 전 전문(BS-TACCOUNT·DESIGN-V2·MOB 블록 포함)은 `docs/todo_archive_designer.md` 맨 위에 있다. designer 는 push 하지 않는다.

## Status (최신 3개)

- **2026-10-18 손해율 가정 구분 선택기 · 2026 3분기 안내 팝업 완료(compare.html · IFRS17.html · theme.js · 빌더 · 점검 스크립트, 커밋·미배포; owner TODO 일괄 처리)** — 선택기: 합계 · Non-Par · Indirect-Par · Direct-Par(공시 이름 그대로, 기본 합계라 기존 숫자 불변), `panel_compare.json` 153KB 로 재생성; 팝업: `theme.js` `NOTICE`, 5페이지 1회, 분석 호출 없음.
  독립 검증: 곡선 최대 0.05pp(마스터 재계산), 합계 선택 시 HEAD 와 동일, 1280/375/다크 위반 0 · 콘솔 0, 팝업 428건 위반 0. 남은 것: IFRS17 현재가치 구분 소계 이중 반올림(publishing 티켓 `20261018T0700Z`) · 팝업 제목 · 숨김일(12-31) · 범위 owner 확인 · 배포 때 HTML 2개 + `panel_compare.json` + `theme.js` 한 묶음.
- **2026-10-13 발행현황 추정 행 툴팁 꼬리 + 새 JSON 47사 재점검 완료(K-ICS.html·점검 스크립트 2종, 커밋·미배포; 티켓 20261013T0030Z)** — `estimated: true` 행이 있는 해의 막대 툴팁에 「추정(원장 미갱신)」 한 줄(하나손해 2026). DB손해 신종 콜 칸은 날짜만(2030-09-01), 하나손해는 최근 발행금리 「—」·총발행액 1,999억·2026 막대·콜 2029-05-14 (1,000억)로 확인.
  새 JSON(HEAD 392efee2, publishing 보정 커밋 포함) 47사 x 1280/375/다크 141회: 도넛·숫자 줄·경과조치 기발행 후순위가 JSON 과 일치(`scripts/check_kics_donuts.py`), 전망·발행현황(`check_kics_forward_note.py`·`check_kics_capsec_cells.py`) 위반 0·콘솔 0·넘침 0. 남은 것: 없음.
- **2026-10-13 K-ICS 전망 거짓 개선 제거 · △ 표기 · 375px 도넛 툴팁 폭 · 콜일 칸 내구성 완료(K-ICS.html·시험·검사 스크립트, 커밋·미배포; 티켓 20261012T2236Z)** — 자본잠식 해(`capacity_exhausted`·`basic_capacity_exhausted`)는 선·점 null, 툴팁 「자본잠식」, 노트 「2030 변화」 「—」 + 안내 한 줄, 노트·y축 음수 전부 △. 도넛 긴 줄을 2줄로 나누고 「보완자본형이면 X%」는 표시값과 다를 때만(6사 박스 329~349 -> 전부 캔버스 325 안). 콜일 칸은 잔액 null·빈 칸·표식이어도 날짜만, 날짜 아닌 값은 대시.
  47사 x 1280/375/다크 141회 위반 0·콘솔 0·넘침 0(`scripts/check_kics_forward_note.py`, 옛 판에 돌리면 예별 +41.8%p·6사 폭 초과를 그대로 잡음), 콜일 합성 6변형 통과(`scripts/check_kics_callcell.py`), 시험 `tests/test_kics_forward_note.py` + 기존 4종 통과. 남은 것: 없음(배포는 owner GO, 발행사 JSON 변경(한도 10% 표기 등)은 publishing 커밋 후 재점검).

## publishing 이 배포 전에 해야 할 일

- 2026-10-13 main `970259b8` 배포로 전부 끝났다(`data/company_segment.json`·`data/csm_combo/panel_csm_combo.json`·`data/compare/panel_compare.json`·`kics_duration_gap.json` 이 origin/main 에 있음, ILP 시트는 `public_exports/보험계약부채.json` 로 공개됨). 전문은 `docs/todo_archive_designer.md` 맨 위.

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

- 페이지 5개: `index.html`(시장지도·버블) · `K-ICS.html` · `IFRS17.html`(7패널, 1=재무상태표 T계정) · `공시보고서.html`(배당현황) · `compare.html`(사별 비교).
- 차트: Chart.js(IFRS17 패널 2~6) · ECharts(CSM 워터폴·treemap·버블). 색은 `IQTheme.chart()` 로 CSS 변수를 읽는다(라이브러리는 `var()` 를 못 먹는다).
- 로컬 미리보기 `python -m http.server 8000`. 프리뷰 창은 `window` scroll 이벤트를 안 뿜는다 — 스크롤 스파이는 합성 이벤트로 검증.
