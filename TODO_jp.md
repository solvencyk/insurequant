# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-12 · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 `docs/todo_archive_jp.md` 로(무수정).

## Status

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

## Active follow-ups

- **10월 말 재census** (2026-10-31 기한 직후): 같은 티켓 구조·같은 csv 열로 79사 재조회. notes 에 "패턴 기반 잠정" 이라 적힌 행(Zurich Life·AXA Life 등)부터 연다. 확정치가 나오면 `preliminary` 5사(LifeNet·Asahi·Fukoku·Japan Post·Sumitomo) 갈아끼움.
  **같은 라운드에 3축도 같이 뽑는다(owner 2026-09-12 확정, 아래 스코프 확장 항목과 병합·더는 미결 아님):** 회사별 공시 PDF 를 어차피 다시 여니
  ESR 옆에 열 3개 추가 — `air_used`(자산집약형 재보험 활용 여부·목적에 "ESR 개선" 명시 있는지) · `catastrophe_reserve_adequacy`(이상위험준비금/화재보험
  충족 여부, 생보는 해당없음) · `interest_margin_sign`(이차손익 부호·역마진→이익 전환 서술 유무). 손보 원문에 이상위험준비금 열람이 이미 필요하므로
  추가 비용 작지만, **생보 AIR·이차손익 서술은 다른 섹션**(결산설명자료 리스크관리·계리 파트)이라 놓치기 쉽다 — census 티켓에 이 3열을 명시할 것,
  "ESR 만 보고 넘어가는" 기본 습관으로 되돌아가지 말 것.
- `/jp/` 라이브 반영(owner 승인 후): publishing 티켓 답변의 "라이브 반영 시 필요한 것" 3건 — 배포 keep-list 가 4페이지 하드코딩(3곳)이라 새 페이지가 게이트에서 안 보임 → 목록화 필요; xlsx 시트 불필요; status_report 4절은 현재 무검사. 루트 `index.html` 에 hreflang 2줄 + 언어 전환 링크(designer 답변 조각).
- `jp_insurers.csv` 완전 중복 2행 정리(행 순서 보존 원칙 때문에 이번엔 보존). not_found 2사(Meiji Yasuda Trust Life·Yamap) 공시 페이지 재탐색.
- **3축 화면 반영은 별도 판단.** census 에 열만 먼저 채우고, `/jp/` 화면에 얹을지(카드 추가·범례 등)는 10월 말 데이터가 실제로 얼마나 뽑히는지
  본 뒤 owner 에게 다시 묻는다(루트 `TODO.md` J-ESR 항목의 기사 원 취지 — insnews #92437, 일본 금융청 2026 보험 모니터링 보고서 참고).
