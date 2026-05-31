# Insurequant TODO

Last updated: 2026-05-31 (5-stage workflow split fully populated: publishing + designer split out today).

Pipeline organized as **downloader / parser / validation / publishing / designer** — each stage has its own prompt (`docs/agents/claude-agent-<stage>.md`), TODO (`TODO_<stage>.md`), and changelog (`docs/changelog_<stage>.md`). See `CLAUDE.md` for the full index. This root file carries cross-stage items + project-wide policy only.

**Stage files:**

- **Downloader** (Stage 1): `TODO_downloader.md` + `docs/changelog_downloader.md` + `docs/agents/claude-agent-downloader.md`
- **Parser** (Stage 2): `TODO_parser.md` + `docs/changelog_parser.md` + `docs/agents/claude-agent-parser.md`
- **Validation** (Stage 3): `TODO_validation.md` + `docs/changelog_validation.md` + `docs/agents/claude-agent-validation.md`
- **Publishing** (Stage 4, **merged gathering + pushing**): `TODO_publishing.md` + `docs/changelog_publishing.md` + `docs/agents/claude-agent-publishing.md` (skeleton — created 2026-05-31)
- **Designer** (Stage 5, **new — HTML/CSS/responsive**): `TODO_designer.md` + `docs/changelog_designer.md` + `docs/agents/claude-agent-designer.md` (skeleton — created 2026-05-31)

Items previously here that have moved out:

