# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-12 · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 `docs/todo_archive_jp.md` 로(무수정).

## Status

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
