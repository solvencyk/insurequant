# Insurequant Changelog — Publishing Stage

Stage 4 of 5 in the workflow split. See `CLAUDE.md` for the full 5-stage index.

**Scope:** master JSON assembly + change reporting + git push command recommendation. HTML structure/styling is **designer** ([`docs/changelog_designer.md`](changelog_designer.md)).

**Cross-stage history:** `docs/claude-changelog.md`.
**This file:** entries scoped to publishing work only.

---

## 2026-05-31 -- Publishing stage created (merge of gathering + pushing)

User decision: parser+validation are the "real" pipeline; gathering+pushing are mechanical follow-up to those. Merged into one **publishing** stage with two responsibilities: (1) assemble validated per-source JSON into HTML-ready masters, (2) report changes + recommend commit/push commands (human still runs `git push`).

- Combined prompt: `docs/agents/claude-agent-publishing.md` (replaces `claude-agent-gathering.md` + `claude-agent-pushing.md`, both deleted).
- New TODO/changelog created from root TODO items: F4 v2 / F13 / INDEX-IFRS17-BUBBLE / INDEX-BUBBLE-V2 / MISC-IR-NB-DENOM (publishing side) / MISC-IR-PROTOTYPE / IFRS17-CSM-BUBBLE.
- Done archive imported: KICS-TIER1/2-UTIL / KICS-FORWARD-CAPITAL / IFRS17-HTML-DASH / F17 Panel 3 data / F5 / F6 data side / F1 cross-nav data hook.
- Hard rule retained from pushing: this stage **reports + recommends only**, never runs `git push`.
- Hard split with designer: publishing owns master JSONs; designer owns HTML. If a new master field needs HTML rendering, publishing reports `manual_html_edit` warn and stops — designer takes over.

---

## 2026-05-30 -- Forward sim v3 deployed + bond tier `(신종)` fix data refresh

**Forward sim v3 (`20260525T061947Z`):** confidence high **5** (+1). KR0032: `fsc_missing_t1` cleared, T1 gap 0%; still **low** on T2 face vs BS (over_deduct). KR0104: **high**. KR0072: **`fsc_missing_t1` remains** — FSC has only **called** tier1 (700억); BS still shows 2403억 outstanding 신종 (not in FSC outstanding cohort).

**Weak capital (document only, no "fix"):** KR0003 Lotte basic_cap **-3875**억 / basic ratio **-23.7%**; KR0072 KDB basic_cap **-3311**억. User-confirmed real stress, not parser error.

(Bond normalize itself = downloader; this entry is the publishing-side refresh that consumed it.)

---

## 2026-05-30 -- F17 Panel 3 clean 4-bar swap (data side)

`scripts/build_net_income_breakdown.py` → `data/dart/viz/net_income_breakdown.json`. Tier1 10/10 손보 OK. Panel 3 (IFRS17.html) swapped from raw-table-last-column 12-row horizontal bar dump to clean 4-bar 당기순이익 decomposition (보험손익 / 투자손익 / 영업외 → 당기순이익). 보험금융 + 보종별 caption.

Designer swapped HTML; publishing owned the JSON shape.

---

## 2026-05-28 -- IFRS17 yearly CSM amort F6 (data side)

`viz_build_ifrs17_panels.py`: `extract_amort_schedule` now emits `yearly` (y1..y10 + y10plus + total) and `granularity` alongside the existing 4-bucket `buckets` (kept — `viz_build_ifrs17_kpis.py` + bubble still read buckets). New helpers `_year_bucket_cell` / `_year_bucket_indices` / `_yearly_from_aligned` / `_extract_transposed_yearly`. `granularity='yearly'` only when >=7 of y1..y10 present.

Split: **16 yearly / 6 coarse / 2 no-data** (of 24); 22/24 ok unchanged.

(HTML panel 2 swap = designer 2026-05-28.)

---

## 2026-05-25 -- IFRS17 CSM 시계열 panel 6 data buildout (assembly side)

Stage 3 of the IFRS-HIST pipeline (stages 1+2 = downloader/parser):

- `viz_build_csm_waterfall_history.py`: reuses `pick_main_block` + `extract_stages` + `detect_unit_scale` from FY-only viz builder. Aggregates per-(insurer, period) snapshots into time-series payload.
- Coverage 20 → **257 ok + 2 partial** out of 299 reachable after measurement promote.
- Output: `data/dart/viz/csm_waterfall_history.json` (319KB, 23 companies × 13 periods).
- IFRS17.html Panel 6 data wiring: dual-axis line, 기말 CSM solid + 신계약 CSM dashed, 22 background lines (회색 spaghetti).
- nulls for `no_csm_block` periods (spanGaps: false) — visible as gaps in HTML.

Push #2 deployed: commit e846e5a (6 files, 9271 insertions). data file 200 OK at 319KB at https://solvencyk.github.io/insurequant/data/dart/viz/csm_waterfall_history.json (now path; previously templates/).

---

## Older entries

Pre-2026-05-25 publishing/gathering/viz entries are in the compressed historical archive of root `docs/claude-changelog.md` ("## Historical archive (compressed)"):

- IFRS17 CSM Waterfall picker (5 no_csm 손보사 → 0, MVP filter off, ceded penalty)
- K-ICS.html Phase 4 (자본성증권 도넛 + Forward Outlook 라인)
- Forward sim v2 (confidence per-row, capacity_exhausted cap)
- KICS-FORWARD-CAPITAL Phase 3 v1 (yearly × 5y, 19사 cohort)
- Bond calendar v3 (5y Call rule for ALL bonds, 3-status outstanding/called/matured)
- FSC schedule API per-insurer full pull (publishing-side normalize)
- HTML single-source refactor P1+P4 (cross-cutting refactor; designer side too)
