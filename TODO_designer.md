# Insurequant Designer TODO (Stage 5)

> Last updated: 2026-09-22 · Stage 5/5 — designer
> Prompt: docs/agents/claude-agent-designer.md (§5 design system formalized 2026-06-16) · Changelog: docs/changelog_designer.md

Session start: read this file + `claude-agent-designer.md` + the page(s) in scope (root HTML files). Publishing ([`TODO_publishing.md`](TODO_publishing.md)) owns master JSONs; designer only reads them and decides how they render. English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

Stage 5 = HTML structure / styling / responsive breakpoints / A11y / chart layout. Desktop pages are in production; KEYCOLOR-V1 K-ICS cancelled by owner (IFRS17 구현 불만족). Mobile scope confirmed; M1 foundation done; full mobile pass open.

**Recent (2026-09-22, K-ICS 금리 민감도 패널 — 순자산 듀레이션/컨벡서티 2카드 -> 자산D/부채D/듀레이션갭 3카드, owner 직접 지시):**
`K-ICS.html` 1파일 +54/−28. 카드가 읽는 마스터를 `kics_rate_sensitivity.json`(±bp 평행이동 표의
가용자본 파생값)에서 신설 `kics_duration_gap.json`(경영공시 금리위험액 현황 표)으로 바꿨다.
**컨벡서티 카드는 폐지** — K-ICS 상승/하락 충격이 비대칭이라(39사 하락/상승 편미분 비율 중앙값
1.20, 대칭 평행이동이면 1.02~1.05) 2차 차분이 곡률이 아니라 비대칭을 잰다. 억지로 계산하면
이론값(D²+D) 대비 1.7~5.7배로 배율도 회사마다 제각각(삼성생명 116 vs 41, 메트라이프 153 vs 27).
아래 ±bp 차트·표는 그대로라 원자료는 안 사라진다.
`.dur-strip` 2열→3열(모바일 1열 규칙 재사용), `<h2>` 부제 문구 교체, 툴팁 산식 교체 + "기간구조
충격이라 2%로 나누는 건 근사" 단서 명시. 값은 마스터 컬럼을 그대로 렌더(JS 재계산 없음).
엣지 3종: 갭 null→스트립 숨김(카카오페이손보 3분기) · 부채D null→그 칸만 `—`+"금리부부채 ≤ 0"
(AIG손해·라이나생명, 책임준비금 음수) · `비고` 있으면 노트 하단 노출.
fetch 는 기존 `kics_rate_sensitivity.json` 과 같은 fail-soft 패턴, 로드 후 재렌더로 수렴.
검증: `test_deploy_assets` 11 passed · 내장 브라우저로 삼성생명 5.94/6.60/△0.26 · 라이나생명
9.99/—/6.65 · 한화생명 8.89/7.84/1.16 확인 · 콘솔 에러 0건. 커밋 `fa21ec9`.
**남은 것**: 분기 셀렉트는 여전히 `kics_rate_sensitivity`(4개 분기)에서 나온다 — 듀레이션갭
마스터는 7개 분기(2023.2Q~)라 2023.2Q·2023.4Q·2024.2Q 3개 분기가 화면에서 도달 불가다.
셀렉트 소스를 합집합으로 넓힐지는 owner 판단 대기.

**Recent (2026-09-21c, IFRS17·기타공시 헤더 셀렉트+토글 이식 · common.css 승격 · 섹션 앵커 착지 오프셋 수정 — owner 발주 inbox `20260921T0500Z`/`0510Z` + owner 직접 지적, 커밋만·라이브 미배포):**
- **K-ICS 에서 먼저 나간 패턴(`3573509`)을 IFRS17.html·공시보고서.html 로 이식.** `#company` 셀렉트를
  `<header>` 안 `.header-select-row` 로 올리고(IFRS17 은 `#coSwatch` 키컬러 점 동반), `기준`(IFRS17
  `wfPeriod`: 연도|분기)·`기간`(공시보고서 `period`: 분기|연도) 셀렉트를 세그먼트 토글로 바꿨다.
  **실제 `<select>` 는 `.sr-only` 로 DOM 에 남긴다** — `.value`/`change` 계약이 그대로라 기존 JS
  (IFRS17 L1788·1859·2246, 공시보고서 L239·L300·L378)를 한 글자도 안 고쳤다.
- **디자인 시스템 단일 소스**: `.header-select-row`/`.header-select-label`/`.control-group`/
  `.control-label`/`.seg-toggle`/`.seg-btn`/`.sr-only` + 모바일 오버라이드를 `common.css` 로 승격하고
  K-ICS.html 의 페이지 로컬 정의는 삭제(§5). 3페이지가 같은 정의를 본다.
- **섹션 앵커가 헤더 밑으로 파고드는 버그 수정(owner 가 라이브 K-ICS 에서 지적).** `common.css` 의
  `scroll-padding-top` 이 `--header-h:76px` **하드코딩**이라, 셀렉트가 헤더로 올라가 헤더가 118px 이
  된 뒤 섹션이 88px 에 착지해 **윗부분 30px 이 헤더에 잘린 채** 보였다. `--iq-hdr-h`(theme.js `hdrH()`
  실측)를 쓰도록 바꿔 `calc(var(--iq-hdr-h, var(--header-h)) + 12px)` — 페이지·뷰포트별로 자동 추종한다.
  **같은 하드코딩이 스냅 트랩도 되살리고 있었다**: `scrollTo(0)` 이 31 로 끌려가 맨 위에 못 가던 것이
  0 으로 복구됐다(4페이지 전부 `topReach=0` 실측). IFRS17·공시보고서도 이번에 헤더가 커졌으니
  이 수정이 없으면 배포와 동시에 같이 깨졌을 자리다.
- **검증(헤드리스 Playwright, 1400px·375px, 스크래치패드 throwaway 2종)**: ① 2,000px 스크롤 후 헤더
  셀렉트 visible(데스크톱 top=72/모바일 68, 3페이지) ② IFRS17 `KR0069` → emptyHint 숨김·dashHost
  표시·스와치 `rgb(20,40,160)` ③ 토글 클릭·ArrowRight/Left 로 `wfPeriod`/`period` 값 전환 ④
  `?company=KR0069` 진입 반영 ⑤ **섹션 착지 전수**: 회사 선택 후 K-ICS 4칩·IFRS17 7칩, 데스크톱·모바일
  모두 gap 12px(문서 끝 칩만 더 큼), 음수 0건 ⑥ `validate_deployed_js.py --no-live` 4페이지 RED=0 ·
  `pytest tests/test_deploy_assets.py` 11 passed · uncaught pageerror 0. 스크린샷
  `artifacts/designer_shots/20260921_header_toggle_v2/`.
