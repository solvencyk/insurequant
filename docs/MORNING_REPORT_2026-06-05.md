# Morning report — 2026-06-05 (overnight, parser stage)

Owner directives (before sleep): (1) **switch PL Tier-1 to the DART standardized FS API,
fleet-wide, now**; archive the HTML Tier-1 code.  (2) Push **Tier-2 decomposition (장기
CSM상각/위험조정/예실차 + 자동차 + 일반)** across all companies/quarters using the KB gold;
request golds only for the genuinely stuck.  (3) Recorded principle: per-company handlers are
fine, but cross-apply other-company patterns + validate before asking for gold.

## ① FS-API Tier-1 — DONE, gold-validated ✅

You were right and the smoke test proved it: DART's `fnlttSinglAcntAll` is standardized by
**account_id** (보험손익=`ifrs-full_InsuranceServiceResult`, 당기순=`ifrs-full_ProfitLoss`, …),
even though account_nm varies (보험손익/보험서비스결과, 당기순/반기순/연결반기순).  New module
**`scripts/fetch_dart_fs.py`**:
- corp_code by NAME at runtime (no permanent map); cached raw JSON under `data/dart/_fs_api_cache/`.
- **반기/분기 = `thstrm_add_amount`(누적/YTD)**, 연차 = `thstrm_amount`.  This single field choice
  killed every HTML headache at once (3개월/누적, 전환표, 재작성표, 반기순이익).
- basis: OFS(별도) default; CFS(연결) only for the 연결-headline golds {삼성화재, 삼성생명, 메리츠}.
- item19(보험금융손익) = **재보험 풀-네팅** (per your note — golds were inconsistent, API standard wins).
- item21 = 세전−영업이익 residual (22=20+21 closes); item15 = 0 (API has no 기타영업수익 account).

**Result (gold gate, no regression):** Tier-1 passes for ALL golds — 삼성화재 24/24, 메리츠 24/24,
삼성생명·한화생명·롯데 **0 DIRECT fail**.  `build_pl_breakdown` now sources Tier-1 from the API
(HTML `extract_tier1` is **DEPRECATED, fallback-only** — kept for the few cells the API can't serve;
banner added, physical move to `scripts/archive/` left for a supervised pass).

| metric | before | after |
|---|---|---|
| company-quarters | 292 | **308** |
| no_income_statement | 60 | **40** |
| self-check v / i | 125 / 121 | **147 / 121** |
| Tier-1 source | HTML parse | **FS-API 257 / HTML-fallback 35** |

## ② Tier-2 decomposition (장기/자동차/일반) — partial; the real hand-parsing work

This is footnote-only (the API has none), so it stays per-company hand-parsed.  Current 손보
coverage (item4 CSM상각 보유 분기 / Tier-1 분기):

| 회사 | 분해/Tier-1 | note |
|---|---|---|
| NH농협손해 | 12/12 | full |
| KB손해 | 9/13 | KB gold 적용(2025.2Q), 누적-column 핸들러 |
| 메리츠 | 8/13 | Format-B |
| 롯데손해 | 6/12 | section-walker |
| 흥국화재 | 4/13 | recent only |
| 현대해상 | 4/11 | recent only |
| 삼성화재 | 3/11 | recent only |
| DB손해 | 2/13 | recent only |
| 한화손해 | 1/13 | NB-rowspan parse damage (code defect) |

The under-covered ones (DB·삼성화재·현대·흥국 early quarters) need their quarterly note dissected
the same way KB was — each company's quarterly note layout differs (3개월/누적 × 국내/해외 × LOB).

## ③ Gold I'd ask for (Tier-2 quarterly — the genuinely stuck)

Same pattern that worked for KB/한화생명/롯데 (gold → fit → generalize → validate):
- **DB손해 2025.2Q** (worst 손보, 2/13) — one sheet unlocks DB quarterly decomposition.
- **삼성화재 2025.2Q** — quarterly 보험손익 상세 note dissection.
- (현대·흥국 follow the same method once DB/삼성화재 patterns land.)
- 한화손해 = NB-rowspan **code fix**, not a gold need.

Everything else (Tier-1 fleet-wide, CSM waterfall, annual Tier-2) is solid.  CSM waterfall
untouched by this work (separate extractor; KB CSM 4/13→12/13 from yesterday holds).
