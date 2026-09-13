# K-ICS lane — quirks & traps

The failure modes that have actually cost time. Crystallized from user-memory (`reference_kics_company_quirks`,
`reference_kics_capital_tiering`) + session experience (2026-05 → 2026-06). Cross-check before trusting a value.

## Table of contents
- [Cadence: even-Q vs odd-Q](#cadence-even-q-vs-odd-q)
- [Parent-zero ⇒ children absent](#parent-zero--children-absent)
- [Unit + sign](#unit--sign)
- [Capital tiering limits](#capital-tiering-limits)
- [Per-company quirks](#per-company-quirks)
- [Reconciliation cross-checks](#reconciliation-cross-checks)
- [Validation blind spots to probe](#validation-blind-spots-to-probe)
- [Scanned PDFs: OCR is a lead, not a source](#scanned-pdfs-ocr-is-a-lead-not-a-source)
- [Windows / encoding](#windows--encoding)

## Cadence: even-Q vs odd-Q
- **2Q/4Q = 반기/연간 full form**: 시장위험 36-40, 금리위험 IRR 41-46, 생명장기 29-35 breakdowns **must exist**.
  A missing decomposition here is a **parser gap → RED**, not legitimate.
- **1Q/3Q = 간이공시**: parent items only; 36-40/41-46 legitimately absent → `19_market`/`36_irr` cadence **SKIP**.
- **But verify the raw.** The gate's `_scan_breakdown_presence` reads the MD: if a real breakdown table is present
  on an odd quarter (≥3 distinct 시장 sub-risk rows — e.g. 카카오 2023.3Q had 시장 248/금리 15/부동산 244), it is a
  **true positive** and must be loaded, *not* cadence-SKIPped. Hiding a real source table is the error to avoid.

## Parent-zero ⇒ children absent
`item17`(생명장기)=0 (보증보험사 / 디지털 손보 with no life book) means **29-35 cannot exist** — a diversified
parent is ≥ its max single child, so a nonzero child with a zero parent is structurally impossible. Likewise
`item19`=0 ⇒ 36-40 absent. A nonzero child is a **cell-shift misparse** (commonly a 일반손해 대재해 row leaking
into the 생명장기 1-7 (item35) slot). Guards: `fill_subitems` parent-gate (item17≤0 ⇒ drop all matches) +
`_is_life_catastrophe_table` (item35 only from life-catastrophe tables, excludes 일반손해/자연재해/풍수해/지진);
validator `_parent_zero_child_nonzero` blocks the gate. Real cases removed: 서울보증 25.4Q/23.4Q item35=5212/5264,
카카오 23.3Q item35=4.72 (all item17=0). (See session 2026-06-16; [[reference-kics-company-quirks]].)

## Unit + sign
- **Source tables are usually 백만원; JSON is 억원** (÷100). Full ladder: 억원 ÷1, 백만원 ÷100, 만원 ÷10⁴,
  천원 ÷10⁵, 원 ÷10⁸. Unit hint parsed from `(단위: …)` lines (handles docling-split hints). Life-catastrophe and
  생명/장기/총계 breakdown layouts **force 백만원** even when the inherited hint looks stale. Never assume.
- **Rounding caveat:** the core extractor rounds 1-28 to integers, so a tiny `item19=2` (from 248백만) can fail
  sqrt-reconcile against precise 36-40 subs = a **documented micro RED**, not a parse error. 36-46 keep 2-decimals.
- **△ (세모) = negative.** `_parse_value` maps `△ ▲ ▽ ▼ −` and `(123)` paren-form → negative. A negative
  지급여력비율 (예별/구MG 2025.4Q = **-8.24%**, 자본잠식; -13.11% at 2026.1Q) is **real** for a distressed insurer,
  not a sign bug. Any chart/table you add must render negatives as △ ([[feedback-samo-negative]]).

## Capital tiering limits
- 기본자본 자본증권 인정한도 = **SCR × 10%** (조건부 15%); 보완자본 한도 = **SCR × 50%** ([[reference-kics-capital-tiering]]).
- **tier1 소진율 100%+ in the data** = a Ⅴ.1 excess parsing-omission artifact (cascade → 이중계상). **But the
  donut viz is 발행/한도 so >100% is legitimate** — owner ruling = show "100%+" on screen. Don't "fix" the donut.
- **권고선(recommended floor) = 지급여력비율 130% / 기본자본비율 50%** — NOT 150%. (Common mis-set.)
- 기본자본비율 sanity: item2 ≤ item1 (기본자본 ≤ 지급여력금액); ratio >100% is normal, not an error.

## Per-company quirks
| company (code) | quirk | handling |
|---|---|---|
| AIA (KR0080) | 경과조치 **미적용** → 적용전 = 적용후 | duplicate 적용후 = 적용전 in sensitivity; not a missing-data RED |
| 코리안리 (KR1000) | 자동차보험 = **일반손해 sub (0)** | don't expect a separate 자동차 risk line |
| 서울보증 (KR0150) | **보증보험사** — 생명장기위험액(item17)=0 (본업은 일반손해 item18) | 29-35 absent is correct; 과거 interim Q1-3 = refetch-impossible structural gap (SGI_QUARTERLY_STRUCTURAL, census whitelist) |
| 예별손해 / 구 MG손해 (KR0004) | **자본잠식** (지급여력비율 음수); rename MG→예별 2025; raw only FY2025_Q4 + FY2026_Q1 on disk | △ negatives are real; 경과조치 **적용사**(TER/TIRR) so 적용후 ≠ 적용전; 2023-2025.3Q never existed → downloader |
| 한화생명·신한라이프·교보 (internal model) | publish **per-scenario 금리위험액 directly** → standard derive_irr(41-46) won't reconcile to item36 | owner-approved **INTERNAL_MODEL_36IRR_EXEMPT** (RED→SKIP); company values correct, not a parse error |
| 카카오페이손해 (KR1098) | **micro-insurer** (single-digit 억); some quarters image-only PDF | tiny item19 → micro-reconcile RED documented; image quarters → owner OCR; 2025.2Q/3Q text-loaded |
| 삼성생명·신한라이프 | **split-table**: item1(amount) and item14(SCR) in separate MD sections | `extract_kics_summary_overview_rows` + `make_quarter_column_picker` (N/4분기); strip `(A)/(B)/(A/B)` suffixes |
| 신한 (OCR) | char corruption: middle-dot `∙`, `보험→보X위`, `손액보험→손해보험` | label-normalize variants |
| KR0010 KB손해 · KR0079 미래에셋 | **image-only** 금리위험액 / core tables | KICS-IMG cohort: tol 10.0, owner OCR for missing cells |
| 동양생명·하나생명·카카오 (various Q) | core or market table = **full-page image** (text layer empty) | owner OCR/gold — don't fabricate; document as census gap, not expected-absent |

## Reconciliation cross-checks
- `item27 = item1 / item14 × 100`; `item28 = item2 / item14 × 100`; `item14 = item15 − item22 + item23`
  (store item22 as **+magnitude**); `item1 = item2 + item3`.
- `19_market`: `item19 = √(Vᵀ·MARKET_M·V)`, V=[36-40]. MARKET_M: diag 1.0; FX–equity (37,39) = **−0.25**;
  자산집중(40) with all = **0**; every other pair = 0.25.
- `36_irr`: `item36 = √(max(R상승,R하락)² + max(R평탄,R경사)²) + R평균회귀`, R = base(41) − scenario(43-46),
  평균회귀 = 41−42 signed.
- `8_life`: `item17 = √(Sᵀ·R7·S)`, S=[29-35]; sum(29-35)/item17 ≈ **1.2-1.6** (diversified) — ratio <0.95 or >2.5 flags.
- **dedup:** when duplicate rows disagree, adopt the **항등식-satisfying** value ([[reference-kics-company-quirks]]).
- A None item that breaks an identity is a **parse miss**, not a real 0 — derive from the closure + source.

## Validation blind spots to probe
The gate's 5 known blind spots ([[feedback-validation-blind-spots]], [[feedback-coverage-census-mandatory]]):
intra-FY 기초 consistency · 0-value blindness (equations close with all-zeros) · lower-bound plausibility ·
source-trust · **provisional gate snapshot during concurrent backfill** + **cell-level census**. A missing cell
is **never** acceptable — SKIP-on-missing defeats validation. Probe the expected (회사 × 분기 × 항목) grid +
parent-child completeness, not just rule pass/fail.

## Docling loses pages three different ways — check the front matter, not just the body
Measured 2026-09-01 over all 39 FY2026_Q2 filers (inbox `20260831T0700Z`). "The section isn't in the MD"
has **three unrelated causes**; do not treat them as one:

1. **Never selected (cap eviction).** `_find_keyword_pages` ranks pages by `matched_count` and
   `_select_page_ranges` keeps only the top `max_keyword_hit_pages` (20). 요약/총괄 pages carry 5-8 ratio
   keywords; a `6-4. 시장위험 관리` opening page names its own risk once and scores **1**, so it ranks 21-36
   and is dropped. Fixed by `PRIORITY_KEYWORDS` (section-anchor terms bypass the cap; costs ~0.9 extra
   pages/filer, closed 15/15 anchor gaps). `parse_scope: keyword_window_priority` marks a file where it fired.
2. **Selected but silently dropped — `std::bad_alloc`.** Docling's preprocess stage OOMs on runs of pages,
   logs it, marks the document `PARTIAL_SUCCESS`, and returns it **with those pages still in
   `document.pages` but owning no items**. Contiguous runs, position-dependent (not a property of the page —
   same page converts fine alone), so the same PDF loses *different* pages on different runs. `_convert_one`
   now inspects the status, finds zero-content pages, and re-converts them one page at a time (5/5, 9/9,
   16/16 recovered in practice). Front matter records `docling_status` / `docling_{dropped,recovered,
   unrecovered}_pages`.
3. **Table reached the MD but the label column is unreadable.** Some filers (KR0094 신한라이프, and the
   KR0051 sensitivity table) print row labels one character per line ("사\n망\n위\n험"); docling turns that
   into cells that match no sub-risk name. Page selection is fine — recover from the raw PDF with fitz
   word-bbox y-clustering, not by touching the window.

"item36 present, 37-40 absent" is **not a fourth mechanism** — it is (1) and/or (2) hitting the detail pages
while the page carrying the 총괄 row survives.

**The guard:** folded into `quality_check.score()` (2026-09-01 rewrite — an earlier standalone
`page_selection_flags()` helper with `SECTION_LOST_*`/`DOCLING_PAGES_LOST`/`PAGE_COVERAGE_LOW` enum flags did
**not** survive that rewrite; don't grep for those names, they're gone). On even quarters `score()` checks the
*converted body* for the 6-4/6-8 section markers (`_RE_REQUIRED_MARKET`/`_RE_REQUIRED_SENSITIVITY`) plus a
catastrophic-failure floor on `source_page_ranges`-vs-PDF-page-count (`REVIEW_RATIO_FLOOR=0.10` — deliberately
low; the ratio does NOT separate good/bad files in the 18.8-100% overlap band, ratio_calibration probe). Either
failing routes to `review` and appends `"<key>=<detail>"` strings to `QualityReport.page_flags`
(`missing_window=<label,label,...>` / `ratio_critical=<ratio>`), which `run_harness.py --stage quality` groups
and counts by key in its printed summary. **This field went missing for 10 days (2026-08-31→2026-09-11):** a
later commit added the `run_harness.py` block that reads `r.page_flags` assuming `score()` still exposed it
from the pre-rewrite design, but the rewritten `QualityReport` dataclass never grew the field back — so
`--stage quality` raised `AttributeError` on the first report, every run, until inbox `20260831T0700Z` iter 4
added `page_flags` back onto the dataclass. Lesson: a helper folded into a bigger function can silently drop an
attribute another file still reads — nothing type-checks `run_harness.py` against `quality_check.py` here. The
guard routes; it does **not** block push (`prepush_check.py` does not call `--stage quality`). Pinned by
`tests/unit/test_docling_page_guard.py`.

## Scanned PDFs: OCR is a lead, not a source
Some filers publish a raster-only PDF for part or all of the filing (`data/_derived/kics_source_textlayer.json`
status `SCANNED_SECTION` = right document, K-ICS section is an image; `UNREADABLE` = whole document scanned —
the ticket-level shorthand "image-only" covers both). The normal pipeline runs `do_ocr=False` on purpose (text
layer only — avoids torch/RAM spikes), so these sections yield nothing.

**docling's own OCR path is not a safe substitute — at any scale.** `docling/models/stages/ocr/easyocr_model.py`
hardcodes `EasyOcrModel.scale = 3` (216dpi); no pipeline option reaches it (`PdfPipelineOptions.images_scale`
does not apply to the OCR stage — scales 1.0/2.0/3.0 through that option produced byte-identical MD). Measured
on 미래에셋(KR0079) 2026.2Q p19, 9 ground-truth figures read off the rendered page:

| scale | dpi | correct |
|---|---|---|
| 1 | 72 | 3/9 |
| **2** | **144** | **5/9 (least-bad)** |
| 3 (docling's hardcoded default) | 216 | 2/9 |
| 4 | 288 | 2/9 |

216dpi is exactly where this filer's font makes EasyOCR misread a leading '1' as '7' (`155.3→755.3`,
`13,473→73,473`, `10,265→70,265`) — a systematic, plausible-looking wrong number, not visible noise.
`scripts/ocr_parse_scanned_disclosure.py --ocr-scale` (default 2) exists as a monkeypatch — docling exposes no
such option natively — and already defaults to the least-bad setting. **Even so, 5/9 means the MD lies close
to half the time.**

**Decision (2026-09-01, reaffirmed 2026-09-11 — inbox `20260831T0800Z`): do not promote `--ocr-scale` into
`docling_parser.py`/`run_harness.py --stage parse` as an unattended default, and do not build a fitz+EasyOCR
bypass pipeline.** No accessible scale clears half, so promoting the least-bad one would only formalize a
~44%-wrong default — worse, one whose errors *look* plausible enough to pass a casual read. Instead: render the
page directly (`fitz.Matrix(dpi/72, dpi/72)`, 150-200dpi, no OCR engine in the loop at all), read it — by eye or
by a vision-capable model — and cross-check every value against a rule-engine identity (e.g. `item48 ==
item14×50%`) before it ever reaches the master. Measured across ~150 cells resolved this way (KR0071 2024.4Q·
KR0079 2023-2025.4Q·KR0010 2025.4Q·KR0080 2025.2Q): **0 mismatches** against independently-confirmed values
(one single-digit reader typo, caught by the item48 identity itself — not a rendering problem). Reusable
helper: `scripts/_probes/render_kics_page.py` (single page or contact sheet, no OCR call). Keep
`ocr_parse_scanned_disclosure.py` only for bulk/unattended conversion where nobody will verify every page by
hand; for a specific small `SCANNED_SECTION`/`UNREADABLE` cohort, direct render+read is both more accurate and
faster (no docling layout/table-model pass, no torch inference).

**Any value read off a scanned-section MD — docling-OCR or otherwise — is provisional until render-verified.
Never write it into the master on MD text alone.**

## Windows / encoding
- python full path: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` (docling lives here; not on PATH).
- **Never inline multi-line `python -c`** — hangs the shell and wedges Workflow subagents permanently
  ([[feedback-workflow-multiline-python-hang]]). Write a `.py` in `scripts/_probes/`, or use Read/Grep.
- `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")` for Korean (console is cp949). Note
  `git show <commit>:file | python` corrupts Korean via the pipe — write bytes to a temp file and `read_text(utf-8)`.
- All docs/inbox markdown: **UTF-8 no BOM**. If Korean would garble in your write path, write English; read back the
  first line after writing ([[feedback-no-garbled-korean]]). `값_적용후` / fill_period rows: schema is inconsistent
  (most rows lack 값_적용후) — don't treat its absence as an error.
