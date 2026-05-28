# Insurequant TODO

Last updated: 2026-05-26 (F2 v3 + F6 amort yearly granularity queued; F4 KB라이프 정정)

## 🚧 Follow-ups (next session — 병렬 sub-agent 대상)

| # | Task | Scope | Notes |
|---|------|-------|-------|
| ~~F1~~ | ~~index.html → IFRS17 cross-nav~~ | done | `fcdd544`. ECharts on('click') → URL param + auto-select |
| F2 v3 | **NB CSM 배수 — segment-match KIDI crawler** | **scope 재정의 2026-05-26**: 신계약CSM 분자가 상품군별로 분리 가능하면 (건강/저축 등) → 같은 segment 월납환산 초회보험료를 분모로. 분리 불가면 **보장성보험 (투자계약 제외) 초회보험료 (월납환산)** 만 사용 (손보·생보 둘 다). IR 자료 있는 6사는 산출값 vs IR값 비교 검증. | KIDI endpoint 확인 완료: `POST /insMonth/getQueryResult.do queryId=getM{XX}List`. 손보 N07 row LINE=99113 = 보장성보험 합계 (개인 + 단체). 생보는 070104 ML04List (종목별 I — 보장 분리됨) 확인 필요. ITEM_VAL 컬럼 의미 매핑은 KIDI 웹 UI 시각 cross-check 필요 (한화 메리츠 작은 N월 값 vs 큰 N월값 패턴 보고). 다음 세션 액션: (a) 070104 schema probe + 보장성 row 식별 (b) 손보 99113 row 사용 검증 (c) 생보 CSM이 segment 분리되는지 확인 — 한화/삼성 IR PDF 참조 (d) crawler 작성 (e) 6 IR-cohort 산출값 vs IR값 cross-check |
| ~~F3~~ | ~~CSM 상각 schedule 전수 조사~~ | done | `4b06492`. 19/24 → **22/24 ok**. 메리츠화재 4-bucket 정상 렌더. 헤더 패턴 (1년미만/30년이상/이하/초과 등) + transposed table + 합계 derive + reinsurance downrank. 2 source-level 한계 (서울보증 PAA, 한화손해 csm.json만) |
| F4 v2 | **Forward Outlook confidence — Cat C/D 리서치 + 외국계 분류 helper** | scope 좁힘 (cat E 정상 제외 / cat F 코드 fix 완료) | F4 v2 report: `output/kics_forward_capital/confidence_low_rootcause_v2_20260525T145147Z.md`. **Cat B drill-down 결과**: 11사 (10 아님) — KR0069 삼성생명 BS T2 66,289억 (FSC alias 최대 gap), KR0008 삼성화재 4,097억, KR1000 코리안리 4,431억 = alias 해결 시 75,000억 격차 해소. **Cat C/D 리서치 필요**: BS 자본성증권 carrying value 정의 (FV vs amortized) + Call exercise 시 차감 메커니즘. 답 나오면 over/under_deduct 의미 재정의. **외국계 분류 helper** 코드 추가 권고: `bond_coverage="no_self_issued, parent_capital"` 등 |
| ~~F5~~ | ~~No-bond insurer forward sim 추가~~ | done | `b02e24d`. 24 → 37 cohort. KR0008 삼성화재 263%→263% flat. 13 no_bond insurer 추가. F4 추가 fix (`<1.0` 임계): KR1010 교보라이프 low→high |
| ~~F6~~ | ~~CSM 상각 schedule yearly granularity~~ | **done 2026-05-28** | `extract_amort_schedule`에 `yearly`(y1..y10+y10plus+total)+`granularity` 추가, 기존 4-bucket `buckets`는 유지(keep-both — kpis/bubble 호환). granularity>=7yr=yearly. **16 yearly / 6 coarse / 2 no-data**. IFRS17.html panel 2 = 데스크톱 10년/모바일 5년 막대(matchMedia 640px), coarse사는 4-bucket 폴백. Chart.getChart 검증 OK. |

