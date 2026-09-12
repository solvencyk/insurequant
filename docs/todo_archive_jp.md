# TODO archive — jp 레인 (일본 ESR)

> `TODO_jp.md` Status 최신 5개 유지 원칙에 따라 밀려난 항목을 한 글자도 고치지 않고 여기로 옮긴다.
> 최신이 위. 필요할 때만 연다(changelog 와 같은 원칙).

**🟢 2026-09-12 (5) `jp/index.html` ESR 랭킹 ECharts 가로막대 폐기 → 루트 `index.html` 모바일 리스트 그대로 이식(designer).**
티켓 `inbox/designer/20260912T0810Z__owner__JP_MULTI__jesr_jp_page_v3_korean_list.md`(answered). owner 지적: "한국 사이트
모바일 리스트 레이아웃을 그대로 쓰면 되는데 새로 ECharts 막대를 만들었다" → `#esrChartLife/Nonlife`(echarts bar) 전부
삭제, 루트 `index.html` 82~98행 `.map-list`~`.li-chip` CSS + 877~948행 `renderList()` + 531~547행
`_ratioHsl`/`colorForRatio` 를 그대로 복사해 `esrListLife`/`esrListNonlife` 로 이식. 색 상수만
`RATIO_SCALE={esr:{base:100,strong:300}}`(base=일본 금융청 감독기준 100%, strong=13사 분포 p90 표시 끝점). 데스크톱·모바일
모두 리스트(jp 는 트리맵이 없어 `.map-list{display:block}` 로 상시 표시), top5+더보기(FOLD=5, `isMob` 조건 없이 데스크톱도
적용 — 기존 jp 동작 유지) · 生保/損保 2섹션 · 速報 는 `.li-chip` 로 이름 옆에 이동. 행 클릭/role="link"/keydown 은 뺐다(jp
에 상세 페이지 없음, 티켓 지시) — `title`/`aria-label` 요약 텍스트만 유지. ▲目標水準 마커 제거, 表 備考열에
`目標 190%+` 텍스트로 이관(`target_pct`). 업태색 범례(生保/損保 스와치) 제거 → 감독기준 색 설명으로 교체. 편차 1건:
`.li-row` 의 `cursor:pointer`/`:active` 는 복사하지 않음(클릭 없는데 포인터 커서면 오탐 어포던스 — a11y 관점 직접판단,
값 변경 아닌 어포던스 수정). 정리(orphan 제거): `chartInst`/`GROUP_COLOR`/`isMobile()`/`parseTargetNum()`/`debounce()`
+ resize 리스너(리스트는 뷰포트 무관 렌더라 불필요). 검증: `python -m http.server 8896`(기존 실행 중) +
Claude Browser preview 로 데스크톱 1280px·모바일 375px 렌더 확인(콘솔 에러 0, jsdelivr `ERR_NETWORK_ACCESS_DENIED`
는 이 PC 크로미움 공통 현상— echarts CDN 못 받는 도넛만 영향, 순수 CSS 인 리스트는 무관하게 정상 렌더됨 확인),
더보기 클릭 → 9사 전체 펼침 + 표 동시 펼침 확인. `scripts/a11y_contrast_check.py contrast "#212529" "#ffffff"` →
15.43:1(AA 통과, `.li-name`/`.li-val` 글자색). Playwright(`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`,
headless는 CDN 차단 없어 도넛도 렌더됨)로 최종 스크린샷 `artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`
덮어씀(재현: 로컬 스크립트로 1280×1400 / 375×900 viewport full-page capture).

**🟢 2026-09-12 (4) `jp/index.html` 2차 개선 — owner 지적 5건 반영(designer) + orchestrator 재검증·버그 1건 직접수정.**
티켓 `inbox/_resolved/20260912T0530Z__owner__JP_MULTI__jesr_jp_page_v2.md`(resolved). ① category 2단 버킷 정렬
(`HD上場`/`相互会社`/`上場` 선두 vs 그 외, 각 버킷 내 `esr_pct` desc — au損害保険 791.7%가 손보 최하단으로 이동)
② sector 별 top5+더보기(生保 9사→top5+4, 損保 4사=버튼 없음, reinsurance는 損保에 합류) ③ 表의 出所 열 제거 →
公表日 텍스트에 `source_url` 링크 ④ 막대차트 빗금(연결) 인코딩·범례 항목 제거, `scope` 는 表·툴팁 텍스트로만
⑤ 速報 배지 그대로. designer 세션은 Playwright 캡처가 cdn.jsdelivr.net `ERR_NETWORK_ACCESS_DENIED`(이 PC 크로미움
공통 현상)로 차트가 빈 화면으로 찍혀 "다음 세션 재확인 권장"으로 넘겼는데, **orchestrator 가 즉시 재검증**함:
echarts 로컬 임시 사본(검증 후 삭제, `jp/index.html`은 CDN 참조만 유지)으로 실제 렌더 확인 — 2단 정렬·top5 폴드·
au 최하단 이동·빗금 제거 전부 스크린샷으로 확인됨. 그 과정에서 **버그 1건 추가 발견·직접수정**: 모바일(375px)
생명보험 차트 x축 눈금이 "50%00%050%060%090%00%" 로 겹쳐 읽을 수 없었음 → `xAxis.axisLabel.hideOverlap:true` +
모바일 `splitNumber:4`(데스크톱 6)로 수정, "0% 100% 200% 300% 400%" 정상 표시 확인. 최종 스크린샷
`artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`(덮어씀).

**🟢 2026-09-12 (3) `jp/jesr_esr.json` 부모-자회사 중복 제거 — 15→13 레코드(publishing).**
티켓 `inbox/publishing/20260912T0530Z__owner__JP_MULTI__jesr_dedup_parent_subsidiary.md`. 소니생명保険(parent 소니FG)·明治安田損害保険
(parent 明治安田生命保険) 제외, au損害保険(parent KDDI, 미공시)은 유지. `J-ESR/build_jesr_page_json.py` 에 회사명 비하드코딩 일반 로직
(`jp_insurers.csv` `parent_group` 조인) 추가. `J-ESR/jesr_master.json` 은 15사 그대로. 재현:
`PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py`.

**🟢 2026-09-12 (2) `/jp/` 일본어 페이지 초안 — 데이터 `jp/jesr_esr.json`(15사, publishing) + `jp/index.html`(designer).**
티켓 `inbox/_resolved/20260912T0446Z__owner__JP_MULTI__jesr_page_json.md` · `..._jesr_jp_page_draft.md`. owner 결정: IP 차등·`.co.jp` 대신
같은 사이트 `/jp/` 경로(나중에 `jp.insurequant.com` 승격 가능). 라이브 반영은 owner 가 초안을 본 뒤.

**🟢 2026-09-12 (1) FY2025 ESR 공시 게재 census 79사 — posted 15 / not_yet 62 / not_found 2, ir_url 공란 41→2.**
`J-ESR/fy2025_esr_census_20260912.csv`. 손보 원문 11/13건이 "신기준 비율 2026년 10월 말 공표 예정" 명시. 소스 루트 정정(EDINET 보조, 회사별
공시 사이트 정본)은 이날 owner 발언 재기록. 티켓 `inbox/_resolved/20260912T0307Z__owner__JP_MULTI__jesr_fy2025_disclosure_census.md`.
