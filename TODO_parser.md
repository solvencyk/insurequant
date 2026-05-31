# Insurequant Parser TODO (Stage 2)

Last updated: 2026-05-31.

Stage 2 — **parser**: raw artifacts (DART body XML / Docling MD / IR xlsx / FSC bonds raw / KIDI JSON) → structured per-record JSON. The validation subagent rule-checks the result; gathering composes derived viz.

**Stage files**
- Prompt: [`docs/agents/claude-agent-parser.md`](docs/agents/claude-agent-parser.md) (skeleton)
- Changelog: [`docs/changelog_parser.md`](docs/changelog_parser.md)
- This file: open parser work + parser-done archive

Session start: read this file + `claude-agent-parser.md` + relevant domain ref(`docs/domains/claude-agent-{kics,ifrs17,misc}.md`).

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## Taxonomy correction (this session, 2026-05-31)

LOB axis differs between 손보 CSM decomposition and 손보 P&L decomposition. Do NOT conflate them in the parser.

- **손보 CSM decomposition** = 보장성 / 물보험 / 저축성 (all within 장기보험; 삼성화재 uses this taxonomy)
- **손보 P&L decomposition (보험손익)** = 장기 / 자동차 / 일반 (Tier2 in F17)
- 자동차 / 일반 are PAA contracts → no CSM rollforward; they contribute to P&L only
- 보종별 신계약 CSM multiple is IR-disclosed only for a subset of insurers; do not synthesize from DART for the others

This box should be removed once F17 lands and the prompt §2.2 captures it.

---

## In-flight (F17 Tier2 LOB 9/11사 확장)

**Status snapshot (this session, 2026-05-31)**

- Tier2 LOB extraction extended from prior 4사 → **9/11 손보사** OK against reconciliation gate.
- IR cross-check report generated: 3-co spot compare (메리츠 / 삼성화재 / DB).
- **Decision pending — three options to discuss with user:**
  1. Commit 9/11 as-is, document the 2 remaining gaps as documented exceptions.
  2. Debug 삼성화재 일반보험 (+246% gap vs IR) and DB 자동차 (sign flip vs IR) before committing.
  3. Commit only IR-verified clean companies (메리츠 baseline); keep 7 others as needs-review.

Cross-check findings:
- 메리츠: matches IR within tolerance
- 삼성화재: 일반보험 손익 +246% vs IR factsheet — likely BS rollforward bleed-through into flow analysis table, or factor-unit mismatch on that segment
- DB: 자동차 sign flip vs IR — picker chose row where 보험비용 > 보험수익 yet IR shows positive 손익; suspect wrong-row pick or 보험금융수익 contamination

Report path: `output/f17_tier2_lob/ir_crosscheck_20260531.md` (gather from session artifacts before next handoff).

---

## Open parser work

### F12 — K-ICS 시장위험 하위위험액 전체 파싱 (parser side)

Parser + validation cross-stage. 금리·주식·부동산·외환·자산집중 등 하위위험액 + 분산효과 행 추출 (화면 노출 X, 데이터 신뢰용). The validation half is V3 in [`TODO_validation.md`](TODO_validation.md).

- [ ] 시장위험 하위 5개 + 분산효과 row 추출 추가
- [ ] 금리위험액 (+5쇼크 순자산 민감도 = 듀레이션갭) display-ready 필드 분리
- [ ] 출력 schema에 `market_risk_breakdown` 신설 → validation R11 sqrt 정합성 룰의 입력

### F15 — CSM 시계열 분기 결측 (remaining gaps after 2026-05-29 fixes)

대부분의 결측은 2026-05-29 `<TE>` data-cell fix + product-segmented column 식별 + 압축 헤더 dedup 으로 복구됨. **잔여 honest gaps:**

- [ ] **삼성생명 2023.1Q** — early-2023 different layout, parser miss
- [ ] **미래에셋 2023.1Q / 2023.3Q / 2026.1Q** — same family of early-2023 layouts plus a 2026.1Q anomaly
- [ ] **동양생명 2025.2Q ~ 2026.1Q** — 잔액(기초/기말) row 모두 0으로 추출됨; 재다운로드 검토는 `TODO_downloader.md` F15-DL
- [ ] **손보 일부 전사-vs-세그먼트 pick** — reject guard 적용 후 gap 처리; 회사별 disambiguation matrix 필요