- **무관 확인**: 4페이지 공통으로 GA4 비콘이 `www.google.com/g/collect` 로도 나가는데 CSP `connect-src`
  에 그 도메인이 없어 콘솔 에러가 뜬다. index.html 포함 전 페이지·변경 전에도 나던 기존 조건이라
  이번 범위에서 손대지 않았다(고치려면 CSP 수정이라 별건).

**Recent (2026-09-21b, K-ICS 보험사 선택 헤더 고정 + 제목 이동·부제 삭제 + 기간/경과조치 토글 — owner 발주(직접 지시), inbox `20260921T0430Z`, 커밋만·라이브 미배포):**
- **대상 `K-ICS.html` 하나(모델: Sonnet 5).** ① `#company` select 를 `.header-select-row`(신설, L143-179)로
  옮겨 sticky `<header>` 안에 두었다 — `theme.js`의 `hdrH()`가 header 높이를 실측해 `--iq-hdr-h`로 내리므로
  하드코딩 없이 자동 반영(지난 라운드 71/88px 하드코딩 사고 재발 없음). ② 첫 `.panel`(h2+lede)을 삭제하고
  `<h2>원보험사별 K-ICS 지급여력비율 변동 추이</h2>`를 `#sec-trend` 상단으로, `분기 공시 기준 시계열입니다.`는
  완전 삭제(옮기지도 숨기지도 않음, owner: "꼭 맞는 말도 아니니까 걍 지워라"). ③ `<select id="period">`/
  `<select id="transition-mode">`는 DOM에 `.sr-only`로 남기고(`.value`/`change` 계약 무변경, 기존 JS 8곳+
  이상 한 글자도 안 고침) 위에 `role="radiogroup"` 세그먼트 토글(`setupSegToggle()`, L366-395)을 얹어
  클릭·키보드(←→·Space)로 `selectEl.value`+`dispatchEvent('change')`를 실행. 기간 기본값 `분기`로 바꿔
  회사만 선택해도 바로 렌더(안내문 "보험사와 조회 기간을..." → "보험사를 선택해 주세요"로 정정).
- **A11y 즉시수정(추가발견)**: `.seg-btn.active`의 포커스 링이 배경과 같은 `--primary` 색이라 안 보이는
  문제를 실측 중 발견 — `.seg-btn.active:focus-visible{outline-color:var(--on-primary)}`로 즉시 수정
  (신설 컴포넌트 포커스 가시성, 기존 렌더값 변경 아니라 owner 승인 없이 처리). 대비 실측: 라이트
  `#fff`/`#0f6e68` 6.09:1, 다크 `#0c110f`/`#54b3aa` 7.62:1, 라벨 `--muted`/`#fff` 4.69:1 — 전부 AA 통과.
- **검증 7항목(헤드리스 Playwright, `scripts/_probes/_20260921_verify_header_toggles.py`, 미커밋
  throwaway + 로컬 http.server)**: ① 데스크톱 1400px·모바일 375px 둘 다 2000px 스크롤 후 `#company`
  visible=true ② 라이나생명+기본 `분기` → tbody 40행+차트 visible ③ `연도` 토글 → 표 헤더
  `2023.4Q~2026.2Q` ④ 한화생명 2024.4Q `적용전`↔`적용후` 값 차이 확인(`pre_vs_post_differ=true`)
  ⑤ `?company=라이나생명보험&period=year` 진입 → 토글이 `연도`로 반영 ⑥ `validate_deployed_js.py --no-live`
  RED=0(4페이지 전부) ⑦ pageerror 0. `pytest tests/test_deploy_assets.py` 11 passed. 스크린샷
  `artifacts/designer_shots/20260921_header_toggles/*.png`.
- **발견(범위 밖, spawn_task `task_1dc9b489`)**: 모바일 375px `기타공시` 탭이 다운로드 CTA에 가려 겹치는
  기존 버그 발견 — HEAD(변경 전) 버전을 재현해 이번 변경이 원인이 아님을 확인(`common.css`
  `.header-row`/`.tabs`/`.download-cta` 공유 이슈, 4페이지 영향이라 별도 티켓으로 분리, `common.css`는
  이번 티켓에서 무수정). 상세: `inbox/designer/20260921T0430Z…` 답변.

**Recent (2026-09-21, K-ICS 금리민감도 `IQP is not defined` 라이브 사고 복구 — owner 신고, inbox `20260921T0057Z`, 커밋만·라이브 미배포):**
- **원인**: `2dbc4ca`(2026-09-20 섹션 네비 통일)가 `IQP()` 정의를 지우고 호출 2곳만 남겨,
  적용후 데이터가 있는 39사 중 36사에서 `renderSensDetail()`이 죽고 있었다(3사만 리터럴 색이라 생존).
  예외가 placeholder 리셋 줄 앞에서 터져 "미공시" 문구가 직전 회사 것 그대로 눌러붙었다.
- **수정 2건**: ① `IQP()`를 `K-ICS.html:273`에 원문 그대로 복구(팔레트 B 색·호출부 무변경).
  ② `renderSensDetail`(`K-ICS.html:1351`)을 try/catch 래퍼로, 본문을 `renderSensDetailInner`
  (`:1362`)로 분리 — 어떤 예외든 `sensHideAll()`로 강제 리셋해 이 버그류(정의 삭제·호출부
  잔존) 재발 자체를 무해화했다.
- **배포 4종 스윕**: 정적 스캐너(`scripts/_probes/_20260921_scan_undefined_calls.py`, 문자열/
  주석/템플릿리터럴 제거 후 호출-정의 대조)로 훑은 결과 실결함은 `IQP` 하나. `IFRS17.html`
  `formatter`·`K-ICS.html` `afterDraw`는 object-shorthand-method 오탐으로 확인.
- **런타임 검증**(로컬 서빙+Claude Browser, `?iq_internal=1`): 39사 전건 예외 0·차트/표 전부
  visible. 엣지케이스 3종(미선택/버그 인위재현/재렌더 복구) 전부 의도대로. `pytest
  tests/test_deploy_assets.py` 11 passed. 스크린샷(라이나생명보험 2026.2Q) 저장 완료.
- 마스터 JSON 무수정, main cherry-push 없음. 상세: `docs/changelog_designer.md` 2026-09-21,
  `inbox/designer/20260921T0057Z__owner__ALL_2026.2Q__kics_sens_IQP_referenceerror.md` 답변.

