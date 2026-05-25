# Meritz Financial Group IR Factsheet Ingest

English only per project encoding rule (CLAUDE.md). All file I/O is UTF-8.

## Source

- **IR landing page:** https://m.meritzgroup.com/mo/ko/ir/ir1.do
- **JSON manifest endpoint:** `POST https://m.meritzgroup.com/web/ir1_1_search.do`
  payload `{bd_div_cd: 'IR011', acrsl_anun_yy: '', currentPage: '1', Mobile: 'All'}`
- **Factsheet xlsx URL (1Q26):**
  https://m.meritzgroup.com/commfiles/hld/attach/2026/20260514/202605141545243300007U.xlsx
  - File name on server: `MFG_202603(k).xlsx` (MFG = Meritz Financial Group, 202603 = period end 2026.03, k = Korean)
  - Size: 884,985 bytes
- **Release date (KST):** 2026-05-14 (1Q26 quarterly results)
- **Extraction date:** 2026-05-25

Note: the IR page itself is served EUC-KR encoded and renders content via AJAX
(`Search0/Search1/Search2` jQuery calls). The xlsx download path requires the
`/commfiles` prefix — links exposed in the JSON manifest are relative
(`/hld/attach/...`) and 404 without it.

Per user decision #2 (TODO row, 2026-05-24): Meritz Financial Group factsheet
replaces the legacy Meritz Hwajae standalone IR scrape. The xlsx already contains
both group-consolidated and Meritz Hwajae standalone tabs.

## Files in this directory

| File | Purpose |
|------|---------|
| `factsheet_202603.xlsx` | Raw IR factsheet, period 1Q26 (FY end 2026.03) |
| `extracted_202603.json` | Normalized KPI snapshot for the latest period (1Q26) |
| `extract_meritz_factsheet.py` | Idempotent extractor; rerun on new factsheet by editing `PERIOD` / `PERIOD_KEY` constants |
| `README.md` | This file |

## Sheets in source xlsx

19 sheets total. Insurance-focused tabs used:

- `Group highlight` — Meritz Financial Group consolidated PL, BS, RoE, BPS, EPS
- `CSM` — Meritz Hwajae CSM movement, new business CSM, NB CSM multiple, amortization
- `Insurance_ALM` — Meritz Hwajae K-ICS (지급여력비율), ALM matching ratio
- `Insurance_Condensed PL` — Meritz Hwajae summary PL (insurance/investment PnL, NI)
- `Insurance_Efficiency` — Meritz Hwajae loss ratios (general / auto / long-term risk)
- `Insurance_Condensed BS` — Meritz Hwajae summary BS (not extracted; in scope if needed later)
- `Insurance_NewP` — New business by product (not extracted in v1; broader scope)

Sheets ignored (out of scope — Meritz Securities entity): `Securities_*`.

## KPIs extracted (1Q26)

### Meritz Hwajae standalone (메리츠화재)

| KPI | Value | Source |
|---|---|---|
| K-ICS available capital (지급여력금액) | 139,078 억원 | Insurance_ALM r19 |
| K-ICS required capital (지급여력기준) | 57,770 억원 | Insurance_ALM r20 |
| **K-ICS ratio (지급여력비율)** | **240.74%** (preliminary, 잠정치) | Insurance_ALM r21 |
| CSM opening balance | 111,037.0 억원 | CSM r10 |
| New business CSM (신계약 CSM) | 4,402.5 억원 | CSM r11 |
| CSM interest accretion | 887.5 억원 | CSM r12 |
| CSM experience adjustment | -368.5 억원 | CSM r13 |
| CSM amortization | -3,041.2 억원 | CSM r14 |
| **CSM closing balance** | **112,917.3 억원** | CSM r15 |
| NB CSM multiple (배수, total) | 12.61x | CSM r36 |
| NB CSM multiple (protection only) | 12.68x | CSM r32 |
| Insurance PnL (보험손익) | 3,345.7 억원 | Insurance_Condensed PL r5 |
| Long-term PnL | 3,157.0 억원 | Insurance_Condensed PL r6 |
| Investment PnL (투자손익) | 1,506.4 억원 | Insurance_Condensed PL r12 |
| Operating income | 4,852.0 억원 | Insurance_Condensed PL r15 |
| **Net income** | **4,660.7 억원** | Insurance_Condensed PL r19 |
| General loss ratio | 69.9% | Insurance_Efficiency r11 |
| Auto loss ratio | 82.7% | Insurance_Efficiency r12 |
| Long-term risk loss ratio | 94.28% | Insurance_Efficiency r13 |

