# Insurequant TODO — Downloader Stage

Stage 1 of 5 in the workflow split. See `CLAUDE.md` for the full 5-stage index.

**Prompt:** `docs/agents/claude-agent-downloader.md` + `docs/agents/source-catalog.yaml`
**Cross-stage TODO:** `TODO.md` (root)
**This file:** active + done items scoped to data collection only.

Last updated: 2026-05-30O (**흥국 amended PDF 사용자 수동 교체로 file-integrity 100%**. 사용자가 Fasoo DRM 우회해서 직접 받아 교체 → 정상 %PDF-1.4. 재검증 1,965/1,965 OK. 직전 2026-05-30N (**DART batch script canonical-path refactor 완료**. `scripts/_dart_path_helpers.py` 신규: kics 원수사명→KR 코드 lookup + `quarterly_raw_dir`/`annual_raw_dir` (Reorg #2 layout 산출). 3개 batch script 갱신: `ifrs17_batch_all.py`, `ifrs17_batch_historical.py`, `ifrs17_ingest_audit_annual.py`. 변경은 path 결정 부분만 (extract/parse 로직 무변경). historical은 annual(A001) 분기와 quarterly(A002/A003)를 갈라 처리(annual은 rcept_no가 dir 이름에 들어가니 fetch_rcept를 out_dir 결정 전에 호출). _KICS_NAME_OVERRIDES에 AUDIT_REPORT_ANNUAL 5사 + 한화생명 표기변형 등록(kics 누락 케이스 보완). `scripts/_dart_path_helpers_smoke.py`로 9/9 케이스 검증(메리츠/삼성생명/IBK/KB라이프/코리안리/AIA + quarterly + group holding).)

Latest downloader work = **Reorg #2 (2026-05-30j)**: 사용자 지적 "DART랑 KIDI 폴더는 정리가 하나도 안돼있어, assoc 폴더는 정체가 뭐냐" 받아 1차 reorg에서 남겨둔 DART/KIDI/assoc 마저 정리. 변경:

1. `data/assoc/` → `data/_derived/` rename (8 script path constant 갱신; assoc는 gathering output이라 underscore 접두로 명시화. templates/data/assoc archive)
2. KIDI `raw/<stamp>/` 494 files → `data/kidi/FY####_Q#/raw/<KR>_<YYYYMM>.json` (yyyymm 03/06/09/12 → Q1-Q4 매핑), 38사×13Q 분기별 균등 배치
3. DART `raw/<name>_<rcept>/` (77 annual) → `data/dart/FY<year>_Q4/raw/KR####_<name>[__cons]_<rcept>/` (year = rcept_year - 1, `__cons` 접미는 연결재무 표시)
4. DART `raw_history/<name>/<YYYY.QQ>/` → `data/dart/FY<year>_Q<q>/raw/KR####_<name>/` (period reverse: 회사>분기 → 분기>회사 트리)
5. dedup: rcept-suffixed vs simple 중복 55개 archive

영향 script 8개 path constant 갱신. **KIDI ingest script도 신규 다운로드를 canonical layout으로 write하도록 refactor 완료.** DART batch scripts(`ifrs17_batch_historical` / `ifrs17_batch_all` / `ifrs17_ingest_audit_annual`)는 OLD path로 write할 위험 — **다음 세션 refactor 필요** (아래 REORG2-DART task). 총 archive 788MB (445MB reorg#1 + 343MB reorg#2).

직전 작업 (Reorg #1, 2026-05-30i) = Downloader workflow 정리 완료 (5 source audit + canonical 폴더 reorg + master prompt). Workflow `wf_f8b5a806-a78` (7 agents, 427k tokens): Phase 1 = 5 source inventory 병렬; Phase 2 = 159 moves 0 errors → `<source>/<period>/raw/KR####_<name>` 적용; Phase 3 = `docs/agents/claude-agent-downloader.md` + `docs/agents/source-catalog.yaml`.

---

## Active follow-ups (next sessions)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| F7 | **KOSIS 손보사별 손해율 시계열 ingest** | 🔴 P1 | 출처: 국가통계포털 KOSIS `orgId=382, tblId=TX_38202_A1561`. JSON API 공개 → 자동화 쉬움. 손해보험사별 원수보험료/보유보험료/경과손해율 (개별사 × 분기/연간). 현재 손해율은 PDF/HTML 파싱 기반 → KOSIS 교차검증으로 품질 보완. **액션**: `scripts/ingest_kosis_loss_ratio.py` 신규 + `data/kosis/<stamp>/` |
| F8 | **손보협회 비교공시 (consumer.knia.or.kr) — GA 인사이트** | 🔴 P1 | 핵심 항목: (a) **채널별 불완전판매비율** (GA/직판/방카 구분) (b) **설계사정착률** (c) **민원발생현황** (d) **보험금 부지급률** (e) **보험금 지급지연율**. **액션**: 사이트 구조 probe (JS-rendered 가능성 점검) → API 또는 scrape 결정 → `data/knia_consumer/` |
| F9 | **data.go.kr 금융통계 API 추가 연동** | 🟠 P2 | 이미 자본성증권 (15059611) 연동 패턴 있음. 추가: (a) `15061307` 금융통계손해보험정보 (b) `15061306` 금융통계생명보험정보 (c) `15094797` 실손보험정보. **액션**: `src/bonds/fsc_client.py` 패턴 재활용해서 `src/finstat/` 신규 모듈 작성 |
| F10 | **GA 통합공시 (gapub.insure.or.kr)** | 🟠 P3 | GA별 불완전판매비율/계약건수/모집실적. **액션**: 사이트 구조 probe |
| F14 | **규제 뉴스 피드** (roadmap §1E) | 🟠 P3 | 최근 1주 규제뉴스 스크래핑 + 키워드 피드백 학습 랭킹. 큐레이션 피드(자동발행 X) |
| MISC-SEIBRO | Seibro HTML fallback | 🟢 low | m.seibro.or.kr smoke ok; lower priority since FSC works |
| ~~REORG2-DART~~ | ~~DART batch script 3개 canonical-layout refactor~~ | ✅ **2026-05-30N 완료** | `scripts/_dart_path_helpers.py` 신규 + 3 script 갱신 + smoke 9/9. 다음 분기 fetch는 `data/dart/FY<year>_Q<q>/raw/` canonical 위치에 쌓임 |
| BATCH-HISTORICAL-FIX | `ifrs17_batch_historical.py` 정정 rcept picking 버그 | 🟠 P2 | DART는 정정([기재정정], [첨부정정]) 공시가 원본보다 먼저 나올 수 있음 → 잘못된 rcept picking → status=014 'file not found' 에러. **고침 방향**: 정정 prefix 제외하고 가장 늦은 rcept (또는 원본 사업/반기/분기보고서)를 picking. REORG2-DART와 같은 PR에서 같이 처리 권장 |
| F15-DL | 동양생명 2025.2Q~2026.1Q 재다운로드 검토 | 🟠 P2 | (F15 본체는 parser 버그 — `TODO.md`) 추출단계에서 wide `<TE>` 표의 잔액(기초/기말)행이 전부 0으로 들어옴 → 원본 다시 받아야 할 수도 있음. 재다운로드 후 재파싱이 효과적인지 먼저 확인 |
| FUTURE-DL | DART 별첨 fetch endpoint 조사 (KB/메리츠/NH FY2025 LOB) | 🟠 P2 | KB/메리츠/NH FY2025 사업보고서는 LOB 표를 별첨 감사보고서로 분리. 결정 2026-05-30: **fetch 안 함** (본문에 다 있음, 회사별 라벨 변형 처리로 해결). 단 별첨 endpoint 위치는 future reference로 기록 — 새 이슈에 필요 시 조사 |

**전략적 시너지 (코리안리 리포트 인과 체인 재현):**
- F8 (설계사정착률) + F8 (채널별 불완전판매비율) + 37회차 해지율 (별도 source)
- = "GA 채널 → 해지율 → 손해율" 인과 체인을 공시 데이터만으로 재현
- → insurequant 프리미엄 기능 후보

---

## User decisions (downloader-scoped)

| # | Decision | Date |
|---|----------|------|
| D5 | API keys: repo root `.env` only (gitignored). `OPENDART_API_KEY` / `DATA_GO_KR_BOND_ISSUANCE_KEY` / `DATA_GO_KR_BOND_REDE_KEY`. Never commit/log key values | 2026-05-24 |
| D6 | Bond Call rule: issue + 5y for ALL bonds (Korean market convention; ignore "콜" keyword gate). Past 5y = assume `called` (de facto mandatory per thebell/흥국 cases) | 2026-05-24 |
| DL-FYR | **Next quarter onwards (2026.2Q+)**: find URLs / XPaths yourself. 2026.1Q only was user-provided. Reuse existing configs, swap only period-specific labels. Escalate to user only if site structure fully changed | 2026-05-30 |
| DL-NOATTACH | **Don't fetch DART attachments (별첨/감사보고서 zip).** Body XML has all IFRS17 disclosures. Verified 2026-05-30 (한화 647 / KB 259 / 농협생명 176 / 라이나 audit 55 / AIG audit 55 occurrences of `보험계약마진` in body) | 2026-05-30 |
| DL-NOTSKIP | KR0029 AIG + KR0150 SGI **K-ICS skip** (no PDF on their own sites), BUT **DART**에서는 받을 수 있는 만큼 받음 (AIG = "에이아이지손해보험" corp_code 00983606 / SGI = 2024.4Q 이후 분기보고서 시작) | 2026-05-30 |

---

## Done — recent (downloader-scoped)

| ID | Task | Done | Notes |
|----|------|------|-------|
| ~~F2~~ | NB CSM 배수 — KIDI ML01/MN07 crawler | 2026-05-30c | endpoint `POST /insMonth/getQueryResult.do`, `queryId=getML01List|getMN07List`, `comp_type=L01~L86|N01~N80`, `data_year=YYYYMM`. 38사×13Q=494 fetch, 0 errors. `data/kidi/raw/<stamp>/<KR>_<YYYYMM>.json` + `data/kidi/premium_summary.json`. `crawl_assoc_nb_premium.py`에 `_parse_kidi_summary` + `KR_TO_WATERFALL` 추가 → `nb_premium_wolnap.json` 6→328 entries |
| ~~DL-FY26Q1~~ | FY2026.1Q full ingest (손보 17 + 생보 22 + IR 13 + DART) | 2026-05-30 | 손보 22.5MB / 생보 29MB / IR 20.8MB; 신한라이프 generic filename pdfminer 첫 페이지로 식별 |
| ~~DL-DART-AUDIT~~ | DART raw 100% audit + gap fill | 2026-05-30h | LISTED 23×13Q=299/299 + NON_LISTED 8사 + AIG + audit-only 5사 + 서울보증. `data/dart/_inventory_manifest.json`: 76 annual rcept + 303 period zip |
| ~~MISC-BOND-KEYS~~ | FSC API keys in .env | done | DATA_GO_KR_BOND_ISSUANCE_KEY + REDE_KEY |
| ~~MISC-BOND-INGEST~~ | FSC bond issuance + Call schedule ingest | done | 2026-05-25 v2 alias-loop fix. Latest pull 24 insurers. 15 missing accepted (외국계/디지털/특수법인 + KR0008/KR0069 likely no capital-instrument issuance) |
| ~~MISC-BOND-NORMALIZE~~ | Bond schedule → per-ISIN calendar | done | Latest `data/bonds/normalized/20260525T061945Z/`. tier1 **63** + tier2 261. `_classify_tier` recognizes `(신종)` / 신종자본증권 / 하이브리드 |
| ~~MISC-IR-MERITZ~~ | Meritz Financial Group factsheet xlsx ingest | done | 2026-05-25 — `data/ir/meritz/` (xlsx + extracted JSON + README). 1Q26: K-ICS 240.74%, CSM 112,917억, NB CSM mult 12.61x |
| ~~IFRS-HIST~~ | Historical 13Q ingest 2023.1Q ~ 2026.1Q | done v2 | `scripts/ifrs17_batch_historical.py` + `_promote_history_to_measurement.py`. 299 targets → 257 ok + 2 partial + 34 no_csm_block + 5 errors. 사업보고서 23/23 거의 완벽 |

---

## Reading order for downloader subagent

When invoked, read in this order:

1. This file (`TODO_downloader.md`) — current state and documented exceptions
2. `docs/changelog_downloader.md` — history (what previous sessions did)
3. `docs/agents/claude-agent-downloader.md` — master prompt (mission + 5 sources catalog + canonical layout)
4. `docs/agents/source-catalog.yaml` — machine-readable URL/XPath catalog
5. `data/dart/_inventory_manifest.json` — DART coverage; avoid re-fetching
6. `data/disclosure/_meta/FY*/_manifest.json` — per-period manifests
7. `data/ir/_*.json` — IR manifests (`_db_manifest.json`, `_db_decks_manifest.json`, `_hyundai_manifest.json`, `_kr_map.json`)

For cross-stage context (other 4 stages), see root `TODO.md`.

---

NOTE: English only where Korean encoding is fragile. Korean content preserved here is read-only history; new entries prefer English. See `CLAUDE.md` "Document/TODO Encoding Rule".