**Recent (2026-09-15c, 손해율 버블차트 폐지 → 적층막대 일원화 — owner 질의("비용 대비 효용"), 커밋만·라이브 미배포):**
- **owner 질문: 손해율×사업비율 버블이 난잡함에 비해 값어치를 하냐, ESR 랭킹만 남기고 치울까.
  재서 답했다 — ① 버블은 빼고 ② 패널 자체는 남긴다.**
- **①-a 2D 자체는 정보가 있었다.** 손해율-사업비율 상관 **r = −0.096**(대각선이 아님). 합산율이
  1.0pt 이내인 쌍 56개에서 손해율 차이 평균 **10.3pt**·최대 **35.6pt**(明治安田 37.7 vs SBI 73.3).
  즉 "합산율 하나로 뭉개면 안 된다"는 맞다.
- **①-b 그런데 적층막대가 그 정보를 안 잃는다.** 손해율·사업비율 두 값이 구간으로 그대로 보이고,
  **합산율은 막대 길이 + 숫자**(버블에선 색 농도 하나뿐이었다 — 헤드라인 지표에 가장 약한 채널을
  주고 있었다). 버블만의 추가 정보는 "원 크기=보험료" 하나인데 그건 이미 정렬 순서가 담당한다
  (10만배 차이라 범례에 「面積比≠保険料比」 변명을 달고 있던 채널이다).
- **①-c 실측 비교(1280px)**: 회사명 표시 버블 30사 중 일부만(라벨 충돌) → 막대 **31사 전건**.
  겹친 쌍 버블 10조(최악 −20.4px) → 막대 **0조**. JS 에러 0, 가로 넘침 0.
  **ECharts CDN(1,029,203 bytes)이 이 페이지에서 통째로 빠졌다** — 유일한 사용처가 버블이었다.
  HTML −19,292 bytes.
- **② "ESR 랭킹만 남긴다"는 안 된다 — 재보니 손보 ESR 은 5사뿐이고 그중 3개가 지주사다**
  (au損保·明治安田損保 + SOMPO HD·東京海上 HD·MS&AD HD). 東京海上日動·三井住友海上·損保ジャパン·
  あいおい 같은 **대형 사업회사는 ESR 랭킹에 아예 없다.** 손해율 패널을 치우면 손보 31사 중 26사가
  화면에서 사라진다(마크업 주석에도 "이 회사들의 유일한 입구"라고 적혀 있다).
- **③ 막대 척도에 버블과 같은 병이 남아 있어 같이 고쳤다.** 꼬리 2사(ヤマップ 230.0%·全管協
  237.4%, 둘 다 事業費率>100%)가 트랙의 **49%**를 먹어 29사가 왼쪽에 뭉쳤다. 버블이 쓰던 것과
  **같은 선·같은 이유**(事業費率>100% = 보험료보다 비용이 큰 구조적 이상)로 눈금에서 빼고 오른쪽
  끝에서 打ち切り(사선 해치, 실수치는 우측 숫자·title 로 상시 개시). 실측 89.3%~98.4% 폭차
  **27px → 52px**, 대형4사 12px → 23px.
- **③-b 눈금 기준을 `list`(접힌 5사) → `full`(31사)로.** 종전엔 「もっと見る」로 척도가 바뀌고,
  접힌 상태에선 maxV=97.1 이라 **100% 기준선이 오른쪽 끝에 붙어 있었다**(실측). 이제 양쪽 82% 고정.
