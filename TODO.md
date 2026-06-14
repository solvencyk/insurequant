# Insurequant TODO

> Last updated: 2026-06-12 · Stage: cross-stage
> Index: CLAUDE.md (5-stage) · Stage TODOs: TODO_<stage>.md

Pipeline organized as **downloader / parser / validation / publishing / designer** — each stage has its own prompt (`docs/agents/claude-agent-<stage>.md`), TODO (`TODO_<stage>.md`), and changelog (`docs/changelog_<stage>.md`). See `CLAUDE.md` for the full index. This root file carries cross-stage items + project-wide policy only.

## Status

Cross-stage focus (2026-06-12): K-ICS gate RED=227 all documented exceptions (19_market 223 + KR0049 4) pending validation registration; cross-stage CSM-waterfall 신한EZ 제외 + K-ICS 금리민감도 feature have only publishing/designer tails left; owner backlog digest dispatched to all 5 stage inboxes. Mid-long-term: duration-gap (MLG-1) and K-ICS 시장위험 분해 (MLG-2) blocked on owner decisions.

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

## 🔴 K-ICS gate documented exceptions (2026-06-12, parser)

Gate run 2026-06-12: RED=227 = **19_market 223 + KR0049 2026.1Q 4** (rules 2/4/5/6). All documented:

- **rule 19_market × 223 (28 companies)** — item19(시장위험액) disclosed but 36-40 breakdown absent
  **in the source PDFs themselves** (structural non-disclosure). Parser exhausted recovery:
  `fill_market_subs_from_pdf.py` (fitz + M-matrix reconcile<2%) full re-run = no-pdf 0, new rows 0.
  Full (company,quarter) list: `artifacts/kics_validation/market_breakdown_red_census_20260612.md`.
  → **validation**: register in `MARKET_BREAKDOWN_EXEMPT` (kics_json_rules.py) after cross-check —
  inbox `20260612T1100Z__parser__MULTI_ALL__2026q1_loaded_and_19market_exempt_request.md`.
  3 reconcile-fail cells kept OUT of exempt (table exists, gate rejected): KR0002 2024.2Q,
  KR0009 2023.3Q, KR0051 2023.1Q.
- **KR0049 악사손해 2026.1Q rules 2/4/5/6 (4)** — K-ICS detail page (p16) is a full-page image in
  the PDF; only core 5 items recoverable from text (총괄 + 공통적용 tables). Needs owner gold or OCR.
- **Scan-only PDFs (coverage census MISSING, not rule REDs)**: KR0079 미래에셋 (all quarters),
  KR0080 AIA (2024.4Q-2026.1Q; 2023.1Q-2024.3Q loaded), KR0087 동양 (2026.1Q). Both own-site and
  협회 copies are the same scans. → owner xlsx gold path (KB KR0010 precedent).

---

## 🚧 CROSS-STAGE — CSM waterfall 신한EZ 제외 후속 (owner xlsx 검토 2026-06-10, 보정 06-11)

~~3사 제외~~ → **하나손해(KR0050)·하나생명(KR0097)은 복원**(자사 감사보고서 별도 변동표 실재 — 경영서술 수치와
정확 일치 검증, owner 재지시 2026-06-11). **신한이지(KR0051)만 제외 유지**: 감사보고서 변동표가 천원 단위인데
백만원 오인(×1000 인플레) + PAA 중심사로 일반모형 CSM ~2억 = 워터폴 무의미. override `data/dart/viz/csm_manual_overrides.json`.

- [ ] **designer**: CSM 워터폴/배수 HTML에서 **신한EZ손해**를 'CSM 분리공시 미제공(PAA 중심)' 표기 또는 목록 제외.
- [ ] **publishing**: override 적용은 build_root_masters.py 훅 자동 — 인지만.

---

## 🚧 CROSS-STAGE — K-ICS 금리민감도 신규 feature (2026-06-10 발주 → 06-12 publishing만 잔여)

경영공시 `6-8. 위험 민감도` → 금리민감도 표(경과조치 × measure × ±50/±100bp)를 신규 루트 마스터 `kics_rate_sensitivity.json`으로. 38사 서베이 완료, 스펙 정본 `docs/agents/kics-rate-sensitivity-spec.md`.

- [x] parser: 추출 스크립트 + 마스터(435행)/diag — RS1·RS2 자기검증 통과 (2026-06-10)
- [x] validation: RS1–RS4 룰 구현, 게이트 RED=0 (consolidate_inbox 핸들러 배선만 후속 잔여) (2026-06-10)
- [ ] **publishing: 커밋 번들 추천 + master xlsx 재생성** — inbox `20260612T0900Z__owner__ALL__backlog_digest.md` #1
- [x] designer: K-ICS.html 민감도 패널 (F-SENS-PANEL, 커버리지 29/30) (2026-06-11)