## 🆕 신규 공공데이터 소스 follow-ups (2026-05-26 Gemini 컨설팅)

자본성증권 ingest (FSC) 패턴이 효과적이었음 → 동일 방식으로 추가 공공데이터 소스 발굴.

| # | Task | Priority | Notes |
|---|------|----------|-------|
| F7 | **KOSIS 손보사별 손해율 시계열 ingest** | 🔴 P1 | 출처: 국가통계포털 KOSIS `orgId=382, tblId=TX_38202_A1561`. JSON API 공개 → 자동화 쉬움. 손해보험사별 원수보험료/보유보험료/경과손해율 (개별사 × 분기/연간). 현재 손해율은 PDF/HTML 파싱 기반 → KOSIS 교차검증으로 품질 보완. 손해율 트렌드 경쟁사 비교 차트 가능. **액션**: `scripts/ingest_kosis_loss_ratio.py` 신규 + `data/kosis/<stamp>/` |
| F8 | **손보협회 비교공시 (consumer.knia.or.kr) — GA 인사이트** | 🔴 P1 | 핵심 항목: (a) **채널별 불완전판매비율** (GA/직판/방카 구분) — GA 역선택 리스크 대리지표 (b) **설계사정착률** — 판매채널 품질 선행지표 (c) **민원발생현황** — 미래 해지/청구 선행지표 (d) **보험금 부지급률** — 언더라이팅 공격성 지표 (e) **보험금 지급지연율** — 보조지표. 삼성화재 리포트 "GA 채널 비중이 역선택 선행지표" → GA 불완전판매비율은 그 다음 단계 확인 지표. **액션**: 사이트 구조 probe (JS-rendered 가능성 점검) → API 또는 scrape 결정 → `data/knia_consumer/` |
| F9 | **data.go.kr 금융통계 API 추가 연동** | 🟠 P2 | 이미 자본성증권 (15059611) 연동 패턴 있음. 추가: (a) `15061307` 금융통계손해보험정보 — 손보사 주요 경영지표 (손해율·사업비율·합산비율, 영업활동) (b) `15061306` 금융통계생명보험정보 — 동일 구조 생보판 (c) `15094797` 실손보험정보 — 유형별/성별 보험료 추이. 경영공시 스크래핑 대신 공식 API → 데이터 품질·업데이트 주기 안정. **액션**: `src/bonds/fsc_client.py` 패턴 재활용해서 `src/finstat/` 신규 모듈 작성 |
| F10 | **GA 통합공시 (gapub.insure.or.kr)** | 🟠 P3 | GA별 불완전판매비율/계약건수/모집실적. 특정 보험사의 GA 의존도를 GA 측 데이터로 역산 가능. 삼성화재 26.1Q GA 비중 48.9%를 cross-check. **액션**: 사이트 구조 probe → scrape 가능성 확인 |

**전략적 시너지 (코리안리 리포트 인과 체인 재현):**
- F8 (설계사정착률) + F8 (채널별 불완전판매비율) + 37회차 해지율 (별도 source)
- = "GA 채널 → 해지율 → 손해율" 인과 체인을 공시 데이터만으로 재현
- → insurequant 프리미엄 기능 후보



## 🎨 Mobile & visual follow-ups (2026-05-28)

Shipped & deployed: index.html M1 (responsive @media foundation on all 4 pages) + M2 (treemap → vertical list on phones, sorted by 지급여력기준금액 desc) + desktop treemap label cleanup (dropped redundant 기준금액 text, size-aware labels) + debug console.log cleanup.

