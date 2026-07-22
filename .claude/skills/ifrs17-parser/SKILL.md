---
name: ifrs17-parser
description: >-
  insurequant IFRS17 parser-lane domain knowledge — how to extract CSM waterfall / 측정요소
  rollforward, 보험손익·투자손익 PL breakdown, BS snapshot, and 가정민감도 (assumption-sensitivity)
  tables from Korean DART insurer filings (DART 사업/반기/분기보고서 XML) into data/dart/extracted/*.json
  and the CSM_waterfall / PL_breakdown / sensitivity_heatmap masters & viz panels. Use this whenever
  working the ifrs17 lane in this repo: parsing or re-extracting a DART filing, building/refreshing an
  IFRS17 viz panel (scripts/viz_build_ifrs17_panels.py, build_pl_breakdown.py, build_csm_waterfall_master.py),
  debugging an IFRS17 extraction (label variants like 보험료배분접근법 vs 계약의 유형, product-row layouts,
  unit/sign), onboarding a new quarter of DART data, or reconciling/answering questions about IFRS17 figures
  (CSM 상각, 투자손익, 보험금융손익, 민감도 부호) on the insurequant site. Covers the src/ifrs17 extractors,
  the extracted & viz JSON schemas, unit normalization (1억=100백만), sign conventions, per-company quirks
  (동양 CSM-only sensitivity, 흥국 product-row layout, 하나생명 two-line investment), and the git-purge
  destructive-rebuild caveat on the fix/csm branch. This is the IFRS17 half of the 2-lane parser split —
  NOT for K-ICS / 지급여력 solvency-disclosure parsing (that is the kics lane).
---

# IFRS17 parser lane (insurequant)

You are working the **ifrs17** lane of the insurequant parser stage: turning Korean insurers'
DART disclosures into the IFRS17 metric masters and the viz panels the site renders.

**Code/data are disjoint from the kics lane — stay on your side.** ifrs17 = `src/ifrs17/`,
`scripts/*ifrs17*`/`build_pl_breakdown`/`build_csm_waterfall_master`, `data/dart/`, root
`CSM_waterfall.json`/`PL_breakdown.json`/`NB_CSM_multiple.json`. kics = `src/solvency/`,
`kics_disclosure.json`, `data/disclosure/`. The two run in parallel sessions; don't edit kics files.

## Source of truth

`docs/domains/claude-agent-ifrs17.md` is the **design/scope SOT** — the label-variant tables, the
CSM table-form taxonomy (Form A / A_rows / B), the slice rules (생보 = 전사 합계, 손보 = 장기 열),
and the Q1–Q9 design decisions. **Read it for "what label means what" / "how is this table shaped".**
This skill does **not** duplicate it — it is the *operational* layer (current pipeline map + traps).

> ⚠️ The SOT is 2026-05 bootstrap-era and some status lines are **superseded by current code**. Most
> important: SOT §7.3 / Q8 say "DART 민감도 = misaligned skim PoC, K-ICS is primary". That is no longer
> true — DART CSM/PL sensitivity is now a **real, owner-directed pipeline** (`sensitivity_extractor.py` →
> `sensitivity_heatmap.json`). Where SOT PoC-status conflicts with live code, **the code + this skill win.**

## Pipeline at a glance

```
DART raw XML                  src/ifrs17/*_extractor.py        data/dart/extracted/                 scripts/build_* + viz_build_*        data/dart/viz/*.json
data/dart/FY####_Q4/raw/  ─▶  (semantic scoring, no           <canonical>_<rcept>_<kind>.json  ─▶  build_csm_waterfall_master       ─▶  csm_waterfall*, csm_amort_schedule,
  KR####_<canon>_<rcept>/       per-company regex)              kinds: csm, measurement,             build_pl_breakdown               ─▶  pl_breakdown_master (+ root PL_breakdown.json)
  *.xml                                                         insurance_pl, reinsurance,           build_nb_csm_multiple            ─▶  csm_bubble, NB_CSM_multiple
                                                                bs_snapshot, sensitivity,            viz_build_ifrs17_panels          ─▶  bs_snapshot, insurance_pl_breakdown,
                                                                liability  (+ _mvp, + _*_summary)                                          sensitivity_heatmap
                                                                                                     build_root_masters (join, after BOTH lanes load)
```

The HTML (`IFRS17.html`, `index.html`) reads the `data/dart/viz/*.json` panels. **Designer owns the HTML;
you own the JSON.** Render bugs (e.g. null shown as 0) → handoff to designer via `inbox/designer/`.

For the file map, extracted-block + panel + PL-master schemas, and how to run/verify a batch, read
**`references/pipeline-map.md`**.

## Before you touch anything — the traps that bite

These are the hard-won ones. Full detail + per-company table in **`references/quirks-and-traps.md`**.

1. **Destructive rebuild on this branch.** `build_csm_waterfall_master.py` and `build_pl_breakdown.py`
   discover companies from `data/dart/FY*/raw/`, but that raw was **git-purged** on `fix/csm-…`
   (only AIA FY2024 + all FY2025 raw survive). Re-running either **collapses** the committed masters.
   On this branch, fix PL/CSM cells via **disposition + `_GOLD_CELL_OVERRIDE` / surgical JSON patch**, not a
   full rebuild. The CSM gold gate is also non-runnable here. (See [[project-git-purge]].)
2. **Unit.** Sensitivity panels are in **억원** (1억 = 100백만); PL master is in **백만원**. The sensitivity
   extractor normalizes via a unit cue, else cross-checks the table's base CSM against `CSM_waterfall.json`
   and power-of-10 snaps, with a `max|ΔCSM| > 3×total` suspect guard. Never assume — let the code decide.
3. **Sign.** For a life insurer, `보험금융손익` (discount unwind) is **hugely negative**, so a large negative
   *net* `투자손익` is structurally **real**, not a parse error. Sensitivity `csm_delta`/`pl_impact` are usually
   same-direction, but 해지율 can legitimately differ across a book — verify against the *current* filing, don't
   assume a sign bug from stale data.
4. **Company mapping.** Just search DART by company name — `"메리츠화재"` is enough. **Never build a permanent
   KR-code ↔ corp_code mapping file.** (Owner directive; [[feedback-ifrs17-company-mapping]].)
5. **`csm_delta = null` ≠ 0.** Some filings disclose only PL impact, no CSM column (e.g. 동양생명). null means
   미공시 and must render as '—', not 0.
6. **Windows shell.** Use the full venv python `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`.
   **Never run an inline multi-line `python -c`** — it hangs the shell (and wedges Workflow subagents);
   write a `.py` file or use the Read/Grep tools. `sys.stdout.reconfigure(encoding="utf-8")` (cp949 default).
   Docs/inbox files are UTF-8 **no BOM**; write English if Korean would garble. ([[feedback-workflow-multiline-python-hang]])

## How to work the lane

- **Drain your inbox first.** `inbox/parser/*ifrs17*` and items with frontmatter `lane: ifrs17`. Answer in the
  file's `## 답변` section; bounce cross-stage work to the right `inbox/<stage>/` (designer for render, downloader
  for missing raw). You don't auto-watch — the driver (Workflow/human) calls you; first act is to drain.
- **Verify, don't guess.** Reconcile against the filing and the cross-checks in `references/quirks-and-traps.md`
  (csm_amort_pl ≈ §(5) 당기손익 CSM; PL item17 = item18 + item19; 영업이익 = item1 + item17). If a pilot value
  doesn't match the owner's expectation, **stop and report the cause** — don't ship a guess.
- **Parallelize by (회사 × 분기 × kind)** when chunks are independent and large; small fixes do inline.
- **What's verifiable on this branch:** `pytest tests/unit/`, and `viz_build_ifrs17_panels.py` (reads committed
  `data/dart/extracted/*.json`). FY2024-quarter cell re-parses are raw-blocked; FY2025 is unblocked (raw on disk).
- **viz 빌더 골든 (2026-07-22):** `viz_build_ifrs17_panels.py`(4개 패널: csm_amort_schedule /
  insurance_pl_breakdown / bs_snapshot / sensitivity_heatmap)와 `viz_build_csm_waterfall.py`
  (csm_waterfall.json)에 골든이 있다 — `tests/test_viz_{ifrs17_panels,csm_waterfall}_golden.py`.
  두 빌더는 커밋된 입력(`data/dart/extracted/*` + `CSM_waterfall.json` + `sensitivity_overrides.json`)의
  순수 함수라 결정론적. **빌더를 고쳤으면 `python -m pytest tests/test_viz_*_golden.py` 필수**
  (오프라인 각 ~1.5초). 이 빌더들은 `data/dart/viz/`의 커밋된 파일을 **인플레이스로 덮어쓰므로**
  골든이 실행 전 백업·drift 시 복구한다. 산출이 의도적으로 바뀌면(추출 수정 등) `python
  tests/test_viz_<x>_golden.py --update` + 커밋에 이유 기록.

After changing a master JSON, regenerate `insurequant_master_tables.xlsx`
(`python scripts/build_master_xlsx.py`) so the review loop stays in sync ([[feedback-rebuild-master-xlsx]]).

## PL breakdown is a package now (2026-07-22) — read this before editing a handler

`scripts/build_pl_breakdown.py` was 4,885 lines / 129 top-level functions. It is now a
layered package and the entry script keeps only discover/assemble/main (567 lines):

```
scripts/pl_breakdown/
  common.py      34L   _norm / _label / _row_nums / _quarter_from_path / _quarter_sort_key
  tier1.py      355L   포괄손익계산서 (income statement) extraction
  tier2.py      475L   generic 계약유형별 / 재보험 note extraction
  companies.py 3438L   per-company handlers + SONBO_HANDLERS / LIFE_HANDLERS dispatch
scripts/build_pl_breakdown.py  567L   discover_filings / assemble / _fs_tier1 / main
```

**Where your edit goes:**

| 하려는 일 | 손댈 파일 |
|---|---|
| 특정 회사의 주석 레이아웃 대응 (대부분의 작업) | `pl_breakdown/companies.py` — 회사 섹션에 함수 추가 후 **`SONBO_HANDLERS` 또는 `LIFE_HANDLERS`에 등록** (파일 끝) |
| 모든 손보/생보에 공통인 표 인식 | `pl_breakdown/tier2.py` |
| 포괄손익계산서 라인 매칭 | `pl_breakdown/tier1.py` |
| 24-항목 벡터 조립·항등식·gold override | `build_pl_breakdown.py` (`assemble`, `_GOLD_CELL_OVERRIDE`) |
| 라벨/숫자/분기 파싱 헬퍼 | `pl_breakdown/common.py` |

**등록하지 않으면 함수는 죽는다.** 실제로 `extract_tier2_koreanre`가 그런 상태로 남아 있었다
(디스패치 표는 철자가 다른 `extract_tier2_coreanre`를 쓰고 있었음) — 2026-07-22 제거.

**의존 방향은 단방향이다. 지킬 것:** `companies` → `tier1`/`tier2`/`common`, `tier1` ↔ `tier2`
간선 없음. companies가 바깥에서 쓰는 이름은 11개뿐이고 전부 `companies.py` 상단에 **명시적
import**로 적혀 있다. 새 헬퍼가 필요하면 `import *`로 열지 말고 그 목록에 추가하라.

### 골든 게이트 — PL 빌더를 고쳤으면 반드시

```bash
RUN_PL_GOLDEN=1 python -m pytest tests/test_pl_breakdown_golden.py
```

빌더를 재실행해 `pl_breakdown_master.json` + `pl_breakdown_coverage.json`을
`tests/fixtures/pl_breakdown_golden.json`의 해시·행수와 비교한다(~95초). 빌더는 결정론적·
오프라인이다(DART FS API 응답이 `data/dart/_fs_api_cache/`에 캐시됨). 실패 시 아티팩트는
메모리에서 복구되므로 마스터가 반쯤 쓰인 채 남지 않는다.

- **구조만 바꿨는데 실패** → 리팩토링이 동작을 바꾼 것이다. 고쳐라.
- **의도적으로 값이 바뀜**(새 분기 raw, 진짜 추출 수정) → 해시를 손으로 고치지 말고 재생성:
  ```bash
  python scripts/build_pl_breakdown.py
  python tests/test_pl_breakdown_golden.py --update
  ```
  그리고 **왜 숫자가 움직였는지 커밋 메시지에 적어라.**

### 경과조치 적용후 (`fill_post_transition_to_disclosure.py`) — 골든 있음 (2026-07-22)

이 스크립트는 **라이브 `kics_disclosure.json`을 인플레이스로** 쓰고 `_extract_post_values`
(원래 569줄)가 회사별 함정 덩어리다(KR0082 unit-fix 투표, KR0004 stale 단위태그 상속,
KR0073 다중 breakdown 선택). 2026-07-22 사후보정 꼬리 182줄을 `_apply_post_corrections`로
분리해 389줄로 줄였다 — **동작 불변**.

고쳤으면 **`python -m pytest tests/test_post_transition_golden.py`** 필수(오프라인·~4초):
전 md_inbox 분기에 대해 순수 코어를 돌려 **쓰게 될 모든 `(회사,분기,항목)→(전,후,소스)`
6,114셀**을 해시로 고정한다(마스터는 안 건드림). 값이 의도적으로 바뀌면 `python
tests/test_post_transition_golden.py --update` + 커밋에 이유 기록.

### DART FS API 캐시 — 정정공시 대응 (2026-07-22)

`data/dart/_fs_api_cache/`(668파일, 커밋됨)는 PL 빌더 Tier-1 소스이자 PL 골든이 오프라인으로
도는 근거다. **owner 결정: 계속 커밋한다**(정정공시 드물고, git-purge 브랜치라 유일 사본일 수
있음). 단 함정 하나 — `_fetch_raw`는 캐시가 있으면 **영원히** 그걸 쓴다(만료 없음). DART
**정정공시(amended filing)**가 뜨면 stale 캐시가 마스터에 계속 반영된다.

정정공시가 뜬 회사-연도는 재취득 후 커밋하라:
```bash
python scripts/fetch_dart_fs.py --refresh <corp_code> <year>   # OPENDART_API_KEY 필요
python scripts/build_pl_breakdown.py                            # 마스터 재빌드
python tests/test_pl_breakdown_golden.py --update              # 골든 재생성(값이 바뀌었으므로)
```
그 다음 갱신된 캐시 + 마스터 + 골든을 **함께** 커밋하고 왜 바뀌었는지 적어라.

### 2026-07-22 아카이브된 것

`ifrs17_batch_{bs_snapshot,insurance_pl,reinsurance,kics_sensitivity}.py`,
`ifrs17_{summarise,dump_table,fetch_samsung_life,download_fy2025_nonlife}.py` →
`archive/2026-07_unreferenced_scripts/` (저장소 어디서도 참조되지 않아서). **살아있는 진입점은
`scripts/ifrs17_batch_all.py`와 `ifrs17_batch_{measurement,sensitivity,historical}.py`.**

`src/ifrs17/kics_sensitivity_extractor.py`(K-ICS MD에서 IFRS17 가정민감도 추출)와
`liability_extractor.py`도 같이 아카이브됐다 — 전자는 유일한 러너가 아카이브로 가서 고아가
됐고, 후자는 임포터가 처음부터 없었다. 그 경로가 다시 필요하면 **러너와 추출기를 같이**
`archive/2026-07_unreferenced_scripts/`에서 되돌려라.
