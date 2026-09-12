# TODO archive — jp 레인 (일본 ESR)

> `TODO_jp.md` Status 최신 5개 유지 원칙에 따라 밀려난 항목을 한 글자도 고치지 않고 여기로 옮긴다.
> 최신이 위. 필요할 때만 연다(changelog 와 같은 원칙).

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