| ID | Task | Status | Notes |
|----|------|--------|-------|
| MOB-KICS | K-ICS.html full mobile layout | deferred | M1 foundation only (header/tabs/table scroll, chart heights ↓). Full pass — donuts stacked vertically, forward-chart legend reposition, dense table → card view — **deferred until panel content/scope agreed.** |
| MOB-IFRS17 | IFRS17.html full mobile layout | deferred | Same — M1 foundation only. Defer full pass until display-metric scope agreed. |
| VIS-DONUT | K-ICS donut row stacks on phones | todo | `.donut-cell` cramped <400px; stack vertically. |
| VIS-CHARTLEGEND | chart legend/axis density on mobile | todo | Chart.js legends overflow narrow widths; hide or bottom-position. |

Session start: read TODO.md then docs/claude-changelog.md (top first).

NOTE: English only. Korean encoding is fragile across the toolchain. See CLAUDE.md "Document/TODO Encoding Rule".

## User decisions (2026-05-24)

| # | Decision |
|---|---|
| 1 | K-ICS skip cohort: KR0029 AIG, KR0150 SGI permanent skip. KR0051 / KR0074 partial-coverage by design. |
| 2 | Meritz IR source: Meritz Financial Group factsheet xlsx at https://m.meritzgroup.com/mo/ko/ir/ir1.do (replaces Meritz Hwajae standalone). AIG IR: skip low-priority |
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료** (IR calls it 월납월초). IR PDF for 6 cos; **assoc crawl** (KIDI/KLIA/KNIA) for 23-co computed multiple — see IFRS17-CSM-BUBBLE |
| 4 | First HTML viz: CSM Movement Waterfall (IFRS17 A1 23-co) |
| 5 | API keys: repo root `.env` only (gitignored). OpenDART=OPENDART_API_KEY; FSC bonds=DATA_GO_KR_BOND_ISSUANCE_KEY + DATA_GO_KR_BOND_REDE_KEY. Never commit/log key values |
| 6 | Bond Call rule: issue + 5y for ALL bonds (Korean market convention; ignore "콜" keyword gate). Past 5y = assume `called` (de facto mandatory per thebell/흥국 cases) |

## IFRS17

Universe: 23 insurers (`src/ifrs17/universe.py`).

