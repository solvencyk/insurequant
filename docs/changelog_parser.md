# Parser Changelog (Stage 2)

Parser-specific history. Cross-stage entries keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).

Stage prompt: [`docs/agents/claude-agent-parser.md`](agents/claude-agent-parser.md). Domain refs: [`docs/domains/claude-agent-{kics,ifrs17,misc}.md`](domains/).

---

## 2026-05-31 — F17 Tier2 LOB 9/11사 확장 + IR cross-check 3사 (메리츠 ok / 삼성 일반 +246% gap / DB 자동차 sign flip)

Parser side of F17 extended Tier2 LOB extraction from prior 4사 → **9/11 손보사** OK against the reconciliation gate (LOB 보험손익 합 vs Tier1 보험손익 0.5~2x). Decision point flagged in [`TODO_parser.md`](../TODO_parser.md) in-flight box — 3 options pending user (commit 9/11 / debug 삼성·DB / commit IR-clean only).

IR cross-check spot compare (3 cos):
- **메리츠**: matches IR within tolerance — clean
- **삼성화재**: 일반보험 손익 +246% vs IR factsheet — suspect BS rollforward bleed-through into flow analysis table, or factor-unit mismatch on that segment
- **DB**: 자동차 sign flip vs IR — picker chose row where 보험비용 > 보험수익 yet IR shows positive 손익; suspect wrong-row pick or 보험금융수익 contamination

Report: `output/f17_tier2_lob/ir_crosscheck_20260531.md`.

Taxonomy correction documented in TODO_parser.md (top): 손보 CSM decomposition is 보장성/물보험/저축성 (within 장기), 손보 P&L decomposition is 장기/자동차/일반. 자동차·일반 = PAA → CSM 없음. 보종별 신계약 CSM multiple은 IR 공시 회사 한정.

---

## 2026-05-30 (b) — F17 Tier2 LOB 보종별 파싱 방법론 수정 (사용자 반례: FY2024·삼성화재도 분해 있음)

사용자 반례 — 삼성화재 FY2025 '26. 보험서비스결과 / 발행보험의 보험수익 분석'에 **장기보험 수익 10,024,617(백만)** 명시. 현대 FY2024도 '27. 전환방법에 따른…' note에 장기 7,481,394,159. 직전 'FY2024 LOB 없음 / 삼성화재 taxonomy 다름' 진단 **철회** (또 성급한 source-limited 오판 — `<TE>` 때와 동일 교훈).

**근본 수정 (`scripts/build_net_income_breakdown.py`):**
- **컬럼 식별 position-based**: 헤더 '계약의 유형' 병합 super-header 탓에 헤더-인덱스가 데이터컬럼과 어긋남 (삼성화재 장기 칸에 자동차값 들어옴). → 행의 numeric cell **위치**(0/1/2=장기/자동차/일반)로 추출
- **rollforward 표 제외**: 보험계약부채 변동표 (기초/기말) 도 보험수익/비용 행을 갖지만 BS 규모 → 제외하고 클린 flow 분석표만
- **보험수익(LOB) = max(정확 '보험수익' 합계행, '보험수익,' 컴포넌트 합)**: 삼성화재=합계행, 현대 장기=GMM 컴포넌트 합 / 자동차·일반=PAA 단일행 — 둘 다 처리
- **단위 factor = Tier1 보험손익 anchor**: note가 원/백만/천원 혼재 → Σ(rev−cost)이 Tier1 보험손익에 맞는 factor 선택 (삼성화재 백만, 현대 원 등 자동)
- **Tier1 연결 우선**: 일관성 통과 후보 중 **최대 당기순이익** (연결 ≥ 별도) 선택 → LOB note (연결 공시) 와 정합. 현대 별도 3,961 → **연결 10,431** 로 정정 (순이익 10,433억 ≈ 1.04조)

