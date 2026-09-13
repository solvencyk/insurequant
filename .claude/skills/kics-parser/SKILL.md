---
name: kics-parser
description: >-
  insurequant K-ICS (Korean insurer 지급여력/solvency-disclosure) parser-lane domain knowledge — how to
  extract the capital/요구자본 items (지급여력금액·기본자본·SCR·지급여력비율, 1-28), 생명장기손해보험 sub-risks
  (29-35), 시장위험 분해 (금리·주식·부동산·외환·자산집중, 36-40), 금리위험 IRR 충격시나리오 순자산가치 (41-46),
  and 금리민감도 rate-sensitivity from Korean insurers' 정기경영공시 PDFs (via Docling MD) into kics_disclosure.json
  and kics_rate_sensitivity.json. Use this whenever working the kics lane in this repo: parsing or re-extracting
  a quarter's K-ICS disclosure, onboarding a new quarter, running or debugging the validation gate
  (scripts/validate_kics_disclosure.py — 19_market / 36_irr / rule5 / parent-zero RED), recovering missing
  market-risk subs (pdfplumber EOF → fitz fallback), backfilling a company/quarter, or reconciling/answering
  questions about K-ICS 지급여력비율·요구자본·시장위험 figures on the insurequant site. Covers the src/solvency/parser
  extractors, the fill_period → fill_subitems → fill_market pipeline, the gate's "RED=0 OR documented in TODO.md"
  contract, capital-tiering limits, per-company quirks (AIA 경과조치 미적용, 내부모형사 직접공시 IRR, 서울보증 보증보험
  생명장기=0, 코리안리 자동차, 카카오/예별 micro·자본잠식), even-Q vs odd-Q cadence, △(세모) negative sign, and
  unit 백만원↔억원 conversion. This is the K-ICS half of the 2-lane parser split — NOT for IFRS17 / CSM waterfall /
  DART filing parsing (that is the ifrs17 lane; use the ifrs17-parser skill for that).
---

# K-ICS parser lane (insurequant)

You are working the **kics** lane of the insurequant parser stage: turning Korean insurers' K-ICS
**정기경영공시** (solvency/지급여력 disclosure) PDFs into `kics_disclosure.json` + `kics_rate_sensitivity.json`,
which the site renders (`K-ICS.html`, `index.html` donut/ratio panels).

**Code/data are disjoint from the ifrs17 lane — stay on your side.** kics = `src/solvency/parser/`,
`scripts/fill_*` / `extract_market_*` / `validate_kics_disclosure.py` / `run_harness.py`, root
`kics_disclosure.json` / `kics_rate_sensitivity.json`, `data/disclosure/`, `md_inbox/`. ifrs17 = `src/ifrs17/`,
`CSM_waterfall.json` / `PL_breakdown.json`, `data/dart/`. The two run in **parallel sessions** (2-lane hard
split, CLAUDE.md) — don't edit ifrs17 files. **Join point:** `build_root_masters.py` runs once after both load.

## Source of truth

Tracked docs hold the **design/scope SOT** — read them for "what label means what" and "what formula gates what".
This skill does **not** duplicate them; it is the *operational* layer (current pipeline map + traps).

- `docs/agents/kics-json-validation-rules.md` + `docs/agents/kics-market-risk-decomposition.md` — the **rules
  SOT**: item 1-46 numbering + label mapping, every formula (R4/R7 matrices, 19_market MARKET_M, 36_irr derive,
  rule5), tolerances. **"What does the gate check?"** → here. The *code* `src/solvency/validation/kics_json_rules.py`
  is the final word — it wins over the doc on any disagreement.