- **④ 칩: 정직하게 재니 내가 또 늘렸길래 도로 줄였다.** 버블 뷰 4칩/잔글씨 4줄 → 일람 뷰가
  5칩/**5줄**이 됐다(버튼 뒤에 있던 6칩 범례가 상시 노출로 바뀌어서). 색 칩 2→1 병합 + caveat 칩
  3줄을 **1줄**로 접어(印＝値に注記あり：Δ／OCR／Σ) **3칩/4줄**. 배지 자체는 각 행에 그대로고
  긴 설명은 이미 배지 `title`·행 `aria-label` 에 있다 — 범례에서 중복이던 부분만 뺐다.
  caveat 칩은 `data-caveat-cat` 으로 **실제로 그 印이 붙은 행이 있을 때만** 나온다.
- **다음**: ESRランキング 범례 8개는 그대로다(2026-09-15b 에서 넘긴 건, owner 판단 대기).
  일본 손보의 진짜 핵심축은 「引受으로 버느냐 運用으로 버느냐」인데(東京海上 引受利益은 経常利益의
  **5%**, 三井住友 17%, 損保ジャパン 13% — 실측) `pl_underwriting_profit`/`pl_investment_pl` 이
  5~6사뿐이라 아직 화면에 못 올린다. jp 레인 수집 타깃으로 넘긴다.

## 🔴 Open — P1

### BS-TACCOUNT — IFRS17.html Panel 1 (was Panel 7) 재무상태표 (formerly BS-DRILLDOWN, renamed 2026-08-14d)
Now a T-account at the **top** of the dashboard (owner's own explicit ask this round — `inbox/designer/20260814T1250Z__owner__IFRS17__bs_taccount_top_panel.md`, answered), not a mockup panel anymore in intent. Data-contract-driven by `섹션`/`레벨` fields on `IFRS17_BS.json` (parser landing separately, `inbox/parser/20260814T1250Z…`) — no item-number branching in the render code.
- [x] **T-account + reposition (2026-08-14d)**: moved above Panel "2) CSM 이동" (was 7, all panels renumbered 1-7). 좌 자산 / 우상단 부채 / 우하단 자본, right-column height ∝ value ratio. Per-zone `+` (`.subtoggle`, reused from the PL panel) toggles a 레벨2 detail list; disabled+`aria-disabled`+"세부 미공시" when a section has zero 레벨2 rows (covers both "parser hasn't landed detail yet" and "company doesn't disclose" with the same code path — no special-casing needed). 준비금 kept structurally separate from 자본 (own side-note block, excluded from the capital total/detail) per owner's explicit double-counting warning.
- [x] `EQ_SECTION_LEVEL_BRIDGE` bridges the *current* pre-migration schema (items 1-7, no 섹션/레벨 columns yet) so the frame renders today; disappears in effect the moment parser's real columns land (row data wins over the bridge automatically, zero HTML changes needed).
- [x] **This time actually deleted** (not hidden) the 08-14b/c dead L2/L3 functions — preserved-uncalled twice already, proven unreusable both times because the schema kept moving under them. History is in the changelog, not in commented-out code.
- [x] Verified 4 companies incl. all 3 of owner's named edge cases (has-detail / listed-no-detail-yet / non-listed-never-has-detail / zero-BS-data). 0 console errors. `pytest tests/test_deploy_assets.py` 10/10.
- [x] **Real-viewport recheck (2026-08-18, resolved after 3 carried-over sessions)**: this session's Browser pane returned a real `window.innerWidth===375` (not the `0` bug from 08-14b/c/d) — confirmed via `resize_window`+JS query: `.bs-t` switches to `flex-direction:column`, detail/sub rows collapse to 1 grid column, `body.scrollWidth` never exceeds `innerWidth` (no horizontal overflow), 0 console errors. Screenshot pixels still unavailable (pane still doesn't composite for actual frame capture), but this is real DOM/computed-style verification, not a skip.
- [x] **Schema landed same session** (owner shrank scope to 13 detail items, not the original ~60 — `inbox/_resolved/20260815T0100Z__parser__MULTI__ifrs17bs_taccount_schema_ready.md`): confirmed compatible with zero HTML changes (contract design worked as intended). Data shape + render-code field matching verified by direct inspection (`fetch(...,{cache:'no-store'})` vs. `renderBsZone`); a true fresh-browser render wasn't achieved that session — local server's HTTP cache kept serving the pre-migration snapshot. **2026-08-18: confirmed live** — 자산/부채/자본 `+` all enable and render real rows for KR0008 (Tier-1), verified via `.click()` + `box.hidden`/`getComputedStyle(...).display` in a clean preview.
- [x] **Partial-detail confusion fixed (2026-08-15, inbox `20260814T1710Z__validation__IFRS17__bs_detail_is_highlight_label_it.md`)**: validation caught that the 레벨2 detail is an intentional "≤15-line highlight" (owner scope, not full closure — `scripts/build_ifrs17_bs.py`), so a section's shown detail routinely undershoots its total (worst case validation found: 신한라이프 자산 세부 17-21조 vs 59조+ total) with zero on-screen explanation — reads as broken. Fixed by computing a "기타·미표시" residual row client-side (`total − Σshown`, no master change) plus a short caption clause. Re-verified on the exact worst-case company (신한라이프/KR0094): shown-detail + residual now ties out to the total within rounding.
- [x] **🔴 `+` toggle dead-on-arrival bug fixed (2026-08-18, owner live-QA `inbox/designer/20260818T0026Z` D-3)**: `.bs-l2-rows{display:flex}` was beating the UA `[hidden]{display:none}` default in cascade, so `box.hidden` toggling never changed the rendered layout — the button looked completely dead (aria-expanded flipped, screen didn't). Fixed with one CSS rule, `.bs-l2-rows[hidden]{display:none}`. Audited all 4 HTML pages for the same display+hidden collision pattern — none found elsewhere (K-ICS/index/공시보고서 don't use the `hidden` attribute at all; the PL 재보험 subrow toggle uses `style.display`, unaffected).
- [x] **법정준비금 재배치 (2026-08-18, D-4)**: moved from a standalone `#bsReserveNote` block (deleted, along with its render code + CSS) into the 자본 zone's own detail list, as indented sub-rows anchored right after the "이익잉여금" row (name-matched, not item-number — new `renderReserveSubrows()`). Still excluded from the shown/residual sum (rendered via a separate pass, owner's double-counting warning preserved) — verified on KR0008 the residual stayed a small △81억 (not off by the ~6.95조 it would be if reserves had leaked into the sum). Companies without an 이익잉여금 row (non-listed) get the sub-rows inserted before the residual row instead.
- [x] **버그 수정(같은 대화, owner 즉시 재확인): 연도모드 "직전 3년" 위반** — 재사용한 `selectPeriods()`가 무상한(전체 4Q) 반환이라 BS가 2021년까지 있는 회사(메리츠화재·현대해상·KB손보·코리안리 등)에서 6열까지 붙었음. BS 전용 `eqYearPeriods()`(최신+직전3개년말 하드캡, `wfYearBuckets()`와 동일 패턴) 신설로 교체, 공유 함수는 미변경(CSM/PL/NB 마스터는 실측상 전부 2023년 시작이라 이 결함이 잠재적일 뿐 미발현 — 확인만 하고 안 건드림). 6개사 전부 재검증 완료.
- [x] **시계열 원천 테이블 신설 (2026-08-19, owner 채팅 발주)**: T자 밑에 다분기(`#wfPeriod` 연동, `selectPeriods` 재사용) 표 추가 — 분기=직전5분기 / 연도=최신+직전3개년말, 분기 미제공사는 CSM 패널과 동일 문구의 stub. 자산/부채/자본[+] → 세부[+] → 자본 세부의 "이익잉여금"은 자체 중첩 [+]로 법정준비금(이제 4항목 — `보증준비금 기적립액` 신규, 생보 16사만) 한 겹 더. 항목은 선택 기간 전체의 이름 유니온(`eqUnionNames`)이라 항목번호 하드코딩 없음. 상위 토글 접을 때 중첩 하위 토글도 재귀 리셋(`collapseGroup`). `renderBsTable`/`buildBsTableDom`/`eqHasQuarterly`/`eqUnionNames`/`eqValByName` 신설. 브라우저 실측 다수(연도/분기 헤더 owner 예시와 정확 일치, 생보/손보 준비금 항목수 차이 확인, stub 전환, zero-BS-data 회사 무충돌, 375px 표 자체 스크롤). `pytest` 10/10.
- [x] **(종결 2026-08-20)** Deploy 차단 해소 — 게이트 `RED=0 YELLOW=276 exit=0`, main 배포 실제로 진행됨(`a0979b9`, 오늘만 3회). 원문: (unrelated to this rebuild, standing condition). No push attempted.

### DIVIDEND-PAGE — 공시보고서.html 배당현황 (built 2026-08-15)
Owner's C-4 chain, designer leg (`inbox/_resolved/20260814T2230Z__parser__MULTI__dividend_json_ready_for_gongsi_page.md`). Fills the page's long-standing "준비 중" shell — no new tab/page, per owner's explicit constraint.
- [x] Company selector (24-company registry, drawn from `dividend.json` itself, not the 39-company kics universe — the 15 non-listed companies structurally never have this DART disclosure, so they're left out of the picker rather than showing a permanent empty stub) + KPI strip + company-level table (항목 1-7) + per-종류주 mini-tables (항목 8-10, auto-detected classes, no hardcoded company list).
- [x] `0` vs `"정보없음"` kept strictly separate everywhere (owner's own repeatedly-flagged trap) — verified on real data, not just written and assumed.
- [x] `claude-agent-designer.md` §1 doc-table gap fixed (my half of `test_docs_agree_with_what_pages_fetch`).
- [x] **(종결 2026-08-20)** `dividend.json`은 **git 추적 중**이고(`git ls-files` 확인) 2026.2Q 24사까지 배포됐다. 'untracked·deploy far off' 전제 stale. 원문:, `claude-agent-publishing.md` doesn't mention it yet, and `validate_data_contract.py` doesn't wire this master into its gate at all — all three already ticketed in `inbox/publishing/20260814T2230Z` (P-1/P-2/P-4), not this stage's files to touch.
- [x] **Period selector added (2026-08-18, owner live-QA `inbox/_resolved/20260818T0026Z` D-5)**: the "shows all 14 raw quarters" gap above is closed — added a K-ICS.html-style 기간(분기/연도) toggle. Quarter mode = last 5 quarters, year mode = latest + prior 3 fiscal year-ends (partial current year labeled "…누계", e.g. "2026.2Q누계"), both derived from `dividend.json`'s own data (`GLOBAL_QUARTERS`), not hardcoded. Window is **global** (same header columns regardless of which company is selected), not per-company — deliberate, so a company's missing quarter shows as a 정보없음 cell under a stable header rather than shifting the whole column set. Also removed 항목1 주당액면가액 (owner: "필요없으니까 빼고"). KPI strip decision: stays anchored to "latest 4Q" regardless of the new period selector (a multi-quarter window doesn't map to a single KPI snapshot) — documented in `#divKpiCap`'s caption per owner's explicit ask to decide-and-state. Verified live on KR0008: quarter headers 2025.2Q~2026.2Q, year headers 2023/2024/2025/2026.2Q누계, `0`-vs-정보없음 distinction intact (현금배당금총액 real 0 for 3 quarters vs 정보없음 for the undisclosed 2026.2Q cell), 0 console errors, 375px no horizontal overflow.
- [x] Real-viewport mobile recheck done for this page too (2026-08-18, same session as BS-TACCOUNT above) — `resize_window`+JS query confirmed `.controls` wraps, period selector visible, no horizontal overflow at 375px.

### KEYCOLOR-V1 — 회사 키컬러 액센트 시스템 ~~(K-ICS 취소, IFRS17 재검토 대기)~~
IFRS17 적용 완료 2026-06-13. K-ICS 적용은 **owner가 2026-06-17 취소** (IFRS17 구현 불만족). IFRS17 키컬러도 재검토 필요 — owner 피드백 대기.
- [x] IFRS17 적용 완료 (2026-06-13)
- [~] K-ICS 적용: **owner 취소 (2026-06-17)**
- [ ] (보류) 전체 키컬러 방향 재검토 — owner 피드백 후

### DESIGN-V2 — de-AI 디자인 오버홀 (proposal delivered 2026-06-11, awaiting owner sign-off)
Owner complaint: site looks AI-generated. Audit done (4 pages + barabom.me reference — actual findings: Spoqa Han Sans Neo webfont + restrained neutrals + 0.1-0.2s micro transitions, NOT heavy animation). Phases:
- [~] **P1 quick wins** — **3/4 이미 배포돼 있다 (2026-08-30 `origin/main` 실측)**: Pretendard 4페이지+common.css 전부 적용 · `tabular-nums` 적용 · `rel="icon"` 4페이지 전부 존재. **남은 것은 둘뿐** — 부트스트랩 잔재 색(`#0d6efd`·`#f8f9fa`)이 4페이지+common.css 에 아직 있고, `og:image` 는 0건이다. 종전 문구 —: Pretendard Variable + `font-variant-numeric:tabular-nums` 전역 / 탈부트스트랩 팔레트(#0d6efd·#f8f9fa 교체, 잉크+페이퍼+딥블루 1액센트) / favicon(IQ 모노그램)+OG+meta description / footer(출처·기준분기·면책) / 이모지 placeholder 제거 / radius 12→6px / Chart.js·ECharts 색 CSS 변수화 (기본 teal/pink 퇴출). [부분 착수: P1-QUICKWIN 일부 done 2026-06-12, 팔레트 교체는 보류]
- [x] **P2 structural (1~2d)**: ✅ common.css · ✅ index 히어로 KPI 스트립+typeahead · ✅ scroll-reveal · ✅ 차트 공통 테마 · ✅ KPI 카운트업 애니(index 3개+IFRS17 Panel7 4개, ease-out 600ms, 2026-06-20) — **완료**
- [x] **P3 — 문서가 낡아 있었다(2026-09-19 정정, 이 트리에서 직접 확인).** 다크모드는 이미 구현돼 있다:
  `theme.js` L93-94 가 `id='iqThemeToggle'` · `class='theme-toggle'` 버튼을 **런타임에 주입**한다(그래서
  HTML 을 grep 하면 0건 — 없는 게 아니라 JS 가 만든다). `common.css` 에 `:root[data-theme="dark"]` 토큰
  (L76)·`@media (prefers-color-scheme:dark)`(L85)·`.theme-toggle` 스타일(L151·L160)이 전부 있고,
  OS 자동감지가 아니라 사용자가 누르는 토글 + localStorage 고정이다. "M3 잔여(도넛 stack·범례) 흡수" 도
  아래 M3 절에서 이미 둘 다 [x] — P3 는 사실상 완료다.
- [x] **TREEMAP-SCALE**: 트리맵 색 임계 앵커 130/200% + 범례 임계 표기 — done 2026-06-13 (권고선=130%, 민감도 패널 150%→130% 정합)
- [ ] **COMPANY-ACCENT**: 회사 키컬러는 배경 틴트 대신 "액센트 1곳" 원칙(패널 제목 2px 룰 + 회사명 칩 + 차트 주 시리즈, 저채도 변형 23사 맵) — 시안 owner 승인 후

## 🟠 Open — P2

### ✅ 2026-09-20 2차 — owner 반려 8건 반영
1차(팔레트 B·K-ICS 네비·툴팁)를 라이브에 올린 뒤 owner 가 8건을 반려했다. 아래가 그 처리다.

- [x] **네비·툴팁을 IFRS17 에도**(owner: *"왜 K-ICS 에만 했노"*). owner 후속 지시로 **종류를 통일**했다 —
  IFRS17 도 같은 좌측 네비 7항목(재무상태표·CSM 이동·CSM 시계열·상각 스케줄·손익 워터폴·NB 배수·민감도).
  IFRS17 은 분석 패널이 `<template id="dashTpl">` 안에 있어 회사를 고른 뒤에 복제된다 — 그래서 네비는
  **정적으로 띄우고 없는 섹션은 "미공시" 로 표시**한다(owner: *"없는 사들은 없다고 띄우면 되지"*).
  감추지 않는 이유는 항목이 사라지면 **그 회사에 무엇이 없는지조차 알 수 없기** 때문이다.
- [x] **네비 로직을 `theme.js` 로 공통화.** K-ICS 인라인 구현을 걷고 4페이지가 같이 쓴다.
  새 배포 에셋을 안 늘리려고 `theme.js`(이미 keep-list 에 있음)에 넣었다. `IQTheme.syncSectionNav()` 공개.
- [x] **🔴 네비가 사라지던 진짜 원인 — sticky top 하드코딩.** 71px(모바일)·88px(데스크톱)로 박아 뒀는데
  **실측 모바일 헤더가 120px** 이다(다운로드 버튼이 아래로 줄바꿈되는 폭 구간). 그 구간에서 네비가 통째로
  헤더 뒤에 숨었다 — owner 가 본 *"어떨 땐 되고 어떨 땐 안 되는"* 증상이 이것이다.
  이제 `theme.js` 가 헤더를 실측해 `--iq-hdr-h` 로 내려 주고 CSS 가 그걸 쓴다.
- [x] **스크롤 업 노출**(owner 요청). 좁은 화면에서 내려가면 접히고 올라오면 다시 나온다
  (`.is-tucked` + transform). 실측: 맨 위 안 접힘 → 내려가면 접힘 → 올라오면 나옴.
- [x] **메타발언 삭제**(owner 가 직접 지목): `IFRS17.html` "K-ICS 템플릿과 동일 스타일의 IFRS17 분석
  패널입니다." 삭제. K-ICS 자본성증권 **규정 조문 근거([별표22])도 삭제** — 1차에서 `?` 뒤에 숨겼는데
  owner 요구는 **숨기기가 아니라 삭제**였다.
- [x] **리드 문장 크기**(owner: *"쓸데없이 폰트사이즈 커"*): `.panel > p.lede` 신설(13px·muted),
  K-ICS 리드 문장을 한 줄로 줄이고 적용.
- [x] **`?` 로 옮긴 것 3건 추가**(owner: *"? 로 숨겨야 할 주석들이 여전히 많다"*):
  PL 표 주석의 OCI 구간·— 표기 설명 / 재무상태표 캡션의 "+ 눌러 펼치기" 안내 / K-ICS 민감도 기준 설명.
  좁은 화면 안내문은 **왜 그렇게 그렸는지(우리 렌더링 사정)를 걷고 사실만** 남겼다.
- [x] **index.html 보험사 검색 제거**(owner: *"이미 버블맵으로 되는 기능"*) — designer 서브에이전트, 커밋 `0647bf5`.
  마크업·CSS·JS 전부 걷고 고아 잔재 0 확인, 버블 클릭·모바일 리스트 클릭 이동은 살아 있음을 실측.

- [ ] **(별건, 이번 라운드 아님) IFRS17 모바일 가로 넘침 160px** — 375px 에서 `TABLE` 이 407px 로 넘친다.
  **라이브(이번 변경 전)에서도 동일하게 160px** 이라 이번 작업이 만든 것이 아니다. 표를 `.table-wrap`
  스크롤 안에 제대로 넣는 별도 티켓 필요.


### ✅ DESIGN-V2 P1 팔레트 — **owner 가 B안 승인, 적용 완료 2026-09-20**
owner: *"사이트 디자인이 너무 ㅈ같이 AI스럽다"* → 진단은 색이었다. `--primary:#0d6efd`(= `--bs-primary`)와
`--card:#f8f9fa`(= `--bs-light`)가 **부트스트랩 5 기본값 그대로**라 스캐폴딩 기본값으로 읽혔다.
견본 3종(현재/A 딥네이비/B 무채색+틸)을 라이트·다크로 그려 올렸고 **owner 가 B 를 골랐다**.

- [x] **토큰 값 교체** — 액센트 `#0f6e68`(딥 틸, 흰 배경 대비 6.1:1) · 패널 `#f5f5f4` · 테두리 `#e4e4e2` ·
  잉크 `#18181b` · 보조 `#63666b`(`--bg` 5.6:1 / `--card` 5.3:1, 둘 다 AA). 다크는 라이트에서 파생
  (`#54b3aa` 등) — 예전 다크 액센트(`#5b9cff` 밝은 파랑)는 라이트와 인상이 따로 놀았다.
- [x] **내 판단으로 같이 바꾼 것(owner 확인 필요)**: 액센트가 틸(hue 176°)이 되면서 기존
  `--pos:#16a34a`(hue 145°)가 **"두 개의 초록"** 으로 읽혀 양(+)을 올리브(`#4b7f2a`, hue ~95°)로 밀었다.
  음(△)도 형광 빨강(`#ef4444`) 대신 벽돌색(`#b4443a`). **견본에 없던 변경이라 되돌리려면 말만 하면 된다.**
- [x] **하드코딩 13곳 전부 제거** — 차트 라이브러리는 CSS `var()` 를 못 먹으므로 `IQTheme.chart()`
  (theme.js 가 CSS 변수를 문자열로 돌려준다)에서 읽게 바꿨다: `index.html` `SECTOR_COLOR` 2곳 ·
  `K-ICS.html` 차트 2곳(`IQP()` 헬퍼 신설)·증감색·`.dur-card.lead` 그라디언트 · `IFRS17.html`
  `DEFAULT_PRIMARY`·`NB_LINE_COLORS` · `theme.js` 폴백 12개 · `공시보고서.html` 자체 `:root`.
- [x] **검증** — 4페이지 전부 계산값으로 훑어 부트스트랩 기본값 잔재 **0건**(`rgb(13,110,253)` ·
  `rgb(248,249,250)` · `rgb(233,236,239)` · `rgb(33,37,41)`), 라이트·다크 둘 다 확인,
  `pytest tests/test_deploy_assets.py` 11 passed.
- [ ] **남은 P1 항목**: `og:image` 는 여전히 4페이지 **0건**. 팔레트와 무관한 별건.


### ✅ KICS-SECTIONNAV — K-ICS.html 섹션 네비 (owner 2026-09-19, **구현 완료 2026-09-20**)
owner: *"드래그 내리기 전에는 어떤 항목이 있는지 알기 어려운데, 좌측에 탭 기능 만들어서 뭐뭐 있는지 미리 좀
알 수 있게. 모바일은 탭 들어갈 공간이 없을 거 같기도."*

- [x] **id 3개 부여** — `#sec-trend`(컨트롤+피벗표 패널) · `#sec-sens`(금리 민감도) · `#sec-forward`(전망).
  `#donut-section-panel` 은 **이름을 안 바꿨다**(다른 곳에서 딥링크할 수 있어 기존 id 를 그대로 앵커로 쓴다).
- [x] **`.section-nav` 컴포넌트를 `common.css` 에** 신설. **`.tab/.tabs` 와 이름을 일부러 분리** — 그쪽은
  페이지 간 이동(K-ICS/IFRS17/기타공시)에 이미 쓰고 있어서, 같은 화면에 생김새가 같은 두 종류가 있으면
  어디로 가는 링크인지 구별이 안 된다.
- [x] **데스크톱(≥1080px)**: `.container.has-section-nav` 를 `186px + 1fr` 그리드로. 네비는 `sticky; top:88px`
  (헤더 76px + 여유). 실측 1280px 에서 `grid-template-columns: 186px 1023px`, 가로 넘침 0.
- [x] **모바일(<1080px)**: 좌측에 넣을 폭이 없어 **헤더 밑에 붙는 가로 칩 줄**(`sticky; top:71px`,
  `z-index:900` — header 1000 아래여야 덮지 않는다). 항목을 **4개로 고정**했다 — 2026-09-15 에 owner 가
  "칩 남발" 로 두 번 반려한 이력을 지켰다. 실측 가로 넘침 0.
- [x] **스크롤 스파이** — 앵커선(96px) 위로 올라간 섹션 중 **마지막** 것을 현재로 표시, `aria-current="true"`
  는 항상 1개. 4개 섹션 전부 제 항목으로 매핑되는 것과 문서 끝 폴백을 실측으로 확인.
- **실패했다가 고친 것 2가지 — 같은 함정을 다시 밟지 말 것:**
  1. **IntersectionObserver 로 "교차 중인 첫 섹션" 을 고르면 안 된다.** 도넛 패널이 키가 커서 그 아래
     섹션으로 내려가도 계속 교차 상태라 활성 표시가 안 넘어간다(1280px 실측: 민감도·전망으로 가도
     '자본성증권 소진율' 이 그대로 남았다). 기하 판정으로 바꿨다.
  2. **`requestAnimationFrame` 으로 스크롤을 스로틀하지 마라.** 백그라운드 탭에서 rAF 가 멈추면 스파이가
     조용히 죽는다(프리뷰 창에서 실제로 밟았다). 대상이 4개뿐이라 매 스크롤에 rect 를 재도 비용이 없고,
     활성이 바뀔 때만 DOM 을 건드려 레이아웃 무효화를 막는다.
- **검증 한계**: 이 PC 의 프리뷰 창은 **`window` scroll 이벤트를 아예 안 뿜는다**(`scrollY` 는 바뀌는데
  리스너가 0회 호출). 그래서 스파이는 합성 `scroll` 이벤트로 실제 핸들러를 깨워 검증했다 — 기하·배선은
  확인됐지만 "브라우저가 스크롤 이벤트를 준다" 는 전제는 이 창에서 확인 못 한다.

### ✅ COPY-TOOLTIP — 화면 설명문 정리 + "?" 툴팁 (owner 2026-09-19, **구현 완료 2026-09-20**)
owner: *"쓸데없는 설명주석들 좀 다 정리 — `?` 표시 만들어서 커서 올리면 설명 나오게. 특히 니가 사이트
구축하면서 노트해둔 메타발언들은 싹 다 지워."*

- [x] **`.iq-help` 컴포넌트를 `common.css` 에** 신설, 4페이지 공용.
  **JS 를 안 쓴다** — 배포 에셋 keep-list 를 안 늘리려고 CSS 만으로 세 경로를 연다:
  포인터 `:hover` · 키보드 `:focus-within`(button 이라 Tab 으로 도달) · 터치는 탭하면 button 에 포커스가
  잡혀 열리고 바깥을 탭하면 닫힌다.
  **숨김에 `visibility` 를 쓰지 않았다** — 접근성 트리에서 사라져 `aria-describedby` 가 헛돈다.
  `opacity` + `pointer-events` 로만 가린다.
- [x] 이관 완료 6곳(전부 실측 확인, `aria-describedby` ↔ 팝오버 `id` 일치 6/6):
  | 위치 | 본문에 남긴 것 | `?` 뒤로 보낸 것 |
  |---|---|---|
  | K-ICS 자본성증권 | 소진율 산식 2줄 | 한도가 계정 단위라는 규정 근거([별표22]) |
  | K-ICS Forward Outlook | "보수적인 가정 두 가지" 한 줄 | 가정 2개 전문 |
  | K-ICS 듀레이션 노트 | 부호 해석 결론 | D·C 산식 유도 전체 (**가장 길었다**) |
  | IFRS17 PL 캡션 | 제목·기간·단위 | 계정 흐름 + y축 톱니 처리 설명 |
  | IFRS17 민감도 캡션 | 기준 분기 | 왜 과거 분기인지(연 1회 공시) |
  | 공시보고서 커버리지 | "24개사" | 상장사만 대상이라 결측이 아니라는 설명 |
- [x] 원문 잔존 0 확인 — 걷어낸 문장 3종을 `document.body.textContent` 로 재검색해 전부 0건.
- **범위에서 뺀 것**: `//` JS 주석으로만 있는 개발 노트는 **화면에 안 나간다**. owner 지시가 "사이트에
  있는" 설명문이라 화면에 렌더되는 것만 건드렸다. 지워야 한다면 별도 티켓으로 — 코드 맥락이 같이 사라진다.


### MOB-KICS — K-ICS.html full mobile layout (scope confirmed by owner 2026-06-12)
Owner confirmed scope: **full-panel mobile pass + alternative render** (not foundation-only). M1 foundation already in place (header/tabs/table scroll, chart heights ↓).
- [x] Donuts stacked vertically — `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap`으로 375px에서 자동 1열 스택. 이미 구현됨 (2026-06-17 확인).
- [x] Forward-chart legend reposition — `position: window.innerWidth < 640 ? "bottom" : "top"` (2026-06-17)
- [x] Dense table → card view (가/나/다 sub-items) — `renderMobileCards` ≤640px (2026-06-20)
- [ ] **(owner open rec 1)** horizontal-scroll range for dense panels — decide which panels scroll vs reflow
- [ ] **(owner open rec 2)** breakpoint set — confirm thresholds beyond the single 640px (e.g. <400px sub-query)

### MOB-IFRS17 — IFRS17.html full mobile layout (scope confirmed by owner 2026-06-12)
Owner confirmed scope: **full-panel mobile pass + alternative render**. M1 foundation only so far.
- [ ] Panel 1–6 mobile policy: which to keep, which to collapse, which to swap for alternate viz
- [x] **Panel 7 (BS-DRILLDOWN) 모바일 실측 — 문서가 낡아 있었다(2026-09-19 정정).** 같은 사실이 두 티켓에
  다른 상태로 남아 있었다: 위 **BS-TACCOUNT 티켓 L208** 에 2026-08-18 real-viewport recheck 기록이
  이미 있다(`window.innerWidth===375` 실측, `.bs-t` 가 `flex-direction:column` 으로 전환, 세부·하위 행이
  1열로 접힘, `body.scrollWidth` 가 `innerWidth` 를 안 넘음 = 가로 넘침 0, 콘솔 오류 0). 이 티켓에만
  반영이 안 됐던 것이다. 코드 변경 없음, 체크박스만 정정.
- [ ] **(owner open rec 1)** horizontal-scroll range for dense panels
- [ ] **(owner open rec 2)** breakpoint set confirmation
- (shares the two owner open recs with MOB-KICS — resolve once for both pages.)

### VIS-DONUT — K-ICS donut row stacks on phones ✅ 완료
- [x] `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap` → 375px 화면에서 자동 1열 스택. 명시적 flex-direction:column 불필요. 이미 구현됨 (2026-06-17 확인).
- [x] Labels legible: 각 도넛이 전체 너비 차지, 레이블 공간 충분.

### VIS-CHARTLEGEND — chart legend/axis density on mobile
- [x] K-ICS forward + IFRS17 hist/NB legend → bottom on mobile (`window.innerWidth < 640`) (2026-06-17)
- [ ] IFRS17 amort + index bubble legend (amort display:false OK, bubble ECharts top=8 review later)

### M3 — chart fine-tuning (roll-up of VIS-DONUT + VIS-CHARTLEGEND + misc)
- [x] K-ICS 도넛 2개 세로배치 (= VIS-DONUT) — 이미 구현됨
- [x] Forward 라인 범례 위치 (= VIS-CHARTLEGEND) — done 2026-06-17
- [ ] 차트 미세조정 across pages

### Panel 7 — 원천지표 카드 ✅ 완료 (2026-06-17)
IFRS17.html 대시보드 최상단에 4-card KPI strip 추가(기말 CSM 잔액·CSM 상각·신계약 CSM·NB CSM 배수). `wfVal(company,latestQ,6/5/2)` + `ix.nbm` 기반. 2열 모바일 그리드.

### INDEX-BUBBLE-V2 HTML side — 4축 bubble rendering
Publishing ships the data (`TODO_publishing.md` INDEX-BUBBLE-V2). Designer ships the ECharts spec:
- [x] **🚫 폐기 — 재착수 금지 (2026-08-20 확인)**. 4축 V2는 owner가 폐기했고 **3축이 이미 라이브 완결**이다: `index.html` L165 *"X: 신계약 CSM 규모 · Y: NB CSM 배수 · 크기: 기말 CSM 잔액"*. 이 줄을 열린 항목으로 두면 다음 세션이 완결된 기능을 다시 만든다. 원문:
- [x] **Mobile rendering — 문서가 낡아 있었다(2026-09-19 정정, 이 트리에서 직접 확인).** 이미 구현돼 있다:
  `index.html` L83 `#bubble-list{display:none}`(데스크톱) + 모바일 폭에서 노출, L107-108 에 행 레이아웃
  CSS, L1363 에 행 클릭 핸들러. 버블맵 대신 리스트로 떨어지는 대체 렌더가 라이브다. 코드 변경 없음.
- [x] **Click → cross-nav — 문서가 낡아 있었다(2026-09-19 정정, 이 트리에서 직접 확인).** `index.html`
  L1125-1127 `bubbleChart.on('click', ...)` → `window.location.href='IFRS17.html?company='+encodeURIComponent(...)`.
  모바일 리스트 행도 같은 이동(L1363), 상단 typeahead 도 같은 패턴(L446). 코드 변경 없음.

### F17 Panel 3 — Tier2 LOB drill-down rendering (when publishing ships Tier2 JSON)
Publishing currently has Tier1 4-bar in production. Tier2 (LOB 장기/자동차/일반 stacked) waits on parser F17 decision + publishing assembly.
- [ ] Stacked bar / waterfall design (손보만, LOB visible)
- [ ] 생보 alt-rendering (장기 전사 fallback)
- [ ] Caption variant per-company taxonomy (장기/자동차/일반 vs 보장성/물보험/저축성)

## ✅ Done (archive)
완결 항목 25+개(2026-05-28~06-14) — M1 모바일 foundation, KEYCOLOR/TREEMAP-SCALE, △(세모) 전면화, 생명장기·시장위험액 토글, PL/CSM 워터폴 패널, HTML single-source refactor, dead-CDN 제거 등. 상세는 `docs/changelog_designer.md`(당시 `(changelog MM-DD)`로 인덱싱) + git log.


## 🗂️ Conventions reference

**Responsive breakpoints**
- M1 foundation: `@media (max-width:640px)` on all 4 pages. Header/tabs/chart heights/table scroll.
- M2: index.html ≤640px swaps treemap → vertical list (`renderList()` mirrors `render()`).
- M3: donut stack + legend reposition + chart fine-tuning.

**Chart libraries (committed)**
- Chart.js: IFRS17 Panels 2–6
- ECharts: Panel 1 (CSM waterfall), index treemap, bubble

**Page roster (root single-source since 2026-05-28)**
- `index.html` — market map + IFRS17 quadrant + bubble
- `K-ICS.html` — per-insurer detail + sub-items + forward outlook
- `IFRS17.html` — 7-panel dashboard (1=BS T-account, 2-7=CSM/PL/NB/sensitivity)
- `공시보고서.html` — 배당현황 (per-company dividend disclosure, filled in 2026-08-15; was a static "coming soon" shell before)

**Local preview:** `python -m http.server 8000` from repo root. (preview_eval 반복 행 시 Edge headless `--dump-dom` 대체; 좀비 포트 회피로 현재 8889.)

## Reading order for designer subagent
1. This file (`TODO_designer.md`) — current state (changelog is deferred: [`docs/changelog_designer.md`](docs/changelog_designer.md) is history, open only when you need a past decision's background)
2. [`docs/agents/claude-agent-designer.md`](docs/agents/claude-agent-designer.md)
3. Root HTML page(s) in scope
4. Master JSON schema (publishing's output) for the panel you touch — read-only
5. Root [`TODO.md`](TODO.md) for cross-stage roadmap notes

## Hand-off
- **From publishing**: notification that a master JSON changed (`manual_html_edit` warn) or that a new field needs rendering.
- **To human**: designer never pushes. Hand off to publishing for the commit message + push recommendation.