### F16 — Panel 5 흥국생명 민감도 (product-as-rows layout)

흥국생명 sensitivity 표는 별도 양식: 상품(사망 / 건강 / 연금) = 행, 당기말 / 전기말 × CSM / 손익효과 / 자본효과 = 컬럼. 영문 'CSM' + '손익 효과' 라벨 사용. 기존 3-path band parser 미적용 → 행 어긋남.

- [ ] product-row × period-band-column 4번째 path 신설 (`viz_build_ifrs17_panels.py` 또는 sensitivity_extractor)
- [ ] 다른 회사 회귀 zero check
- [ ] Panel 5 caption 갱신 (가능한 회사 명시)

### F17 — Tier1 (전사) + Tier2 (LOB) 당기순이익 분해 (parser body)

Tier1 10사 OK 유지. Tier2는 위 in-flight 박스 참조. **남은 parser gap:**

- [ ] **KB / 메리츠 / NH농협** — FY2025 사업보고서가 FS를 **별첨 감사보고서**로 분리, body XML에 LOB 없음. (별첨 fetch는 사용자 결정상 안 함; 회사별 label 매트릭스 + 본문 내 다른 표 찾기로 해결 필요)
- [ ] **DB / 한화 / 흥국** — 회사별 disambiguation (다중후보표 중 picker가 오선택)
- [ ] **삼성화재 Tier2** — taxonomy 가 보장성/물보험/저축성 → 현 파서가 장기/자동차/일반만 기대해 미스 (taxonomy correction box 참조)
- [ ] **코리안리** — 재보험사 LOB N/A, 영구 SKIP
- [ ] FY2024 LOB — 사업보고서에 존재 (감사보고서 X). 필요 시 fetch 대상 분리

### F18 — IR factsheet 정형화 (DART↔IR cross-validation 활성화)

Parser + gathering. Validation 룰 3개는 추가됨 (V1 in [`TODO_validation.md`](TODO_validation.md)); 활성화 대기.