- `docs/domains/claude-agent-kics.md` — the bootstrap-era domain stub. **Thin and partly stale:** only its
  extraction-target list, 생명장기 6-sub-risk list, the cross-quarter integrity rule, and the Samsung/Shinhan
  **split-table** mechanics (`extract_kics_summary_overview_rows`, `make_quarter_column_picker`) are durable.
  It predates and **omits** 시장위험 36-40, 금리위험 IRR 41-46, and 금리민감도 entirely, says `kics_data.json`
  (old name for `kics_disclosure.json`), and links pre-reorg flow docs. For market/IRR/sensitivity, trust the
  **code + this skill's references**, not that doc.

When a doc's status line conflicts with live code, **the code + this skill win** — verify against the script.

## Pipeline at a glance

```
data/disclosure/<period>/raw/        run_harness.py --stage parse         md_inbox/<period>/                 scripts/fill_* (UPSERT, idempotent)        kics_disclosure.json
  KR####_<회사>.pdf            ─▶    (docling → MD; venv python,    ─▶    KR####_<회사>.md          ─▶       fill_period_to_disclosure   (1-28 core)   ─▶  flat rows
  (gitignored, on disk)              ~100s/PDF, >5MB bad_alloc)            (Docling markdown tables)          fill_subitems_to_disclosure (29-35 생명장기)
                                                                                                              fill_market_subitems_…      (36-40 시장)
                                                                                                              market IRR recovery         (41-46 금리 IRR)
                                                                                                                         │
                                                       scripts/validate_kics_disclosure.py  ◀───────────────────────────┘   (gate: RED=0 OR documented)
  kics_rate_sensitivity.json  ◀──  금리민감도 extractor (경과조치 적용전/후 × measure × ±50/±100bp shock)
```

The market localizer `scripts/extract_market_section_pages.py` finds the 시장위험 pages; its **pdfplumber backend
dies on malformed-xref PDFs (EOF) → fitz (PyMuPDF) fallback** reads them fine. After loading, the gate validates.
**Designer owns the HTML; you own the JSON.** Render bugs (null shown as 0, label-exact-match drops) → handoff to
designer via `inbox/designer/`.

For the script-by-script file map, JSON schemas, gate rule formulas, and run/verify recipes, read
**`references/pipeline-map.md`**. For the company quirks + failure modes, read **`references/quirks-and-traps.md`**.

## Before you touch anything — the traps that bite

These are the hard-won ones. Full detail + per-company table in **`references/quirks-and-traps.md`**.

1. **Docling needs the venv python, not system python.** `run_harness.py --stage parse` (PDF→MD) only finds
   `docling` under `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`. ~100s/PDF; PDFs >~5MB can hit
   `std::bad_alloc`. PDF→MD conversion is **parser's job** (don't bounce a conversion gap to downloader). ([[project-docling-is-parser-stage]], [[project-venv-location]])
2. **pdfplumber EOF ≠ corrupt PDF.** When the market localizer errors on a PDF, it's usually pdfplumber's
   pdfminer backend choking on a malformed xref — **the PDF is fine, fitz reads it.** Recover via the fitz
   fallback; don't bounce to downloader as "corrupt". (This recovered NH/DB손해/한화 in one session.)
3. **even-Q vs odd-Q cadence.** 2Q/4Q are full-form (시장위험 36-40 + IRR 41-46 + 생명장기 29-35 breakdowns).
   1Q/3Q are **간이공시** (parent items only — 36-40/41-46 legitimately absent). A 19_market/36_irr RED on an
   odd quarter is usually cadence, **but verify the raw** — if the breakdown table *is* present (e.g. 카카오
   2023.3Q), it's a true positive and must be loaded, not cadence-SKIPped.
4. **parent=0 ⇒ children absent.** 생명장기위험액(item17)=0 (보증보험·디지털 손보 with no life book) means
   **29-35 cannot exist** — a non-zero child is a cell-shift mis-map (일반손해 대재해 leaking into the 1-7 slot).
   `fill_subitems` has a parent-gate + `_is_life_catastrophe_table` guard; the validator's `_parent_zero_child_nonzero`
   gates it. Same for item19=0 ⇒ 36-40 absent. ([[reference-kics-company-quirks]])