**결과 — Tier2 보종별 LOB 4사 검증완료** (reconciliation gate 통과, 억원): 삼성화재 장기 16,651 / 자동차 −1,220 / 일반 5,917 · 현대 장기 4,097 / 자동차 −677 / 일반 6,613 · DB 장기 12,257 / 자동차 6,811 / 일반 −26 · 한화손보 장기 4,171 / 자동차 −966 / 일반 −735. (직전 1사 → 4사.) 이후 2026-05-31 세션에서 9/11 로 확장 (위 entry).

**남은 갭 (정직)**:
- 흥국화재 — LOB 표 파서 미스 (gate로 제외, 소형사)
- KB · 메리츠 · NH농협 — FY2025 사업보고서가 FS를 **별첨 감사보고서**로 분리 → document.xml API 본문에 LOB 없음 (attachment fetch 필요)
- 롯데 = 표 없음, 코리안리 = 재보험 N/A
- **FY2024 LOB은 사업보고서에 존재** (감사보고서 아님) — 현 ifrs17 ingest는 FY2024 감사보고서라 LOB 없음, FY2024 LOB 원하면 사업보고서 (예 현대 rcp 20250407001731) fetch

Tier1 (보험손익 / 투자손익 / 당기순이익) 은 10사 전부 OK 유지. Panel 3 caption 에 보종별 표시, 브라우저 재검증 OK (콘솔 에러 0).

---

## 2026-05-30 — F17 손보 당기순이익 분해 (보험손익 / 투자손익) — Tier1 10사 + Tier2 1사 (현대 검증완료)

(폴더 리네임 `data/ifrs17` → `data/dart` 는 cross-stage 정리 — root [`docs/claude-changelog.md`](claude-changelog.md) 참조.)

신규 `scripts/build_net_income_breakdown.py` → `data/dart/viz/net_income_breakdown.json`. 표 파싱은 `csm_extractor._iter_tables_with_context` 재사용.

**Tier1 (포괄손익계산서, 전사 OK 10/10)**: 보험손익 / 투자손익 / 보험금융수익·비용 / 영업이익 / 영업외 / 당기순이익. 단위는 **매그니튜드 자동추론** (IS가 회사별로 원 또는 백만 — 삼성화재 = 원, DB 등 = 백만/천원 → 당기순이익이 5 ~ 120,000억에 들도록 factor 선택). 표 선택은 일관성 (보험손익 + 투자손익 ≈ 영업이익) + 자릿수 concatenation guard (>16자리 거부) + all-zero/blank 거부. FY2025 사업보고서 우선, thin 사는 FY2024 fallback.

예: 삼성화재 보험손익 14,830 / 투자손익 11,761 / 순이익 20,203, DB 11,454 / 12,386 / 17,906, 메리츠 14,270 / 8,595 / 16,929.

**Tier2 (보종별 보험손익 장기 / 자동차 / 일반, FY2025 보험서비스결과 note)**: **현대해상 검증완료** — 장기 보험수익 80,684 / 비용 76,397 / 보험손익 4,097 / CSM상각 9,639억. 나머지는 reconciliation gate (LOB 보험손익 합 vs Tier1 보험손익 0.5~2x) 로 제외 — 오값 방지. 이후 2026-05-30 (b) 에서 4사, 2026-05-31 세션에서 9/11 사로 확장.

---

## 2026-05-30 — IR factsheet 전사 수집 + 손보 disclosed/derived NB CSM 배수 파싱

User: "받아둔 현대·DB·한화손보 raw 파싱해서 disclosed 더 채우기" + 삼성화재 IR 사이트/xpath 제공.

**삼성화재 (KR0008) — 직접 disclosed 배수 확보 (13Q).** 공식 IR (VH.HPMK0201.do) factsheet 13개 분기 (FY2023_Q1 ~ FY2026_Q1) 다운로드. factsheet `CSM` 시트가 **신계약 CSM 배수 합계를 직접 공시** (분기 standalone): 2023 15.2/17.2/22.2/19.3, 2024 15.2/14.5/15.5/15.4, 2025 11.9/13.7/14.9/14.0, 2026.1Q 14.08. `신계약 CSM 합계` (분기) 의 cumsum 이 DART/KIDI 분자와 **정확히 일치** (2023 cumsum 6782.7 / 14426 / 26067.9 / 34995.3). `scripts/parse_ir_samsung_fire.py` 작성 — disclosed (단분기) + derived_ytd (= cumYTD CSM / cumYTD 월납환산 x3) 둘 다 기록. derived_ytd 가 KIDI 와 근접 (2024.1Q 15.18 vs KIDI 14.83, 2025.1Q 11.85 vs 11.54). xlsx 의 malformed docProps/custom.xml 은 zip strip 으로 우회.