---

## 📬 2026-06-12 — 전 스테이지 backlog digest 발송 (owner 전수 점검)

5개 스테이지 inbox에 `20260612T0900Z__owner__ALL__backlog_digest.md` 발송 (publishing/designer inbox 신설,
`inbox/README.md` layout + route `backlog` 추가). 각 스테이지는 다음 호출 시 자기 다이제스트 드레인.

---

## 중장기 목표 (Mid-long-term goals) — 신규 마스터 테이블 (cross-stage)

(2026-06-06 owner 제안. 착수 전 단계 — 소스 위치만 슥 확인. 우선순위/일정 미정.)

### MLG-1. 듀레이션갭 (Duration Gap) 지표 마스터
- **목표**: 자산·부채 듀레이션 및 듀레이션갭(금리리스크 ALM) 전사·전분기 마스터 테이블.
- **소스 확인 결과**: 정기경영공시 MD(`data/disclosure/FY*/parsed/*.md`)에 "듀레이션" 단어 **0회**(삼성화재/삼성생명/DB 확인) → 표준 경영공시엔 없음. **소스 추가 조사 필요**:
  - 1순위 후보: DART 사업보고서 주석의 **금리위험 민감도 / 자산·부채 듀레이션** 표 (사별 상이, K-ICS 금리위험액 산출 부속).
  - 2순위: 사별 IR 자료 / K-ICS 공시 부속서.
- **다음 스텝(대략)**: (a) DART 사업보고서 1~2개사(삼성화재·한화생명) 금리위험 주석에서 듀레이션 표 존재 확인 → (b) 있으면 parser 시그니처 추가, 없으면 IR 소스로 전환. PL/CSM 마스터와 동일 8-field 스키마 재사용.
- **[조사완료 2026-06-07 야간]** DART 본문(한화생명/삼성생명 주석 50)에 **듀레이션갭 서술 + 만기사다리(16버킷) + 100bp 금리민감도(손익/OCI)** 존재하나 **자산/부채 듀레이션 숫자·갭 자체는 없음**(만기+할인곡선 유도 필요). 손보(삼성화재/DB)는 sparse. → **owner 결정 필요**: (i) 100bp 민감도만 추출(직접 가능), (ii) 듀레이션 유도식 정의(만기가중/할인). 다세션 작업. 상세 → `changelog_parser.md` (j).

### MLG-2. K-ICS 요구자본 세부 도해 (시장위험액→금리위험 / 해지위험액 세부)
- **목표**: 지급여력기준금액 중 **시장위험액 하위(금리/주식/부동산/외환/자산집중)**, **해지위험액 세부**를 분해한 마스터/도해.
- **소스 확인 결과**: `kics_disclosure.json`은 top-level만 캡처(`3. 시장위험액`, `1-5. 해지위험액` 등). **하위 분해 미캡처**. 단 경영공시 MD(`data/disclosure`)에 **"금리위험"·"주식위험" 텍스트 존재**(삼성화재·DB·삼성생명 확인) → **기존 데이터에서 parser 확장으로 추출 가능 (답지 불요)**.
- **다음 스텝(대략)**: (a) K-ICS 요구자본 detail 섹션 표 확인(시장위험액 하위행: 금리/주식/부동산/외환/자산집중) → (b) 기존 K-ICS parser에 하위 항목번호(예 `3-1` 금리위험…) 추가 — 코리안리 `2-1` 시리즈처럼 문자 항목번호 패턴 재사용 → (c) validation gate에 합산검증(Σ하위 = 시장위험액) 추가.
- **[조사완료 2026-06-07 야간]** `fill_subitems_to_disclosure.py`(생명장기 1-1~1-7 파서)가 템플릿이나, 시장위험은 **통합 ①시장위험액 현황 표 부재** + 하위가 사별·위험별 **이질 표**(금리=충격전후 shock표 → 위험액 *유도* 필요·모호, 주식=헤더 embed, 부동산=합계행). clean disclosed 총액 사별 불일치(삼성화재 금리·주식만, 삼성생명 금리만, DB손해 전무). → **PL-Tier2급 사별 핸들러 다수 + 금리위험액 유도규칙 owner 결정 필요.** R11(Σ=시장위험액)은 금리 확정 후. 다세션. 상세 → `changelog_parser.md` (j).

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