5. **△ (세모) is negative; distressed insurers really go negative.** Korean disclosures write negatives as △,
   not a minus sign — the extractors map △714 → -714. A negative 지급여력비율 (e.g. 예별/구MG 2025.4Q = -8.24%,
   자본잠식) is **real**, not a sign-parse bug. Any chart/table you add must display negatives as △ ([[feedback-samo-negative]]).
6. **Unit: source tables are usually 백만원, JSON is 억원** (1억 = 100백만, so ÷100). Sub-item/market tables in
   the 경과조치 적용 전/후 layout are commonly 백만원; the core extractor rounds 1-28 to integers (so a tiny
   item19=2 can break sqrt-reconcile = documented micro), while 36-46 keep 2-decimal precision. Let the unit-cue
   logic decide; never assume.
7. **Internal-model insurers disclose IRR directly.** 한화생명·신한라이프·교보 publish per-scenario 금리위험액,
   so the standard `derive_irr(41-46)` won't reconcile to item36 — the company values are correct. These are
   **owner-approved 36_irr exceptions** (INTERNAL_MODEL_36IRR_EXEMPT), not parse errors.
8. **Windows shell.** Use the full venv python (above). **Never run an inline multi-line `python -c`** — it hangs
   the shell and wedges Workflow subagents permanently ([[feedback-workflow-multiline-python-hang]]); write a
   `.py` file (put diagnostics in `scripts/_probes/`) or use Read/Grep. `sys.stdout = io.TextIOWrapper(sys.stdout.buffer,
   encoding="utf-8")` for Korean (console is cp949). Docs/inbox are UTF-8 **no BOM**; write English if Korean would garble ([[feedback-no-garbled-korean]]).

## How to work the lane

- **Drain your inbox first.** `inbox/parser/` items with frontmatter `lane: kics`. Answer in the file's
  `## 답변` section; bounce cross-stage work to the right `inbox/<stage>/` (designer for render, downloader for
  truly-missing raw, validation for rule/cadence questions, owner for OCR-only image cells). You don't auto-watch
  — the driver (Workflow/human) calls you; first act is to drain. ([[feedback-orchestrator-route-via-inbox]])
- **The gate is mandatory before any swap/push.** `validate_kics_disclosure.py` on root `kics_disclosure.json`:
  **RED must be 0, OR every remaining RED is a documented exception in `TODO.md`** (company, quarter, rule, reason).
  Any *unexpected* RED → parsing-error review (MD source, parser scope, row mapping) before continuing. Push is
  **owner authority** — parser never self-approves ([[feedback-user-approves-not-executes]]).
- **Coverage census is first-class — a missing cell is never acceptable.** SKIP-on-missing defeats validation.
  Probe the expected (회사 × 분기 × 항목) grid + parent-child completeness; don't let a 0-filled equation hide a
  결손 ([[feedback-coverage-census-mandatory]], [[feedback-validation-blind-spots]]).
- **Verify, don't guess.** Reconcile against the filing (item27 = item1/item14×100; item14 = item15−item22+item23;
  19_market sqrt(M-matrix of 36-40) ≈ item19; 29-35 sum / item17 ≈ 1.2-1.6 diversified). If a value doesn't match
  the owner's expectation, **stop and report the cause** — don't ship a guess. Push back rather than wander ([[feedback-ask-when-uncertain]]).
- **Parallelize by (회사 × 분기)** when chunks are independent and large; small fixes inline ([[feedback-multi-agent-parallel]]).
- **What's verifiable:** `pytest tests/unit/`, the gate above, and a per-(company,quarter) census probe.

After changing a master JSON, regenerate `insurequant_master_tables.xlsx`
(`python scripts/build_master_xlsx.py`) so the review loop stays in sync ([[feedback-rebuild-master-xlsx]]).
