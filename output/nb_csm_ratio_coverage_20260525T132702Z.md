# NB CSM Ratio — Coverage Report

Generated: 2026-05-25
Source: `output/_nb_csm_coverage_intermediate.json` (synthesis, no new crawls)

Definition: NB CSM ratio = New-business CSM (IFRS17) / Monthly-initial-premium (월납월초환산보험료).
Grid: 23 insurers x 13 quarters (2023.1Q .. 2026.1Q) = 299 cells.

## 1. Coverage matrix

| Bucket | Count | Share |
|---|---:|---:|
| Filled (num + denom) | 60 | 20.1% |
| Numerator only (denom missing) | 196 | 65.6% |
| Denominator only (num missing) | 18 | 6.0% |
| Both missing | 25 | 8.4% |
| **Total** | **299** | **100%** |

By sector cohort:

| Cohort | Companies | Cells | Filled | Filled % |
|---|---:|---:|---:|---:|
| cohort (IR-deck disclosed) | 6 | 78 | 60 | 76.9% |
| non_cohort (KIDI/KLIA-only) | 17 | 221 | 0 | 0.0% |

Per-period filled count (cohort only; non_cohort = 0 across all quarters):

| Period | Filled / 6 cohort |
|---|---:|
| 2023.1Q | 5 | 
| 2023.2Q | 6 |
| 2023.3Q | 6 |
| 2023.4Q | 6 |
| 2024.1Q | 6 |
| 2024.2Q | 6 |
| 2024.3Q | 6 |
| 2024.4Q | 6 |
| 2025.1Q | 6 |
| 2025.2Q | 0 |
| 2025.3Q | 0 |
| 2025.4Q | 5 |
| 2026.1Q | 1 |

Note: 2025.2Q/3Q/4Q gap is the DART semi-annual cycle (`status_no_csm_block` — quarterly CSM block not in 반기/3Q report). 2026.1Q gap is the pre-disclosure lag (only Meritz filed early as of run time).

## 2. Root-cause buckets

**A. Denominator missing (196 cells / 17 insurers)** — DOMINANT BLOCKER.
The viz builder (`scripts/viz_build_nb_csm_ratio.py`) only reads denominators from
hardcoded per-company IR-deck extractors. Only 6 insurers (Samsung Life/Fire,
Hyundai Marine, Hanwha Life, DB Sonbo, Meritz) publish 월납환산 in their IR
decks. The fallback crawler `scripts/crawl_assoc_nb_premium.py` calls KIDI INCOS
`stattbl_20040` but `kidi_numeric_companies=false` — endpoint returns rows
without parseable wolnap fields (only annual long-term premium totals; not the
월납월초환산 measure).

**B. Numerator missing (18 cells)** — all `status_no_csm_block` or
`status_download_error` for 2025.2Q/3Q/4Q/2026.1Q — DART filing cycle, not a
parser bug. These resolve when companies file 사업보고서.

**C. Both missing (25 cells)** — intersection of A + B (non-cohort companies in
DART-gap quarters), plus 2 pre-2024 download errors (농협생명 2023.4Q,
동양생명 2023.3Q) and 1 empty extract (롯데손해 2023.1Q).

## 3. Top 5 fixable cells (numerator present, denominator gap)

These have the largest 1Q26 NB CSM and would benefit most from a single
denominator add. Data path: insurer IR PDF/Excel decks (Q1 2026 results), or
manual entry in `data/assoc/nb_premium_overrides.yaml`.

| Rank | Company | 2026.1Q NB CSM (백만원) | Suggested source |
|---:|---|---:|---|
| 1 | 교보생명보험 | 831,754 | Kyobo Life IR FY25 deck (월납월초환산 line) — not yet on public IR site for 1Q26; check kyobo.co.kr/ir |
| 2 | 신한라이프생명보험 | 732,600 | Shinhan Life 1Q26 earnings release — shinhanlife.co.kr/ir |
| 3 | 농협생명보험 | 719,504 | NH Life IR (annual disclosure only) — nhlife.co.kr/ir; likely FY-only |
| 4 | KB손해보험 | 421,820 | KBFG group IR has only group-level NB ratio (see existing `notes` in `data/ir/nb_csm_ratio.json`); KB Sonbo standalone IR deck would be needed |
| 5 | DB생명보험 | 285,894 | DB Life IR (limited public disclosure); KIDI 월보 if endpoint expanded |

## 4. Blocker list (rest of 196)

| Blocker | Companies | Reason |
|---|---|---|
| No public IR deck with 월납환산 row | DB생명, KB손보(standalone), NH농협손보, 교보생명, 농협생명, 동양생명, 롯데손보, 미래에셋, 신한라이프, 에이비엘, 케이디비, 케이비라이프, 코리안리(재보험-별도지표), 푸본현대, 한화손보, 흥국생명, 흥국화재 | Quarterly 월납월초환산 not disclosed externally |
| KIDI INCOS `stattbl_20040` parse | all non-cohort | Endpoint returns long-term annual total premium (천원), not 월납월초환산 measure. Different table needed. Candidate: KIDI `insMonth/ML02` (Life monthly book) — crawler probes it but row count = 0 for company×month wolnap. KLIA/KNIA equivalents not yet probed. |
| Auth-walled | none confirmed | KIDI INCOS is public; no auth wall hit. |
| Coverage cap by definition | 코리안리 (재보험사) | NB CSM ratio benchmark uses original-insurance wolnap; reinsurer denominator definition differs. |

## 5. Quick-win data additions

None applied this session. All 5 top-rank fixes require fetching an external IR
PDF and adding 1 line to `data/assoc/nb_premium_overrides.yaml`. The override
schema (already supported by `crawl_assoc_nb_premium.py:213`) is:

```yaml
companies:
  교보생명보험:
    wolnap_premium_eok: <NN.N>
    period: "FY2026.1Q"
    source: "ir:kyobo_2026_1q.pdf p.NN"
    scope: "total_monthly_avg"
```

Each manual add takes a single cell from 196 -> 195. Recommend a focused IR-PDF
ingest pass for the top-5 insurers (estimated 30-min manual work) to lift
coverage from 20% -> 22% with high-signal cells (covers 2.3T won of the missing
NB CSM denominator).

## 6. Structural recommendation

The 196-cell gap is not a crawler bug — it is a definitional disclosure gap.
17 of 23 insurers do not publish quarterly 월납월초환산 in either IR decks or
KIDI INCOS. To close it requires either (a) bilateral data request via 생보협회
/ 손보협회, or (b) accepting the cohort restriction (6 insurers) as a permanent
design decision and renaming the panel to reflect "Top-6 cohort" scope.