**DB손해보험 (KR0011) — derived 배수 (13Q).** IR 이 배수를 직접 공시하진 않지만 components 보유: `BEL,CSM변동` 시트 `신계약 유입` (분기, 백만원) + `신규월납` 시트 `월납신규` + `비월납` (월별, 억원). `scripts/parse_ir_db_derived.py` 작성 — multiple = cumYTD (신계약 CSM) / cumYTD (월납신규 + 비월납). 결과 15 ~ 17x. **분자가 KIDI 와 정확 일치** (24.1Q 7175.2, 24.4Q cumsum 30780.4), **분모도 KIDI 월납초회 + 기타초회 와 근접** (24.1Q 469.9 vs 467.7, 24.2Q 886.6 vs 882.6) → 손보 ~16x 가 **두 독립 소스에서 동시 검증됨** (에러 아님, 고마진 장기 보장성 특성).

**한화손해보험 (KR0002) — DART 분자 ~2 배 과대 발견 (배수 미산출).** IR 실적발표 PDF 내러티브 (CSM 변동원인 "신계약 ...억") 만 보유, 월납환산 미공시 → IR 단독 배수 산출 불가. 추출한 IR YTD 신계약 CSM = FY2024 7,410 / 2025.1Q 1,891 / 1H 4,510 / 9M 7,351 억. **DART/KIDI 분자는 FY2024 14,819.8 (약 2.0 배), 2025.1Q 3,971.5 (2024.1Q 와 동일 = stale carryover)** → KIDI 한화손보 배수가 ~20-22x 로 비현실적 (사용자 기대 <20, ~10-15). 2025.2Q DART (5,119) 는 IR 1H (4,510) 와 근접 → 과대계상은 2023-2024 + 2025.1Q 에 집중. `data/ir/series/KR0002_한화손해보험.json` 에 IR vs DART 비교 + flag 기록.

**현대해상 (KR0009).** 2025.1Q factsheet 에만 `(7) ETC` 신계약 CSM 시트 존재. KIDI 분자가 이미 정확 일치 (24.1Q 4,114.6 억) 하므로 단일포인트 외 series 미작성.

**집계 (`scripts/build_ir_disclosed_multiples.py`).** DISCLOSED_KEYS 에 multiple_disclosed, DERIVED_KEYS 에 multiple_derived_ytd / multiple_derived 추가 + derived_ytd / premium passthrough. `data/ir/disclosed_csm_multiple.json` = **9사** (배수 보유 6: 메리츠13 / 롯데9 / 삼성화재13 / DB13 / 한화생명13 / 삼성생명12, 미보유 3: 한화손보 [flag] / 미래에셋 / 코리안리).

**교차검증.** 회사마다 배수 **공시 기준이 제각각** (삼성생명 = 월평균월초, 메리츠 = 월납환산, 한화생명 = APE 류, 삼성화재 = 단분기 월납환산 x3). 단일 일관기준 (월납초회 [+기타초회 손보]) 의 KIDI computed 가 **회사 간 버블 비교에 적합**하고 삼성생명 (±10%, 일부 0%) / 삼성화재·DB·현대 (분자 정확일치) 로 검증됨. disclosed 는 회사별 참고치로 병기. 미해결: 한화생명 +40% (APE 기준차), 한화손보 분자 버그.

---

## 2026-05-29 — 삼성생명·미래에셋 합계-vs-CSM 컬럼 식별 + 상품군 분리공시 합산 (FY anchor 정정)