| ID | Task | Status | Notes |
|----|------|--------|-------|
| IFRS-Q | Open Q1-Q9 | done | All 9 confirmed |
| IFRS-A1 | measurement rollforward | done | 23/23 MVP |
| IFRS-A2 | CSM amort | done | 23/23 |
| IFRS-A3 | insurance P&L | done | 23/23 MVP |
| IFRS-A4 | reinsurance rollforward | done | 23/23 MVP |
| IFRS-B1 | BS snapshot | done | 23/23 MVP |
| IFRS-B5 | sensitivity DART skim | done | 23/23 MVP. PoC only per Q8 |
| IFRS-B5-KICS | B5 K-ICS primary ingest | done | FY2025_Q4 **13/23** nonempty, **30** tables. KR0073 **4** + KR0069 **3** after IFRS keyword MD reparse (2026-05-25). |
| IFRS-B3-UNIFY | B3 = section8 long-format | done | ``src/ifrs17/row_normalizer.py`` + ``scripts/ifrs17_normalize_liability.py``; PoC **5** ``*_liability.json`` → ``data/ifrs17/normalized/*_liability_normalized.json``; **2956** rows scanned, **930** ``canonical_key`` hits (**1** empty source file: 삼성화재) |
| IFRS-NORMALIZE | 23-co full normalization | in-progress | ``data/ifrs17/crawl_manifest.json`` lists artifacts per insurer |
| IFRS-P3 | half/quarter reports | eligible | MVP complete |
| IFRS17-SEN-TABLE | sensitivity heatmap panel table load | done | sensitivity_heatmap 14/23 ok |
| IFRS17-HTML-DASH | IFRS17.html 7-panel dashboard | done | ECharts panel 1 + Chart.js 2-4; Samsung Life sensitivity table renders. (root single-source since 2026-05-28; was templates/) |
| IFRS-HIST | Historical 13Q ingest 2023.1Q~2026.1Q | done v1 | `scripts/ifrs17_batch_historical.py` + `_promote_history_to_measurement.py` + `viz_build_csm_waterfall_history.py`. 299 targets → 257 ok + 2 partial + 34 no_csm_block (분기보고서 text-only) + 5 errors. 사업보고서 23/23 거의 완벽. Output: `data/ifrs17/viz/csm_waterfall_history.json`. IFRS17.html Panel 8 "CSM 시계열" (dual-axis 기말+신계약, 22사 회색 배경 spaghetti) |

## index.html (market map)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| INDEX-C12 | treemap + IFRS17 quadrant | done | Post-transition default for items 27/28; IFRS17 quadrant below treemap |
| INDEX-IFRS17-BUBBLE | CSM bubble below K-ICS treemap | in-progress | size=CSM, color=NB CSM mult; `csm_bubble.json` + `viz_build_csm_bubble.py`; K-ICS treemap unchanged |

## K-ICS

| ID | Task | Status | Notes |
|----|------|--------|-------|
| KICS-SUB | sub-items 29-35 | done | Permanent skip KR0029/KR0150; image-only KR0010/KR0079 manual OCR |
| KICS-POST | values_post-transition | done | Historical reparse auto-fill |
| KICS-RATIO28 | item28 basic-capital post-transition | done | 133 rows `값_적용후` |
| KICS-HIST | historical reparse 9 periods | done | BATCH_END 2026-05-24T11:08:19Z |
| KICS-HTML-SUB | K-ICS.html sub-items + transition toggle | done | K-ICS.html + JSON sync (root single-source since 2026-05-28) |
| KICS-TIER2-UTIL | tier2 utilization 2025.4Q | done | KIRI PDF reconcile; 34/38 in 0-100%; output/tier2_utilization/ |
| KICS-TIER1-UTIL | tier1 hybrid utilization 2025.4Q | done | SCR×15% strict 10%; 35/38 valid; output/tier1_utilization/ |
| KICS-RULES-DOC | validation rules authoritative doc | done | docs/kics-json-validation-rules.md |
| KICS-PARSER-SPLIT | parser split-table + row scope fix | done | KR0005 FY2025_Q4 golden test |
| KICS-REPARSE-Q4 | FY2025_Q4 parse refresh | done | parse 30/38 ok; JSON 10028→10454 |
| KICS-KR0069 | Samsung Life all-quarters validation | done | Parser bullet-section fix; 0 RED all 12 quarters |
| KICS-KR0097 | Hana Life parse fix | done | RED 18→2 |
| KICS-RED-FIX2 | user-verified RED pass 1 | done | RED 419→311 |
| KICS-RED-FIX3 | missing RED reparse + item27/28 | done | RED 311→217 |
| KICS-RED-SAMPLES | per-rule RED export | done | scripts/summarize_red_findings.py |
| KICS-VALIDATE | rules 1-10 harness | done (ex OCR) | **RED=2** (KR0010 OCR only). report_20260525T000831Z. Rules 9 (item2 post≥pre) + 10 (item14 pre≥post) added 2026-05-25. fill_post_transition auto-detects unit hint mismatches via JSON 값 cross-check (×100 or ÷100 correction); 23 insurer-quarter combos fixed (3 ×100 + 20 ÷100). Rule 8_post latent bug (pre14 in denominator) also fixed → uses post14 consistently |
| KICS-IMG | image-only PDF manual OCR | todo | KR0010 KB Sonhae, KR0079 Mirae Asset, KR0080. Validator tol=10 for IMAGE_OCR_COMPANIES; manual OCR still needed for rule2 large diffs |

## Misc (IR and bonds)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| MISC-IR-CATALOG | IR visual-aid catalog 6 cos | done | docs/ir_visual_aids_research.md |
| MISC-IR-NB-DENOM | NB CSM ratio denominator + validation | in-progress | Crawl/extract → compute → validate vs IR. **Waterfall:** `validate_csm_waterfall.py` **23/23 pass** (NB required + rollforward identity). **NB mult:** 5/6 IR cohort pass (한화 period mismatch FY24 vs 1Q25). Loop: `run_ifrs17_csm_reconcile_loop.py` |
| MISC-IR-PROTOTYPE | viz prototype | in-progress | CSM Waterfall **23/23 ok** + validation. **NB CSM ratio:** IR 6-co. **index.html bubble:** `viz_build_csm_bubble.py` |
| MISC-IR-MERITZ | Meritz Financial Group factsheet xlsx ingest | done | 2026-05-25 — `data/ir/meritz/` (xlsx + extracted JSON + README). 1Q26: K-ICS 240.74%, CSM 112,917억, NB CSM mult 12.61x, Net income 4,661억 (Hwajae standalone). Group RoE 25.37%. Page: plain HTTP+AJAX, no JS required |
| MISC-BOND-KEYS | FSC API keys in .env | done | DATA_GO_KR_BOND_ISSUANCE_KEY + REDE_KEY |
| MISC-BOND-INGEST | FSC bond issuance + Call schedule ingest | done | 2026-05-25 v2 alias-loop fix. Latest pull 24 insurers. **15 missing accepted**: 외국계/디지털/특수법인 + KR0008/KR0069 likely no capital-instrument issuance (user 2026-05-25) |
| MISC-BOND-NORMALIZE | Bond schedule → per-ISIN calendar | done | Latest `data/bonds/normalized/20260525T061945Z/`. tier1 **63** + tier2 261 (was 48+276). `_classify_tier` recognizes `(신종)` / 신종자본증권 / 하이브리드 — fixes KR0032/KR0104 T1 mis-tag. |
| MISC-SEIBRO | Seibro HTML fallback | todo (low) | m.seibro.or.kr smoke ok; lower priority since FSC works |

## Long-term projects

> 📈 **중장기 제품·수익화·전략 로드맵 → `docs/roadmap.md`** (2026-05-26 신설)
> VC 사업성 밸리데이션 종합. Phase 0 (이해상충 선결) → Phase 1 (한국 데이터 심화: 추가 공시지표·정합성 보정·projection 엔진·재보험 스크리너) → Phase 2 (3-tier 수익화) → Phase 3 (Build-in-Public 마케팅) → Phase 4 (EU Solvency II / 일본 IFRS17 글로벌 피벗). 레이팅: 솔로 캐시카우 ★★★★☆ / 기술해자 ★★★★★.

| ID | Task | Status | Notes |
|----|------|--------|-------|
| IFRS17-CSM-BUBBLE | index.html IFRS17 bubble (CSM size × NB multiple color) | in-progress | Pipeline: crawl → `validate_csm_waterfall.py` → `validate_nb_csm_multiple.py` → `viz_build_csm_bubble.py`. **Waterfall validation 23/23.** Samsung/Meritz/Samsung Life NB CSM fixed (당기 block + non-zero sub-rows). |
| IFRS17-NB-RECONCILE | NB CSM multiple validation reconcile loop | in-progress | `run_ifrs17_csm_reconcile_loop.py` orchestrates measurement re-extract → waterfall → both validators → bubble. **Remaining:** 한화생명 FY24 numerator vs IR 1Q25 denominator — align quarter or override in `nb_premium_overrides.yaml` |
| KICS-FORWARD-CAPITAL | Forward solvency simulation chart in K-ICS.html | done v3 | v3 confidence uses `subordinated_eok` not numerator residual. Post tier-fix: KR0032 T1 bond=4500=BS; KR0104 **high**; KR0072 T1 still `fsc_missing_t1` (all FSC 신종 **called**, BS 2403). KR0003/KR0071 weak capital documented (no data fix). Latest `20260525T061947Z/forward_simulation_v3.json`. |

## Meta

- Encoding rule: CLAUDE.md "Document/TODO Encoding Rule" added 2026-05-24
- .gitignore: data/ifrs17/raw/, data/ifrs17/reports/ excluded
- 2026-05-25 doc trim: changelog 124KB→11KB (latest 5 entries detailed + historical archive 1-liners). TODO.md done-task Notes compressed
- git: **initialized + pushed** to github.com/solvencyk/insurequant (main). GitHub Pages → solvencyk.github.io/insurequant.
- 2026-05-26: docs/roadmap.md 신설 (중장기 제품·수익화·글로벌 피벗 전략)
- 2026-05-28 **HTML single-source refactor (P1+P4)**: templates/*.html 4개 삭제, 루트가 유일 원본. forward_capital_simulation.py → 루트 K-ICS.html 갱신. index.html 미사용 xlsx CDN 제거. 로컬 미리보기는 루트에서 `python -m http.server 8000`.
  - ⚠️ 남은 중복(다음 단계 후보): 데이터 JSON이 root↔templates 양쪽 존재 — templates/{kics_disclosure,tier1_utilization_latest,tier2_utilization_latest,forward_capital_latest}.json. recalc_*.py / crawl_assoc_nb_premium.py / extract_ir_wolnap_benchmarks.py 가 templates/로도 write. (P2 데이터 단일화 시 정리)
  - 남은 HTML 구조 todo: P3 공통 CSS/네비 → assets/common.css 추출 / P5 K-ICS 인라인 데이터 외부 JSON+fetch 통일
- 2026-05-28 **모바일 반응형 M1 (공통 토대)**: 4개 페이지에 `@media (max-width:640px)` 추가 — 헤더/탭 가로스크롤, 여백·글자·차트높이 축소, 표 가로스크롤. 데스크톱 무영향(640px 이하만). Claude Preview로 375px/1280px 검증 완료.
- 2026-05-28 **모바일 반응형 M2 (히트맵→리스트)**: index.html ≤640px에서 트리맵 숨기고 세로 리스트(회사명+색상막대+비율%, 비율 내림차순, 업권 그룹)로 자동전환. renderList()가 render()와 동일 데이터·색상·토글·클릭이동 공유. Preview 375px/1280px 검증, 콘솔 에러 0.
  - 모바일 남은 단계(선택): **M3** 차트 미세조정(K-ICS 도넛 2개 세로배치, Forward 라인 범례 위치 등)
- 2026-05-28 **IFRS17 패널 정리 + F6**: 연도별 CSM 상각(panel 2, 데스크톱 10년/모바일 5년) 신설. 파생 KPI 카드 4개 + BS 스냅샷 패널 **제거** → `docs/archived_metrics.md` 아카이빙(생성 스크립트는 유지). 패널 1~6 재번호. 재보험 영업관점 우선 추가지표 6종(요구자본 위험액 분해·RA·P&L 보험/투자 분해·출재율·유지율·운용자산이익률) → `docs/roadmap.md §1A-2`.
  - 후속 과제: **원천지표 카드 신설**(CSM 잔액·상각액·NB CSM 직접 노출, 제거한 파생 KPI 대체)

## MVP checklist (IFRS17)

- [x] A1 A2 A3 A4 B1 B5 all 23/23 MVP (B5 K-ICS primary ingest done FY2025_Q4)

## Next priorities

1. **KICS-IMG manual OCR** (user-owned): KR0010 KB Sonhae rule2 x2 — only remaining RED
2. **IFRS-B3-UNIFY coverage**: extend `row_aliases.yaml` for higher hit rate (current PoC **930**/2956 tagged)
3. **IFRS-NORMALIZE**: extend K-ICS sensitivity to remaining empty FY2025_Q4 life insurers (Hanwha/Heungkuk/KDB etc.)
4. **IFRS17-NB-RECONCILE**: fix validation fails (period/scope/unit); extend KIDI/KLIA FY24 crawl; re-run validate until IR cohort pass
5. **git init + commit + push** (.git not yet initialized)