K-ICS trend context (from same sheet): 1Q25 238.9% → 4Q25 241.3% → **1Q26 240.7%** —
stable in the 238-243% band since 1Q25.

### Meritz Financial Group consolidated (메리츠금융지주)

| KPI | Value | Source |
|---|---|---|
| Insurance PnL | 1,738.2 억원 | Group highlight r6 |
| Net income | 6,802.3 억원 | Group highlight r21 |
| Net income (controlling) | 6,669.7 억원 | Group highlight r22 |
| **RoE** | **25.37%** | Group highlight r54 |
| BPS | 64,348 원 | Group highlight r55 |
| EPS | 3,926 원 | Group highlight r56 |

RoE basis: numerator = controlling-interest net income; denominator = simple
average of opening + each quarter-end controlling equity.

## Internal taxonomy mapping

| Internal field | JSON path |
|---|---|
| `kics_ratio_pct` (Hwajae) | `meritz_hwajae_standalone.kics.ratio_pct` |
| `csm_total` (Hwajae) | `meritz_hwajae_standalone.csm_movement_eok.closing` |
| `nb_csm_total` (Hwajae) | `meritz_hwajae_standalone.new_business_csm_eok.total` |
| `nb_csm_multiple` (Hwajae) | `meritz_hwajae_standalone.new_business_csm_multiple.total` |
| `insurance_pnl` (Hwajae) | `meritz_hwajae_standalone.pl_ytd_eok.insurance_pnl_eok` |
| `investment_pnl` (Hwajae) | `meritz_hwajae_standalone.pl_ytd_eok.investment_pnl_eok` |
| `net_income` (Hwajae) | `meritz_hwajae_standalone.pl_ytd_eok.net_income_eok` |
| `roe` (Group) | `group_consolidated.ratios.roe` |

NB CSM multiple denominator note: Meritz IR convention publishes the multiple
against 월납월초 (initial monthly premium), aligned with TODO decision #3.

## Gaps / KPIs expected but not present

- **RoE for Meritz Hwajae standalone** — only Meritz Financial Group consolidated
  RoE is in the factsheet (`Group highlight` r54). Hwajae-only RoE not published
  here; would need to be derived externally (Hwajae net income ÷ Hwajae equity
  from `Insurance_Condensed BS`, not done in v1).
- **K-ICS for the Group** — none. K-ICS is solo-entity by regulation; Group
  factsheet only shows Hwajae's number.
- **Operating expense ratio / combined ratio** — not directly published as
  single-line metrics in 1Q26 sheet; derivable from PL + loss ratios.

## Constraints honored

- Did not touch `templates/`, K-ICS pipeline, or IFRS17 code.
- No git operations.
- All file I/O uses explicit `encoding='utf-8'` (Python) per CLAUDE.md rule 5.
- Source page is EUC-KR; openpyxl reads xlsx strings in UTF-8 natively so no
  manual recoding is needed for the data values.

## Reproducing / refreshing

1. Fetch the latest manifest:
   ```
   POST https://m.meritzgroup.com/web/ir1_1_search.do
   data: bd_div_cd=IR011&acrsl_anun_yy=&currentPage=1&Mobile=All
   ```
   Pick the entry with `file_nm` matching `MFG_YYYYMM(k).xlsx`.
2. Download from `https://m.meritzgroup.com/commfiles{file_url}`.
3. Save xlsx to `data/ir/meritz/factsheet_<YYYYMM>.xlsx`.
4. Edit `PERIOD` and `PERIOD_KEY` constants in `extract_meritz_factsheet.py`.
5. Run `python extract_meritz_factsheet.py` from this directory.

If Meritz changes the workbook layout (row indices shift), the extractor's
hard-coded row numbers in each `extract()` block will need to be re-verified
against the new sheet — by design (defensive crawling: parse step is isolated
from extract step per `docs/claude-agent-misc.md`).