User: "삼성생명/미래에셋 합계-vs-보험계약마진 컬럼 식별을 더 파고든 다음 커밋." 이전 세션의 `<TE>` 복구 후에도 삼성/미래 다수 분기가 no_csm_block 으로 남았던 진짜 원인 두 가지를 규명·수정.

**근본 원인 1 — 상품군 분리공시 (per-product split).** 삼성생명·미래에셋은 측정요소 변동표를 **상품군별 별도 표** (사망 / 건강 / 연금 / 저축 / 기타) 로 쪼개 공시. 기존 picker 는 그중 **한 상품 (사망)** 만 집어 회사 전체로 착각 → 삼성 FY 마감 CSM 이 **4.9조 (사망 1개 상품, 게다가 전기값)** 로 나옴. 진짜 전체 = 3개 상품 합 **13.08조** (공개치와 일치).

**근본 원인 2 — 합계(소계) 컬럼 이중계상.** `find_csm_leaf_cols` 의 압축 헤더 분기가 `[2,3,4,5]` (전환방법 3개 + **소계**) 를 모두 더해 CSM 을 **2 배** 계상. 미래에셋 사망 0.79조 가 1.57조 로, 동양생명 2.54조 가 5.08조 로 뻥튀기돼 있었음.

**수정 (`viz_build_csm_waterfall.py`):**
- `find_product_segmented_csm_cols`: 상품 P 개가 옆으로 나열된 **wide 표** (2025+ 분기 `<TE>` 표: 삼성 3×6, 미래 5×5) 에서 상품별 CSM 컬럼 전부 식별, 그룹별 합계열은 per-product 합계 불변식으로 탐지·제외 → 2025+ 분기 복구
- 압축 분기: sub2 의 `소계` / `합계` 라벨 컬럼 제외로 이중계상 제거 (`[2,3,4,5]` → `[2,3,4]`) → 동양·미래 단일상품 정정
- `collect_current_product_blocks` + `extract_stages_summed`: 상품군 분리공시를 **합산**. 안전 게이트 7개 — (a) 좁은 단일상품 블록만, (b) 동일 leaf 레이아웃 최빈군, (c) **전기** 캡션 제외, (d) ≥3 개 상품, (e) 마감액 near-uniform 거부 (연결/별도/기간 변형), (f) product#1 재시작 감지로 cycle 종료, (g) 한 블록이 나머지 합이면 거부
- `build_for_file` (FY): 분리공시면 합산. `build_one_period` (history): 합산은 **FY anchor 정합 fallback** 으로만 (단일픽이 anchor 에서 >45% 벗어나고 합산이 ≤35% 일 때만) → 한화·KB·신한 등 segment 분리 회사 오합산 방지

**결과:** FY anchor 정정 — **삼성 13.08조 / 미래 2.08조 / 동양 2.54조** (모두 공개치·인접분기와 정합). History: 삼성 **12/13**, 미래 10/13 (8 ok + 2 partial), 동양 8/13 복구. **비대상 28사 FY·history 회귀 0건**, ok 셀 258 (기준선과 동일하나 값 정정).

잔여 갭 (삼성 2023.1Q, 미래 2023.1·3Q / 2026.1Q, 동양 2025.2Q ~) 은 정직한 갭 — 동양 2025.2Q+ 는 컬럼식별이 아니라 **추출단계 잔액행이 0** 으로 들어온 별개 이슈 (F15-DL downloader 측 재다운로드 후보).

---

## 2026-05-29 — CSM 시계열 결측 진짜 원인: `<TE>` 데이터셀 미파싱 (이전 "원본에 없음" 진단 철회)

