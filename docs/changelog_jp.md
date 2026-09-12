# Changelog — jp 레인 (일본 ESR)

> 이력 저장소. 세션 시작 시 읽지 않는다. 현황은 `TODO_jp.md`.

## 2026-09-12 -- jp 레인 신설 + FY2025 ESR census 79사 + `/jp/` 초안

- owner 결정 3건: (1) J-ESR 소스 정본은 EDINET 이 아니라 회사별 공시 사이트 PDF(기한 2026-10-31) — 이전 세션 구두 결론이 repo 에 없어
  오케스트레이터가 EDINET 조회를 다시 제안하는 사고 후 재기록. (2) 일본 화면은 IP 차등·`.co.jp` 대신 같은 사이트 `/jp/`. (3) jp 는
  한국 stage 에이전트와 **별개 에이전트**로 부린다(한국 프롬프트 11만 자에 일본 언급 0건 — 비대화 + 규칙 오염).
- census: downloader 에이전트 2개(행 1~41 / 42~81) → `J-ESR/fy2025_esr_census_20260912.csv` 79사, posted 15 / not_yet 62 / not_found 2.
  posted 이상치 2건(au 791.7%·Meiji Yasuda Non-Life 743.2%) 원문 PDF fitz 재확인. `jp_insurers.csv` ir_url 41→2. 커밋 `ca54fca`.
- 초안: publishing 이 `J-ESR/build_jesr_page_json.py` → `J-ESR/jesr_master.json` + `jp/jesr_esr.json`(15사, preliminary 5), designer 가
  `jp/index.html`(일본어 UI, 요약 카드·ESR 랭킹 막대·커버리지 도넛·출처 표·hreflang). 기존 4페이지 무수정.
- 레인 뼈대: `docs/domains/claude-agent-jp.md`, `TODO_jp.md`, 이 파일, `inbox/jp/`, `.claude/agents/jp-collector.md`(로컬).
  `CLAUDE.md` 는 같은 날 룰만 남기고 202→94줄로 축약(전문은 `docs/claude-md-history.md`).

## 2026-09-01 -- 9월 말 킥오프 확정 (owner)

인스뉴스 기사(일본 금융청 2026 보험 모니터링 보고서) 계기. 상세 루트 `TODO.md` J-ESR 항목.

## 2026-07-21 -- MVP 페이지 revert (`167cba1`)

그룹 연결값 11사뿐이라 화면 보류(owner). 근거 메모리 `project_jesr_scope_timing`.

## 2026-06-24 -- 트랙 신설 (당시 downloader/parser 가 처리)

`docs/changelog_downloader.md` 2026-06-24 항목 2건 · `inbox/_resolved/2026062*__*jesr*` 8건.