- [ ] **Delivery 계약**: `data/ir/<period>/parsed/<KR>.json` 정형 JSON. Schema: [`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md) §1.4. 모든 값 억원
- [ ] **출발 cohort 9사**: 메리츠 · 삼성화재 · 현대 · KB · DB · 한화생명 · 삼성생명 · 미래에셋 · 동양
- [ ] IR 미공시 회사 (교보 · KDB · 외국계 · 카카오페이손해 등) auto-SKIP 명시
- [ ] 생보 `segment_insurance_income` 키 셋 (보장성 / 저축성 / 연금 / 변액 후보) 확정 필요 — validation V1 참조

### IFRS-NORMALIZE — 23-co full normalization (extend B3-UNIFY coverage)

- [ ] `row_aliases.yaml` 확장 (현재 PoC 930 / 2956 tagged)
- [ ] K-ICS sensitivity 잔여 empty FY2025_Q4 생보사 normalize

### KICS-IMG — image-only PDF manual OCR

- [ ] **KR0010 KB손해** rule 2 x2 (validation gate 잔여 RED 1건의 root cause)
- [ ] KR0079 미래에셋생명
- [ ] KR0080
- 정책: parser는 image-only PDF 만나면 escalate; OCR 즉흥 금지 ([claude-agent-parser.md](docs/agents/claude-agent-parser.md) §2.1)

---

## Done — recent (parser-scoped)

| ID | Task | Done | Notes |
|----|------|------|-------|
| ~~F11-WF~~ | Foreign-affiliate life 5사 waterfall-builder safe fixes | 2026-05-29 | Magnitude unit fallback by largest-magnitude stage / 직접 block always outranks ceded / 보고기간말 label + guarded net-row patch. 23-co zero regression |
| ~~F15-TE~~ | `<TE>` data-cell parser fix (the real F15 root cause) | 2026-05-29 | `csm_extractor._iter_tables_with_context` now recognizes `<te>` as a data cell. Recovered 한화 all 13Q, 교보 all quarters, 삼성화재 2025.2Q/3Q, 현대해상, 케이디비, 코리안리 |
| ~~F15-LEAF~~ | `find_csm_leaf_cols` 6-row multi-level header fallback | 2026-05-29 | Was only inspecting rows 0–2; now scans all header rows and maps 보험계약마진 to the right index |
| ~~F15-PICKER~~ | Picker hardening (consolidation filter + continuity all-candidates + FY-anchor) | 2026-05-29 | Exclude 관계기업/종속기업/요약재무정보/지분 tables; continuity searches all candidates not top-5; FY-anchor 45% guard with ≤35% fallback |
| ~~F15-SEG~~ | 삼성생명·미래에셋 product-segment column id + 압축 헤더 dedup | 2026-05-29 | `find_product_segmented_csm_cols` + `collect_current_product_blocks` + 7 safety gates. FY anchor: 삼성 13.08조 / 미래 2.08조 / 동양 2.54조. Per-product split (사망/건강/연금/저축/기타) now summed correctly; `소계`/`합계` no longer double-counted |
| ~~F16-RS~~ | Panel 5 sensitivity rowspan + header-aware parse | 2026-05-29 | `_band_sensitivity_columns` + `_extract_sensitivity_band` (rowspan-elided continuation rows inherit risk). Fixed 한화 / 교보 / 케이디비 / DB생명. 삼성생명 unchanged. **흥국생명은 별도 layout** → F16 잔여 |
| ~~F17-T1~~ | Tier1 (전사) 당기순이익 분해 — 10/10 손보 | 2026-05-30 | `scripts/build_net_income_breakdown.py` → `data/dart/viz/net_income_breakdown.json`. 매그니튜드 자동추론 + 보험손익+투자손익≈영업이익 일관성 + 자릿수 concatenation guard |
| ~~F17-T2v1~~ | Tier2 LOB 1사 (현대) → 4사 검증 (삼성화재 / 현대 / DB / 한화손보) | 2026-05-30 (b) | position-based 컬럼 식별 + rollforward 표 제외 + 보험수익(LOB) = max(합계행, 컴포넌트 합) + 단위 factor = Tier1 anchor + 연결 우선 |
| ~~NB-SAMSUNG~~ | Samsung Life 사망 NB CSM regex misparse fix | 2026-05-29 | rfind("사망") + cap-filtered `\d+\.\d+` scan. Death now [7.6, 10.0, 7.6, 7.2, 5.1] (was 520/471/488 absolute amounts read as multiples). Validation gate side is changelog_validation 2026-05-29 |
| ~~CSM-DECONTAM~~ | Panel 6 prior-period contamination + per-quarter new-business | 2026-05-29 | `pick_main_block._period_affinity` penalty for 전분기/전반기 + bonus for 당분기/당반기 (guarded for combined captions). `add_nb_increments` chains across unobserved quarters. 한화 2025.1Q 13,362,336 → 12,994,325 (caption "1) 당분기"); 0 regressions on FY28 |
| ~~CSM-CONT~~ | History builder continuity tiebreak (한화 2023.4Q dip) | 2026-05-29 | `rank_main_blocks` exposed + guarded 25%/5% continuity tiebreak. 한화 9.24조 → 13.30조; 롯데 2025.4Q 0.03→4.92조; 메리츠 2026.1Q 0.05→11.1조; 신한 14.7조 / 케비 3.4조. FY waterfall 0 regression |
| ~~IR-DISCLOSED~~ | 손보 disclosed/derived NB CSM 배수 (삼성화재 / DB / 한화손보 / 현대) | 2026-05-30 | 삼성화재 13Q disclosed (factsheet CSM sheet); DB 13Q derived (component-based, KIDI-consistent); 한화손보 DART numerator ~2x overstatement flagged (no multiple emitted); 현대 single-point |
| ~~IR-MULTIPLES~~ | `build_ir_disclosed_multiples.py` aggregation | 2026-05-30 | DISCLOSED_KEYS / DERIVED_KEYS 추가 → `data/ir/disclosed_csm_multiple.json` 9사 |
| ~~IFRS-A1~~ | Measurement rollforward extractor | done | 23/23 MVP |
| ~~IFRS-A2~~ | CSM amort schedule extractor | done | 23/23 |
| ~~IFRS-A3~~ | Insurance P&L extractor | done | 23/23 MVP |
| ~~IFRS-A4~~ | Reinsurance rollforward extractor | done | 23/23 MVP |
| ~~IFRS-B1~~ | BS snapshot extractor | done | 23/23 MVP |
| ~~IFRS-B5~~ | Sensitivity DART skim extractor | done | 23/23 MVP (PoC) |
| ~~IFRS-B5-KICS~~ | B5 K-ICS primary ingest | done | FY2025_Q4 13/23 nonempty, 30 tables. KR0073 4 + KR0069 3 after IFRS keyword MD reparse |
| ~~IFRS-B3-UNIFY~~ | B3 = section8 long-format normalizer | done | `src/ifrs17/row_normalizer.py` + `scripts/ifrs17_normalize_liability.py`; PoC 5 → `*_liability_normalized.json` (930/2956 tagged) |
| ~~IFRS-HIST~~ | Historical 13Q ingest 2023.1Q ~ 2026.1Q | done v2 | parser side: `scripts/ifrs17_promote_history_to_measurement.py` (294 → 293 ok). Combined with `<TE>` + leaf-col + picker fixes (F15 series), 257 ok + 2 partial + 34 no_csm + 5 err. 2026-05-29 v2 = prior-period decontamination + per-quarter new-business |
| ~~IFRS17-SEN-TABLE~~ | sensitivity heatmap panel table load | done | sensitivity_heatmap 14/23 ok |
| ~~KICS-PARSER-SPLIT~~ | Parser split-table + row scope fix | done | KR0005 FY2025_Q4 golden test |
| ~~KICS-REPARSE-Q4~~ | FY2025_Q4 parse refresh | done | parse 30/38 ok; JSON 10028→10454 |
| ~~KICS-KR0069~~ | Samsung Life all-quarters parser fix | done | bullet-section start patterns; 0 RED all 12 quarters |
| ~~KICS-KR0097~~ | Hana Life parse fix | done | RED 18→2 |
| ~~KICS-RED-FIX2~~ | User-verified RED pass 1 (parser-side fixes) | done | RED 419→311 (Rule 2 label/alias fixes, MetLife reverse, item4 reconcile) |
| ~~KICS-RED-FIX3~~ | Missing RED reparse + item27/28 recalc | done | RED 311→217 |
| ~~KICS-SUB~~ | Sub-items 29-35 parser | done | image-only KR0010/KR0079 → KICS-IMG (above, jurisdiction = parser escalate) |
| ~~KICS-POST~~ | `값_적용후` historical reparse | done | Auto-fill across periods |
| ~~KICS-RATIO28~~ | item28 basic-capital post-transition | done | 133 rows `값_적용후` |
| ~~KICS-HIST~~ | Historical reparse 9 periods | done | BATCH_END 2026-05-24T11:08:19Z |
| ~~UNIT-HINT~~ | Unit-hint mismatch auto-detect (parser) | done | 23 insurer-quarter latent bugs (3× ×100, 20× ÷100), 56 post values corrected. Rule 8_post pre/post bug fixed at parser layer |
| ~~B5-APPENDIX~~ | IFRS17 B5 K-ICS sensitivity appendix headings + multi-period batch | 2026-05-25 | `kics_sensitivity_extractor.py` recognizes appendix wording (보험위험 + 민감도 without contiguous 가정민감도); default `min_score=3`; `--all-periods` batch. 49 tables across 12 quarter folders; FY2025_Q4 11 insurers / 23 tables |

---

## Reading order for parser subagent

When invoked, read in this order:

1. This file (`TODO_parser.md`) — current state, in-flight decision points, taxonomy box
2. [`docs/changelog_parser.md`](docs/changelog_parser.md) — history (what prior sessions did)
3. [`docs/agents/claude-agent-parser.md`](docs/agents/claude-agent-parser.md) — master prompt + per-domain contract
4. Domain ref(s): [`docs/domains/claude-agent-{kics,ifrs17,misc}.md`](docs/domains/) for label variants and known company-specific quirks
5. Root [`TODO.md`](TODO.md) only for cross-stage items (F12 / F17 / F18) — full detail lives here

---

## Hand-off to validation

After parser produces a normalized JSON, validation is invoked per [`docs/agents/claude-agent-validation.md`](docs/agents/claude-agent-validation.md) §3 (retry loop, max 5). On RED, validation calls back the parser with the failing rule + suspected source.