User pushed back with a concrete counter-example: 한화생명 2025.3Q DART 공시에 '(3) 최초 인식한 계약의 효과' 보험계약마진 **2,228,273** 이 분명히 있다 → "source import 문제"일 것. **User was right; my earlier "source-limited" conclusion was wrong** (I'd checked only 2025.2Q and extrapolated).

**Root cause = `<TE>` cells.** DART's 2025+ filings render table data cells as `<TE>` (table entry), not `<TD>`. `csm_extractor._iter_tables_with_context` only collected `<th>`/`<td>`, so every body row parsed **empty** (header captured, rows blank) → no_csm_block. The batch HAD fetched the right document (한화 2025.3Q rcept 20251113000814, 19MB). Fix: recognize `<te>` as a data cell.

**Audit of all non-ok periods** (raw-XML signature scan): **HAS_DATA (parser missed real rollforward) 34**, NO_FILE 5, genuinely-condensed (요약 반기) **only 1** (한화 2025.2Q). So nearly all gaps were parser failures, not missing data.

**Second bug surfaced by the recovery: `find_csm_leaf_cols`.** These tables use a **6-row multi-level header** with the leaf column labels (미래현금흐름 / 위험조정 / 보험계약마진 / 합계) in the last header row; the function only inspected rows 0-2 → returned `[]` → block still rejected. Added a fallback that scans all header rows and maps 보험계약마진 to its value-column index.

**Picker hardening on the now-richer consolidated filings:**
- Exclude consolidation tables (관계기업 / 종속기업 / 요약재무정보 / 지분의 장부금액) — they mention 보험계약마진 but aren't the insurer's CSM rollforward (was mis-picking 미래에셋 2025.4Q 5.43조 equity table)
- History builder: reject a pick whose opening is still >40% off the prior close → emit an honest gap instead of a misleading number (한화 2025.2Q condensed, 롯데 2025.4Q tiny, 미래에셋 spurious)

**Diversified label patterns.** 한화 2025.2Q ALSO had NB CSM — '해당 기간에 처음 인식한 계약의 영향에 따른 증가분(감소분)' = **1,378,511** — which I'd missed because my audit signature used '최초 인식' not '처음 인식'. The extractor's STAGE_PATTERNS already handle '처음 인식'; the real miss was the **picker** not selecting the total block among the segment sub-tables.

**Two more picker fixes:**
- Continuity searches **ALL** candidates (not top-5): the total often ranks below segments but its opening matches the prior close (한화 2025.2Q total 13.07조 vs segment 4.16조). Recovered 한화 2025.2Q (NB 1,378,511)
- **FY-anchor regime correction** (history builder): the pick's closing must sit within 45% of the company's FY total (`csm_waterfall.json`); if it's off, take the nearest anchor-consistent (≤35%) candidate, else emit an honest gap. Fixes systematic segment-vs-total mis-picks (교보생명 ~5조 segment vs 11.75조 total → now ~11-13조). `main()` builds each company chronologically, threading prior-close + FY anchor

**Result (re-promote from cached raw, no re-fetch):** ok 258 / no_csm 29 / partial 6 (was 257/34 with *wrong* "ok" values); **outlier scan = 0**; **FY 28-co waterfall 0 regressions**. Recovered with correct values: 한화 all 13Q (NB 2025.2Q 1,378,511 / 2025.3Q 2,228,273), 교보 all quarters, 삼성화재 2025.2Q/3Q, 현대해상, 케이디비, 코리안리.

---

## 2026-05-29 — Panel 5 sensitivity rowspan fix + 한화 2023.4Q dip

User flagged ΔCSM sensitivity table mis-aligned ("3.27% 감소" in the 위험요인 column) and the 2023.4Q CSM dip.

**Panel 5 sensitivity — rowspan + header-aware parse (`viz_build_ifrs17_panels.py`).** The risk name spans the 증가/감소 row pair via HTML rowspan, so the 감소 row has one fewer leading cell → every column shifted left (the user's exact symptom). Added `_band_sensitivity_columns` (header-aware: finds the 변동금액 보험계약마진 / 당기손익 value columns, preferring 원수; uses the LAST CSM column so 교보's 기준금액 + 변동금액 layout maps to 변동; strips label cells like 케이디비's 위험변수 / 변동; accepts 보험서비스마진 K-ICS term) + `_extract_sensitivity_band` (detects rowspan-elided continuation rows and inherits the risk). Routed only when that band header is present, so product-line path (삼성, unchanged) and generic path are untouched. **Fixed: 한화 (사망률 증가 ΔCSM −256,319 / 손익 +80,535; 감소 +262,227 / −84,260), 교보, 케이디비 (−57,369 / −308,997), DB생명.** 삼성생명 verified unchanged.

**Remaining: 흥국생명** — different layout (products-as-rows × 당기말/전기말 with 'CSM' / '손익 효과' headers); needs its own path → F16 follow-up.

**한화 2023.4Q dip (9.24조 → 13.30조).** FY2023 report has two near-identical "(5) 측정 요소별 변동" rollforwards: a 13.30조 total and a 9.24조 subset; `pick_main_block` chose the subset because its caption kept the 당기 marker (period_affinity 35 vs 0). Fix: exposed `rank_main_blocks` and added a **guarded continuity tiebreak** in the history builder — when the default pick's opening deviates >25% from the prior period's closing AND another top candidate opens within **5%**, prefer continuity. `main()` now builds each company's periods chronologically, threading the prior closing. The 5% guard fixes 한화 + several clearly-broken tiny values (롯데 2025.4Q 0.03→4.92조, 메리츠 2026.1Q 0.05→11.1조, 신한 14.7조, 케비 3.4조, 미래에셋) **without** touching ambiguous mid-range picks (삼성생명 stays 4.906). FY waterfall **0 regressions**; outlier scan now **0**.

---

## 2026-05-29 — NB CSM multiple Samsung 사망 misparse fix (parser side)

User flagged 삼성생명 종신/사망 NB CSM multiple >400x (impossible).

**400x = regex misparse [fixed].** `viz_build_nb_csm_ratio.extract_samsung_life` read the death row with a positional 5-number regex; the IR PDF text interleaves the death *multiples* (single digits) with absolute CSM amounts (십억원: 459/435/520/471/488) on adjacent lines, so it grabbed 520/471/488 for FY24.1-3Q. **Fix:** scan the region between the 건강 row and the (last) 사망 label, keep only `\d+\.\d+` values < cap → death now [7.6, 10.0, 7.6, 7.2, 5.1]. (`rfind("사망")` — the first 사망 is the column header 건강 사망 금융.)

**Plausibility gate** (validation rule, MAX_PLAUSIBLE_MULTIPLE = 60.0) — see [`docs/changelog_validation.md`](changelog_validation.md) 2026-05-29 for the validation half.

---

## 2026-05-29 — CSM 시계열 (Panel 6) prior-period de-contamination + per-quarter new-business

User asked why 한화생명's CSM time series stops at 2025.1Q and flagged the new-business sawtooth. Investigation: not staleness — three separate issues, two parser-side.

1. **Prior-period contamination [real picker bug].** `pick_main_block._period_affinity` penalized `전기` but **not `전분기` / `전반기`**, so 분기/반기 reports' prior-period column was chosen. 한화 "2025.1Q" closing was literally 2024.1Q's value (13,362,336). Across 23 insurers, 13-17 quarterly points per period were prior-period dupes. **Fix:** added `전분기` / `전반기` penalty (−22) + `당분기` / `당반기` bonus (+22), guarded so a combined "당분기 및 전분기" caption stays current. Re-ran `viz_build_csm_waterfall_history.py` (reuses the picker on cached extracts — **no re-fetch**). Result: **prior-period contamination 0 across all periods**; 한화 2025.1Q now 12,994,325 (caption "1) 당분기"). FY28 current-panel waterfall verified **zero regression**.
2. **FY2025 (2025.4Q) was always present** (20/23 ok) — it just rendered as an isolated dot because 2025.2Q/3Q are null (line break). Not a data gap.
3. **2025.2Q/3Q/2026.1Q gaps** (~11/23 no_csm_block): genuine — 반기/분기보고서 often lack a parseable rollforward (2026.1Q reports defer to the audit report). Captured in F15.

**New-business → per-quarter increment.** New-business CSM is disclosed fiscal-YTD cumulative → within-year sawtooth. `viz_build_csm_waterfall_history.add_nb_increments` now emits `new_business_increment_mn_krw` (+ `_span_q`): flow since the previous available quarter in the same FY, chain persisting across an unobserved quarter. IFRS17.html Panel 6 plots the increment for the pink line; tooltip flags multi-quarter spans. Verified for 한화: ~0.7-1.1조/quarter (no sawtooth); 2025.4Q dot = 2.42조 (span 3Q, flagged).

---

## 2026-05-29 — F11 waterfall-builder 3 safe fixes (parser-adjacent, foreign-affiliate life)

Cross-stage F11 done is in root [`docs/claude-changelog.md`](claude-changelog.md). Parser-side fixes (`viz_build_csm_waterfall.py`), each zero-regression vs snapshot of the 23:
1. Magnitude unit fallback now keyed on the **largest-magnitude stage**, not opening — these insurers report in **천원** and some split the 기초 row so opening matched a zero placeholder (메트 / AIA / 하나 scale)
2. `pick_main_block`: **direct block always outranks ceded** (new top sort key). 처브라이프 `<당기>`-tagged 재보험계약부채 block had been beating its direct 보험계약부채 block → fixed (closing 1,124억, was negative/wrong)
3. Closing label `보고기간말` added + a **guarded** net-row patch: when opening/closing resolves to ~0 (rowspan-split 자산/부채/순부채 balance, e.g. 하나생명), pull the 보험계약순부채 net row's CSM. Guard (only fires on ~0) keeps the 23 untouched. 하나 fixed: open 3,016억 / close 4,390억

Final waterfall status for the 5: 메트라이프 / AIA / 처브라이프 / 하나생명 **ok**; 라이나생명 **partial** (rollforward has no matched amort row; Panel 2 amort schedule is clean from csm.json).

---

## 2026-05-25 — IFRS17 historical 13Q ingest pipeline (parser side)

User asked to expand IFRS17 from FY2024 annual only to all quarters 2023.1Q ~ 2026.1Q.

**Stage 2 of 3 — Promote to measurement (`scripts/ifrs17_promote_history_to_measurement.py`):**
- Runs `src.ifrs17.measurement_extractor.extract_measurement_tables` per (canonical, period) XML dir
- 294 targets → 293 ok (single 1 with no_measurement_tables). Cache when ≥64 bytes
- Output `_measurement.json` matches the picker schema in `viz_build_csm_waterfall.py` (block_type / slice_label / mvp_candidate)

(Stage 1 fetch = downloader; Stage 3 viz aggregate = gathering. See respective changelogs.)

Coverage at this push: 20 → **257 ok + 2 partial** out of 299 reachable after the promote step. 사업보고서 (FY): near 23/23. 2025.2Q ~ 2026.1Q had 11-13 no_csm_block each (분기보고서 often text-only) — later improved to 258 ok with the 2026-05-29 `<TE>` fix.

---

## 2026-05-25 — IFRS17 B5 K-ICS sensitivity: appendix headings + multi-period batch

- `src/ifrs17/kics_sensitivity_extractor.py`: section starts also recognize markdown titles that contain both `보험위험` and `민감도` (appendix wording without the contiguous `가정민감도` token); compact-line match for spaced `가정` / `민감도`; bullet `- (5)` only when assumption-sensitivity wording matches. Default `min_score` lowered to **3** so IFRS LIC/CSM grids that land at score 3 after the +2 K-ICS bump are emitted (fixes e.g. 미래에셋 변형 표 헤더 cases). Solvency-only `6-8` blocks unchanged.
- `scripts/ifrs17_batch_kics_sensitivity.py`: `--all-periods` runs every `md_inbox/FYyyyy_Qn` directory; `--manifest-period` selects the `crawl_manifest.json` period (default last sorted). JSON output includes `tables_grand_total_across_periods`.
- Latest full run (12 quarter folders on disk): **49** tables extracted across all periods; FY2025_Q4 **11** insurers with >=1 table (**23** tables) vs legacy headings + `min_score=4` baseline **10** / **19**. KR0073 / KR0069 still empty: FY2025_Q4 MD lacks IFRS 가정 민감도 grid in the keyword parse window (upstream MD scope), not fixable by regex alone.

---

## Historical archive (compressed, parser-scoped)

### 2026-05-25 mid-session (parser items)
- NB CSM ratio prototype: artifact `_read()` UTF-8 → cp949 fallback (KB fix), Samsung Life multiline 금융 layout
- IFRS17 B3 row tagging: `src/ifrs17/row_normalizer.py` + `row_aliases.yaml`; 5 source files, 2956 rows scanned, 930 canonical hits
- IFRS17 B5 K-ICS sensitivity ingest v1: `kics_sensitivity_extractor.py` + `ifrs17_batch_kics_sensitivity.py`; FY2025_Q4 10/23 insurers, 19 tables
- CSM waterfall stage patterns: extended STAGE_PATTERNS; **23/23 ok**, 0 no_csm at that point
- IFRS17 CSM Waterfall picker: 5 no_csm 손보사 → 0 (MVP filter off, ceded penalty, header-in-rows hoist). 23/23 coverage
- Unit-hint mismatch auto-detect: 23 insurer-quarter latent bugs (3× ×100 + 20× ÷100), 56 post values corrected

### 2026-05-25 K-ICS RED reduction (parser fixes that drove the cumulative reduction)
- Rule 2 fixes (KR1098 / KR0051 / KR1010 / KR0095): KakaoPay / MetLife reversed capital labels, item4 reconcile, item10 baseline; `_canonicalize_table_label`, MetLife alias, `labels_compatible` guard
- 8_life item35 parser fix (KR0009 / KR0095 / KR1098 / KR0051 / KR0049): multi-line unit hint, life-only 총계, default 백만원 for life catastrophe tables
- Shinhan Life (KR0094) 2024.4Q rule 6 fix: drop bare `분산효과` alias; only top-level item16 labels
- Rule 5 missing item22 (KR1010 / KR1098 / KR0051): recalc infers item22 = 0; OCR-spaced label match
- Samsung Life (KR0069) 2023.1Q / 3Q parse: bullet section start patterns
- DB손해 (KR0011) 8_life: keep first 위험액 block (sub-item overwrite fix)

### 2026-05-24 KICS parser progression
- K-ICS RED per-rule samples @177
- KR0097 Hana Life parse fix (RED 18→2)
- K-ICS missing-data reparse + item27/28 recalc fix (RED 311→217)
- K-ICS validation RED fix pass 2 (user ground truth, RED 419→311)
- KICS-REPARSE-Q4 FY2025_Q4 refresh: parse 30/38 ok, fill_period upd = 30
- K-ICS RED troubleshooting (user-verified cases)
- K-ICS full reparse, validate, JSON swap (all periods)
- K-ICS parser: split-table continuation + row scope (KR0005 FY2025_Q4 golden test)

### 2026-05-24 IFRS17 parser bootstrap
- IFRS17 CSM 추출기 강화 + 37사 일괄 자동 추출 (23/37 ok)
- IFRS17 MVP tiers A3 / A4 / B1 / B5 (skim extractors + 23-co batch)
- A1 gap 3사 (KB손해 / 코리안리 / 한화손해) MVP 슬라이스 fix
- A1 23사 batch
- K-ICS 경과조치 적용 후 값 (`값_적용후`) + KR0076 보조지표 fix
- IFRS17 sensitivity heatmap table load fix

### 2026-04-25 ~ 04-28 Pipeline foundation (parser side)
- Docling 파이프라인 도입 (PDF → MD inbox)
- NONLIFE / LIFE 협회 단위 파서 1차
- FY2025_Q4 PDF → Markdown → kics_data.json 플랜 완료
- FY2025_Q4 → kics_disclosure.json 직접 채우기 (749 rows)
- 과거 분기 PDF 배치 검증 + 누락 비율 (27/28) 자동 산출
