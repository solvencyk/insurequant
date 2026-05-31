# Archived metrics (removed from live display)

Last updated: 2026-05-28

Metrics intentionally removed from the IFRS17 dashboard display but preserved here
(and still computed offline) so they can be revived later. Removal rationale came
from the user's product-priority review: derived **proxy** ratios are non-official
and can mislead B2B users when numerator/denominator definitions are not obvious;
showing the **raw** source figures (CSM closing, amortization, new-business CSM) is
more trustworthy. The BS snapshot duplicated what DART shows directly.

## 1. Downstream KPI cards (4) — archived 2026-05-28

Previously panel "5) Downstream KPI 카드" in `IFRS17.html`. The display (panel +
`renderCompany` block + `.kpi-*` CSS + PATHS/payload/ix wiring) was removed.

**Still generated** by `scripts/viz_build_ifrs17_kpis.py` → `data/dart/viz/downstream_kpis.json`
(kept because `scripts/viz_build_csm_bubble.py` reads `inputs.closing_csm_mn_krw` from it).

Definitions (from the generator):

| Card label (KR) | field | definition |
|---|---|---|
| CSM 의존도(프록시) | `csm_dependency` | \|CSM amort\| / (\|CSM amort\| + insurance service margin proxy) |
| CSM 런웨이(년) | `csm_runway_years` | closing CSM / \|annual CSM amort\| |
| 스케줄 소진 속도 | `schedule_run_rate` | sum(A2 y1 + y1_y3 buckets) / closing CSM |
| NB 교체 필요도(프록시) | `nb_replacement` | \|new business CSM\| / \|CSM amort\| |

Notes:
- `schedule_run_rate` was the weakest: non-official, built on the coarse 4-bucket
  amort split, plus a `scale` heuristic (×1 / ×1e3 / ×1e6) to paper over unit
  mismatches between `near_term` and `closing` — fragile.
- The new yearly CSM amort chart (panel 2) already shows near-term release visually,
  making a separate scalar run-rate redundant.

**To revive:** re-add the panel `<div data-pane="kpi">` template, the `renderCompany`
KPI block, the `.kpi-grid`/`.kpi-card` CSS, and `PATHS.kpi` / `payload.kpi` / `ix.kpi`
+ boot fetch wiring. (See git history around commit for this date.)

## 2. BS snapshot table — archived 2026-05-28

Previously panel "6) BS 스냅샷 표" in `IFRS17.html`. Low value vs. reading DART
directly; consumed layout space (low 시안성). Display + `renderMatrixTable` helper
removed.

**Still generated** by `extract_bs_snapshot` in `scripts/viz_build_ifrs17_panels.py`
→ `data/dart/viz/bs_snapshot.json`.

**To revive:** re-add the `<div data-pane="bs">` template, the `renderMatrixTable`
function + the BS render block, and `PATHS.bs` / `payload.bs` / `ix.bs` + boot wiring.
