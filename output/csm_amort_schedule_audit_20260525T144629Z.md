# F3 audit — CSM amortization schedule coverage

Stamp: 2026-05-25T14:46Z. Scope: `data/dart/viz/csm_amort_schedule.json`
(annual 2024 filings, 23 listed insurers + 서울보증 = 24 rows).

## Coverage

| State | Before | After |
|---|---|---|
| status=ok, all 5 buckets (y1, y1_y3, y3_y5, y5_plus, total) | 11/24 | 21/24 |
| status=ok, sparse buckets only | 8/24 | 1/24 (미래에셋) |
| status=partial / no buckets | 3/24 | 1/24 (한화손해) |
| status=empty / no_csm_table | 2/24 | 1/24 (서울보증) |
| **status=ok (any buckets)** | **19/24** | **22/24** |

Headline: 메리츠화재 chart now renders correctly with all 4 time buckets.

## Per-insurer table (problem cases)

| Insurer | Before | After | Root cause |
|---|---|---|---|
| 메리츠화재 | ok, only y5_plus (값=9,369,907 → 단일 막대) | ok, full 5 buckets (y1=1,078,110; y1_y3=1,772,316; y3_y5=1,404,678; y5_plus=6,932,786; total=11,187,890) | Header `1년 미만`/`1~2년`/.../`30년 이상`. `_YEAR_CELL_RE` (`^\d{1,2}년$`) missed all of them; ranges dumped into y5_plus; `30년 이상` not recognised (only `30년 초과`). New classifier covers 미만/이하/이상/이후/초과 + lo~hi ranges. |
| 미래에셋생명 | partial (no header, no buckets) | ok (y5_plus, total — best the source allows) | THEAD missing; column header lives in `rows[1]`. New header inference promotes that row. Source itself lacks a separate 1년 bucket (uses `1~10년` aggregate), so finer buckets cannot be derived without per-portfolio breakdown logic. |
| 흥국화재 | partial (no header, no buckets) | ok, full 5 buckets | Same THEAD-less issue as 미래에셋; row 1 has full `1년…30년 이후 합계` header. Fixed by header inference. |
| 농협생명 | ok, missing total | ok, total derived (43,606) | Header `총계` not matched (`합계 in 총계` was substring-False). New classifier recognises 총계/소계/합계/계; missing 합계 column now derived from bucket sum. |
| 신한라이프 | ok, missing total | ok, total derived (37,819) | Header `합 계` with internal space failed the substring check. Same fix. |
| 푸본현대 | ok, only y5_plus | ok, full 5 buckets | 2-row header (`예상 상각 기간` band + `1년 이하, 1년 초과 2년 이하, …, 30년 초과`). New classifier handles `N년이하` / `N년초과M년이하` / `30년초과`. |
| 한화생명 | ok, only y5_plus (재보험 block) | ok, full 5 buckets (direct issue block) | Multiple candidate blocks with score 6; picker chose first (재보험). New picker downranks reinsurance-only captions and prefers wider year-bucket headers. |
| 한화손해 | ok, bogus rollforward numbers | partial | All source blocks are §(5) measurement rollforward; no dedicated CSM amort schedule in this filing. Picker now correctly returns no_rows. **Source-level limitation** (csm_extractor doesn't capture an A-form for this insurer). |
| 케이비라이프 | ok, weird tiny y1_y3 | ok, sensible buckets (y1=152,557; y1_y3=271,554; y3_y5=239,005; y5_plus=1,057,669; total=3,010,510) | Multi-row product header (Non-Par/Indirect-Par/Direct-Par × product); time buckets in column 0. New transposed-table branch handles this. |
| 흥국생명 | ok | ok (matches baseline; total now 2,242,699) | Already worked via tail-numeric fallback; now also routes via classifier. |
| 교보생명 | ok | ok (regression fixed via clamped caption score) | Mid-debug regression: picker briefly preferred a short B-form summary; clamping caption bonus + tie-breaking on bucket-column count restores the detailed Form A pick. |
| 삼성생명 | ok (sparse y5_plus 4,222,423) | ok (y5_plus 9,031,129) | Now picks the wider Form A `(6) 발행한 보험계약에 대한 보험계약마진의 기대상각기간별` block; prior pick miscounted y5_plus. |

Remaining residual gaps (acceptable):

- **서울보증보험** — empty. PAA / `보험계약마진` 단어 미존재 (documented in `claude-agent-ifrs17.md` §3.4).
- **한화손해보험** — partial. No CSM amort schedule emitted by source extractor (`*_csm.json` only contains rollforward measurement tables). Out of F3 scope (csm_extractor fix needed).
- **미래에셋생명** — ok, only y5_plus + total. Source filing uses `1~10년` as the lowest bucket; no finer split available without per-portfolio aggregation logic (would need source-extractor rework).

## Files touched

- `scripts/viz_build_ifrs17_panels.py` — surgical edits, +1 net new helper module, +3 helper functions in `extract_amort_schedule` path. Other extractors (`extract_pl_breakdown`, `extract_bs_snapshot`, `extract_sensitivity`) untouched.
  - L13–21: 4 new regex patterns (`_RANGE_TILDE_RE`, `_RANGE_CHOGWA_IHA_RE`, `_AT_OR_UNDER_RE`, `_OVER_ONLY_RE`).
  - L62–75: `header_has_year_buckets` keyword set expanded (총계, 이후, 이하, 미만).
  - L78–116: `_classify_bucket_cell` — central routing of any header cell to {y1, y1_y3, y3_y5, y5_plus, total}.
  - L119–135: `_bucket_for_range(lo, hi)` — range upper-bound routing.
  - L151–173: `_bucket_indices` rewritten to delegate to `_classify_bucket_cell`.
  - L181–248: `_row_has_year_buckets`, `_infer_header_from_rows`, `_amort_caption_score`, `_bucket_columns_count`, `_pick_amort_block`, `_extract_transposed_amort`.
  - L267–386: `extract_amort_schedule` rewritten — eligibility now accepts THEAD-less and transposed tables; transposed branch handles row-keyed layouts (KB라이프); derives `total` when no 합계 column exists.
- `data/dart/viz/csm_amort_schedule.json` — regenerated.

## Verification

Spot-check 메리츠 against source row `발행한 보험계약 → 장기손해`:
1,078,110 + 940,805 + 831,511 + 741,679 + 662,999 + 2,458,195 + 2,617,219 + 1,117,499 + 739,873 = 11,187,890 (matches `total`). Bucket sums reconcile.

## Constraints honored

- Did not touch `scripts/forward_capital_simulation.py`, `viz_build_nb_csm_ratio.py`, `viz_build_csm_waterfall*.py`, K-ICS code, `templates/`, or git.
- No new DART filings pulled; reused on-disk `data/dart/extracted/*_csm.json`.
- File saved UTF-8 (no BOM).
