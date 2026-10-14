# Viz Prototype: NB CSM Ratio (line chart)

*2026-05-24 — IR/viz sub-agent*

## Goal

Standalone HTML prototype visualising the **New-business CSM ratio** time series
across major Korean insurers, per TODO.md Decision #3.

- Numerator: New-business CSM (from each company's IR PDF)
- Denominator: Monthly initial premium (월납월초) — IR industry standard
- Unit: ratio (x)

No KIDI / KLIA / KNIA crawl. Numerator, denominator, and ratio are all printed
in IR PDF bodies; ratio is extracted directly.

## Output

- `prototype_nb_csm_ratio.html` — standalone, ECharts via CDN. Two panels
  (non-life / life). Companies with insufficient time series listed in a
  partial-disclosure table below the charts.
- `data/ir/nb_csm_ratio.json` — extracted data, per-company series + partial points.

## Coverage

| Domain | Company | Series | Points | Chart |
|---|---|---|---:|---|
| Non-life | Samsung F&MI | protection-only quarterly | 3 | yes |
| Non-life | Hyundai M&F | total / personal / property | 4 each | yes |
| Non-life | DB Insurance | annual snapshot only | 1 | no (partial table) |
| Non-life | KB Insurance | group-level only | 0 | no (partial table) |
| Life | Samsung Life | total + health/death/financial | 5 each | yes |
| Life | Hanwha Life | total / general-protection YoY | 2 each | yes |
| Both | Meritz | pending (xlsx ingest TODO MISC-IR-MERITZ) | 0 | no |

Successfully charted: **4 of 6** companies (Samsung F&MI, Hyundai M&F,
Samsung Life, Hanwha Life). DB and KB excluded from line chart due to
insufficient quarterly disclosure; their snapshot values are listed in the
partial-disclosure table.

## Sample sanity values

- Samsung F&MI protection: 11.9 → 13.8 → 14.9x (FY25 1Q→3Q, recovering)
- Hyundai M&F total: 13.4 → 18.9x (2024.1H → 2025.2Q, growing)
- Samsung Life total: 10.2x (FY25.1Q); health 16.3x; death 5.1x; financial 3.0x
- Hanwha Life total: 6 → 8x (1Q24 → 1Q25, YoY +33%)

## Design notes (kept simple per CLAUDE.md)

- ECharts (matches CSM Waterfall prototype sibling)
- Per-company stable color; product-line variants differentiated by line style
  (solid total / dashed primary subgroup / dotted secondary subgroup)
- Periods on x-axis union all observed labels; gaps left as null
  (`connectNulls: true` only for Hanwha 2-point lines)
- No external font, no build step; single file viewable by double-click

## Known imperfections

- Samsung F&MI total ratio not on a quarterly basis in the source deck (only
  YTD 24.1-3Q vs 25.1-3Q comparison). Only protection-type series shown.
- Hyundai mixes 1H (semiannual) and 2Q (quarterly) on the same axis; this is
  faithful to the source deck.
- Period labels are not normalised between companies (FY24.1Q vs 2024.1H vs
  1Q24). Acceptable for prototype; normalise if/when promoted to main viz.
