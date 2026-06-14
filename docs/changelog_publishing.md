# Insurequant Changelog — Publishing Stage

> Last updated: 2026-05-31 · Stage 4/5 — publishing
> Prompt: docs/agents/claude-agent-publishing.md · TODO: TODO_publishing.md

**Scope:** master JSON assembly + change reporting + git push command recommendation. HTML structure/styling is **designer** ([`docs/changelog_designer.md`](changelog_designer.md)).

**Cross-stage history:** `docs/claude-changelog.md`.
**This file:** entries scoped to publishing work only.

---

## 2026-06-14 -- Tier-1 hybrid utilization 100% cap (glitch G2 resolution)

9개사 2025.4Q tier1(기본자본 신종자본증권) 소진율 >100% (코리안리 242.5%, NH농협손해 187%, 교보 171% 등). 진단: 규정(K-ICS 해설서 [별표22] Ⅲ.2.다.(1)) 상 신종 한도(SCR×10%, 조건부자본증권 15%) 초과분은 보완자본 자동 재분류 → 소진율 정의상 ≤100%. >100%는 Ⅴ.1 재분류액(excess) 파싱누락 artifact. parser-kics 회신: standalone Ⅴ.1 행 9사 전부 부재(번들 "…초과한 금액 **등**" 행으로만 공시). 번들값 검산상 신종 한도초과분과 40배 차이(번들="등" 기타항목; 신종초과분은 공시 보완자본에 직접 반영, 라.(1)).

owner 결정: **소진율 100% 캡(옵션 2/3)** — tier2 cascade는 공시 보완자본 이중계상이라 미채택.

- `compute_tier1_utilization.py`: `utilization_pct=min(recognized/limit,1.0)*100` 캡(util_strict 동일) + 신설 필드 `tier1_hybrid_overflow_eok=max(recognized−한도,0)`(보완자본 재분류분 명시, 예: 코리안리 4,749억). definition에 `utilization_cap` 주석.
- 9사 util15 → 전부 100.0, util>100=0건. `templates/tier1_utilization_latest.json`(K-ICS.html 리더) 갱신.
- **무변경**: compute_tier2/forward_capital_simulation(cascade 미채택), K-ICS.html(line 816 Math.min 캡 그대로=안전망, designer 도메인). designer XXX%+ 도넛 구현 보류 확정.
- inbox 종결: parser `tier1_hybrid_excess_unparsed`(blind_spot, resolved), owner `tier1_overflow_cascade`(resolved) → `_resolved/`. designer 스레드 재통지(예외 없음).

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