- Downloader (F2 done, F7–F10, F14, MISC-BOND-*, MISC-IR-MERITZ, MISC-SEIBRO, decisions #5/#6) → `TODO_downloader.md`
- Parser (KICS-PARSER-SPLIT/REPARSE-Q4/KR0069/KR0097/RED-FIX2/RED-FIX3/SUB/POST/RATIO28/HIST/IMG + IFRS-A1~B5-KICS/B3-UNIFY/NORMALIZE/HIST/SEN-TABLE) → `TODO_parser.md`
- Validation (KICS-VALIDATE, IFRS17-NB-RECONCILE) → `TODO_validation.md`
- Publishing (F4 v2, F13, INDEX-IFRS17-BUBBLE, INDEX-BUBBLE-V2, MISC-IR-PROTOTYPE, MISC-IR-NB-DENOM, IFRS17-CSM-BUBBLE, KICS-TIER1/2-UTIL, KICS-FORWARD-CAPITAL, KICS-HTML-SUB, IFRS17-HTML-DASH, F5/F6 data) → `TODO_publishing.md`
- Designer (MOB-KICS, MOB-IFRS17, VIS-DONUT, VIS-CHARTLEGEND, INDEX-C12, F1-HTML, F6-HTML, F17-PANEL3 HTML, M1/M2) → `TODO_designer.md`

**Reorg #2 (2026-05-30j)** — `data/assoc/` → `data/_derived/`; KIDI/DART → `FY####_Q#` 컨벤션 통일. **DART batch script refactor 잔여** → `TODO_downloader.md` REORG2-DART.

Session start: read this root file first, then the relevant stage's `TODO_<stage>.md`.

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## 🔀 Cross-stage follow-ups (multi-stage; detail in stage files)

| # | Task | Stages involved | Detail location |
|---|------|-----------------|-----------------|
| F12 | K-ICS 시장위험 하위위험액 전체 파싱 + 분산효과 validation | parser + validation | `TODO_parser.md` F12 + `TODO_validation.md` V3 |
| F17 | 당기순이익 분해 (Tier1 전사 + Tier2 손보 LOB) | parser + publishing (+ designer for Tier2 panel) | `TODO_parser.md` F17 (body) + `TODO_publishing.md` F17 viz + `TODO_designer.md` F17 Tier2 |
| F18 | IR factsheet 정형화 + DART↔IR cross-validation | parser + validation + publishing | `TODO_parser.md` F18 + `TODO_validation.md` V1 + `TODO_publishing.md` F18 viz |
| F13 | 재보험 영업 지표 세트 | downloader (F8) + parser + publishing | `TODO_downloader.md` F8 + `TODO_publishing.md` F13 |

## 📋 Policy / User decisions (cross-stage)

| # | Decision | Date |
|---|----------|------|
| 1 | K-ICS skip cohort: KR0029 AIG, KR0150 SGI permanent skip. KR0051 / KR0074 partial-coverage by design | 2026-05-24 |
| 2 | Meritz IR source: Meritz Financial Group factsheet xlsx (replaces Meritz Hwajae standalone). AIG IR: skip low-priority | 2026-05-24 |
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료**. IR PDF for 6 cos; assoc crawl (KIDI/KLIA/KNIA) for 23-co computed multiple | 2026-05-24 |
| 4 | First HTML viz: CSM Movement Waterfall (IFRS17 A1 23-co) | 2026-05-24 |
| 5 | API keys: repo root `.env` only (gitignored). Never commit/log key values | 2026-05-24 → `TODO_downloader.md` D5 |
| 6 | Bond Call rule: issue + 5y for ALL bonds. Past 5y = assume `called` | 2026-05-24 → `TODO_downloader.md` D6 |
| 7 | Pushing: subagent **reports + recommends only**. Human runs `git push` | 2026-05-30 |
| 8 | DART attachments (별첨/감사보고서 zip): **don't fetch**. Body XML has all IFRS17 disclosures | 2026-05-30 → `TODO_downloader.md` DL-NOATTACH |

## 🌐 Universe (cross-stage)

- **K-ICS**: 38 insurers (`kics_disclosure.json` `원수사명`); skip cohort KR0029/KR0150
- **IFRS17**: 28 insurers (`src/ifrs17/universe.py`) — 23 listed + 5 foreign-affiliate life via audit reports (F11, `AUDIT_REPORT_ANNUAL`, annual-only). Historical 13Q cohort = 23 listed.
- **K-ICS↔IFRS17 mismatch**: AIA (에이아이에이생명보험) is in IFRS17 universe but NOT in `kics_disclosure.json`. Cohort joins must handle this.

## ✅ Done — cross-stage anchors

| ID | Task | Notes |
|----|------|-------|
| ~~F1~~ | index.html → IFRS17 cross-nav | `fcdd544`. ECharts on('click') → URL param + auto-select. Data hook = publishing; HTML = designer |
| ~~F3~~ | CSM 상각 schedule 전수 조사 | `4b06492`. 19/24 → 22/24 ok |
| ~~F5~~ | No-bond insurer forward sim 추가 | `b02e24d`. 24 → 37 cohort |
| ~~F6~~ | CSM 상각 schedule yearly granularity | 2026-05-28. 16 yearly / 6 coarse / 2 no-data |
| ~~F11~~ | 외국계 생보 5사 IFRS17 추가 | DONE 2026-05-29. 23→28 (생보 13→18). corp_codes: 라이나 00504232 / 메트라이프 00171104 / AIA 01295517 / 하나생명 00187123 / 처브 00203102. universe.py `AUDIT_REPORT_ANNUAL`. NOTE: AIA not in kics_disclosure.json |
| ~~IFRS-Q~~ | Open Q1-Q9 | done. All 9 confirmed |

## 📚 Long-term / roadmap

> 📈 **중장기 제품·수익화·전략 로드맵 → `docs/roadmap.md`** (2026-05-26 신설)

Active long-term tracks now live in their respective stage TODOs:

- **IFRS17 bubble + market map evolution** → `TODO_publishing.md` (data) + `TODO_designer.md` (HTML)
- **Forward solvency simulation** → `TODO_publishing.md` (KICS-FORWARD-CAPITAL done v3 archive)
- **Roadmap §1A-2 priority 6 추가지표** (요구자본 위험액 분해 / RA / P&L 보험·투자 분해 / 출재율 / 유지율 / 운용자산이익률) → distributed across parser + publishing
- **Roadmap §1E 규제 뉴스 피드** → `TODO_downloader.md` F14

## 🧾 Meta

- Encoding rule: `CLAUDE.md` "Document/TODO Encoding Rule" added 2026-05-24
- .gitignore: `data/dart/raw/`, `data/dart/reports/` excluded
- 2026-05-25 doc trim: changelog 124KB→11KB (latest 5 entries detailed + historical archive 1-liners)
- git: initialized + pushed to github.com/solvencyk/insurequant (main). GitHub Pages → solvencyk.github.io/insurequant
- 2026-05-26: `docs/roadmap.md` 신설
- 2026-05-28 HTML single-source refactor (P1+P4): templates/*.html 4개 삭제. ⚠️ 데이터 JSON 중복 남음 (P2)
- 2026-05-28 모바일 반응형 M1/M2 적용
- 2026-05-28 IFRS17 패널 정리: 파생 KPI 카드 + BS 스냅샷 제거 → `docs/archived_metrics.md`
- 2026-05-30j Reorg #2: `data/assoc` → `data/_derived`, KIDI/DART → `FY####_Q#`. DART batch script refactor 잔여 → `TODO_downloader.md`
- 2026-05-30k 5-stage workflow split (downloader/parser/validation/gathering/pushing 초안)
- 2026-05-31 Stage 2/3/4/5 split fully populated: parser/validation TODO+changelog (오전), publishing(=gathering+pushing 머지)+designer(MOB/VIS HTML 별도 stage) TODO+changelog (오후). Root TODO is now genuinely cross-stage only

## ✓ MVP checklist (IFRS17)

- [x] A1 A2 A3 A4 B1 B5 all 23/23 MVP (B5 K-ICS primary ingest done FY2025_Q4)

## 🎯 Next priorities (cross-stage)

1. **KICS-IMG manual OCR** (user-owned): KR0010 KB Sonhae rule 2 ×2 — only remaining RED. Parser policy → `TODO_parser.md`; validation gate exception → `TODO_validation.md` V6
2. **F17 decision**: 9/11 손보 Tier2 LOB commit vs debug 삼성·DB vs IR-clean only. Parser detail → `TODO_parser.md`. Tier2 panel rendering → `TODO_designer.md` after decision
3. **F18 activation**: parser delivers IR JSON → V1 validation rules activate → publishing assembles cross-source viz
4. **REORG2-DART**: 3 batch scripts canonical-layout refactor → `TODO_downloader.md`
5. **Stage prompts 마무리**: parser / publishing / designer prompts still skeleton (TBD bodies); validation + downloader prompts are owner-authored complete
