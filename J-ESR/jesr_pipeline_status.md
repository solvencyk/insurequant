# J-ESR Pipeline Status
> Track: J-ESR (Japan Economic Solvency Ratio)
> First J-ICS mandatory disclosure cycle: FY2025 (ending 2026-03-31)
> Last updated: 2026-06-24

## Coverage Summary

| Route | Companies | Status | Trigger |
|---|---|---|---|
| HD press / IR (manual 1st pass) | 7 groups | Partial (5 confirmed 2026.3末, 2 prior-Q) | Complete |
| Mutual IR-PDF (`jesr_mutual_irpdf.py`) | 5 companies | Seed only (prior-Q) | May 2026 press PDFs |
| EDINET XBRL (`jesr_edinet_fetch.py`) | 12 codes known | Scaffold ready, need API key | Oct 2026 |
| Non-EDINET listed subs | ~20 | URL patterns TBD | Oct 2026 |
| Small/foreign subs | ~40 | Not scoped | Oct 2026+ |

**2026-06-24 total confirmed (2026.3末 as-of):** 5 companies (HD only)

## October 2026 Checklist

### Pre-October (now)

- [x] EDINET API probe (auth: 401, key required)
- [x] Master company list `jp_insurers.csv` (生保 41 + 損保 31 + 再保険 2 = 74 entries)
- [x] EDINET fetch scaffold `jesr_edinet_fetch.py`
- [x] Mutual IR-PDF route `jesr_mutual_irpdf.py`
- [ ] **EDINET Subscription-Key registration** (owner: free, 5 min at https://disclosure2.edinet-fsa.go.jp/)
- [ ] Smoke test with key: `python jesr_edinet_fetch.py --key <KEY> --smoke`
- [ ] Verify 12 known EDINET codes with live API (dry-run 有報 search on prior-year docs)
- [ ] Look up TBD EDINET codes for ~20 insurer subsidiaries (bulk company search after key obtained)
- [ ] Update `jp_insurers.csv` with confirmed codes

### October 2026 (after 有報 submission window opens)

有価証券報告書 deadline: **2026-10-31** (最終期限). Most insurers submit June-September.

- [ ] Monitor EDINET daily from **2026-06-01**: `jesr_edinet_fetch.py --all --year 2026`
- [ ] Download XBRL zip for each submitted 有報
- [ ] Extract ESR tags once FSA J-ICS XBRL taxonomy published (check FSA website)
  - Fallback: PDF extraction via LLM if XBRL tags not standardized
- [ ] Download mutual company PDFs when available: `jesr_mutual_irpdf.py --download`
- [ ] Run `jesr_mutual_irpdf.py --extract` for 5 mutual companies
- [ ] Validate all records: `eligible_capital / required_capital * 100 ≈ esr_pct ±2%`
- [ ] Assemble `J-ESR/jesr_master.json` (append to 1st-pass 2026.3末 records)
- [ ] Handoff to parser inbox for `jesr_master.json` schema finalization

## Expected Coverage (Oct 2026)

| Category | Count | Route | Confidence |
|---|---|---|---|
| HD 上場 (連結ESR) | 7 | Already collected | High |
| Listed subsidiaries filing 有報 | ~12 | EDINET XBRL | High (if taxonomy published) |
| Mutual companies (相互会社) | 5 | IR-PDF | Medium (manual update needed) |
| Non-listed KK subsidiaries (大手子会社) | ~20 | EDINET or IR | Medium |
| Small/niche/foreign | ~30 | IR-PDF or N/A | Low |
| **Total (realistic)** | **~44** | | |

Note: 100% individual-company coverage is unlikely before 2027 (some small companies may not
publish stand-alone ESR until full J-ICS reporting culture matures).

## Known EDINET Codes (confirmed)

| Company | EDINET | Category |
|---|---|---|
| 東京海上ホールディングス | E05026 | HD 上場 |
| MS&ADインシュアランスグループHD | E14905 | HD 上場 |
| SOMPOホールディングス | E04979 | HD 上場 |
| 第一生命ホールディングス | E04506 | HD 上場 |
| T&Dホールディングス | E06008 | HD 上場 |
| ソニーフィナンシャルグループ | E33424 | HD 上場 |
| かんぽ生命保険 | E04678 | 上場 |
| 東京海上日動火災保険 | E03823 | 子会社 (社債) |
| 三井住友海上火災保険 | E03824 | 子会社 (社債) |
| 損害保険ジャパン | E03827 | 子会社 (社債) |
| 日新火災海上保険 | E03829 | 子会社 |
| あいおいニッセイ同和損害保険 | E03833 | 子会社 上場 |
| 共栄火災海上保険 | E03850 | 独立 |

## EDINET API Setup (2026-06-24 실측 확인)

```
# 1. Key registered — saved at J-ESR/edinet_key.txt (gitignored)

# 2. Correct base URL: https://disclosure.edinet-fsa.go.jp/api/v2 (disclosure NOT disclosure2)
# 3. Correct header:  Ocp-Apim-Subscription-Key (NOT Subscription-Key)

# 4. Smoke test PASS:
python J-ESR/jesr_edinet_fetch.py --key $(cat J-ESR/edinet_key.txt) --smoke
# -> EDINET status: 200 OK, Documents on 2025-06-19: 600

# 5. FY2024 XBRL structure confirmed (6개사 다운로드):
python J-ESR/jesr_edinet_fetch.py --key $(cat J-ESR/edinet_key.txt) --all --year 2025
# -> E03823 東京海上日動 S100VZU6 ✓
# -> E03824 三井住友海上 S100VZN0 ✓
# -> E03827 損保ジャパン S100W7D2 ✓
# -> E03833 あいおいニッセイ S100VZTI ✓
# -> E03850 共栄火災 S100W78G ✓
# -> E04506 第一生命HD S100W361 ✓
# -> 7社 not_found (HD 7社は2025年6~7月以降提出、または異なる期末月)

# 6. J-ICS ESR tags in FY2024 XBRL: NONE (expected)
#    -> FY2024 有報 = 旧SMR方式のみ. ESR初登場 = FY2025有報(2026年10月提出)
```

## Data Contract Rules (same as Korea pipeline)

- `as_of_consistent`: must be `true` (2026-03-31) for comparison charts
- Records with `as_of_consistent: false` → flagged, shown with date label, not in main ranking
- `esr_pct` plausible range: 80-600% (outside → validation flag)
- Math check: `eligible_capital / required_capital * 100 ≈ esr_pct ±2%` (when both available)
- Missing data → `null` (never imputed)
- Negative values → △ prefix (Korean accounting convention, consistent with KR pipeline)

## Files

| File | Purpose |
|---|---|
| `jp_insurers.csv` | Master company list (EDINET codes, IR URLs, category) |
| `jesr_edinet_fetch.py` | EDINET XBRL fetcher (listed companies) |
| `jesr_mutual_irpdf.py` | Mutual company IR-PDF downloader + extractor |
| `jesr_sources_2026Q1.csv` | 1st pass manual collection (11 HD/group, June 2026) |
| `raw/jesr_sources_raw.json` | 1st pass raw records |
| `raw/edinet/` | XBRL downloads (after key obtained) |
| `raw/mutual/` | Mutual company PDFs |
| `jesr_master.json` | Assembled master (parser output, schema TBD) |
| `probe_edinet.py` | API probe (confirmed auth=401 without key) |
