# CSM Movement Waterfall — Prototype (v1)

First HTML visualization for the IR/viz prototype track (TODO MISC-IR-PROTOTYPE,
user decision #4). Standalone static page that reads the existing IFRS17 A1
extracts.

## Files

| Path | Role |
|---|---|
| `scripts/viz_build_csm_waterfall.py` | Reads `data/dart/extracted/*_measurement.json`, picks the §14(4) measurement-rollforward block, sums CSM-only leaf columns per stage, writes the JSON below. |
| `data/dart/viz/csm_waterfall.json` | Per-company waterfall data (23 entries). |
| `prototype_csm_waterfall.html` | Single-file ECharts page. Fetches the JSON, draws the 6-stage waterfall, shows per-stage source labels and the original block header. |
| `.claude/launch.json` | Adds the `Viz prototype (static)` server (Python http on :8765). |

## Run

```
python -m http.server 8765
# open http://localhost:8765/prototype_csm_waterfall.html
```

Or via the Claude harness Preview tool: launch profile **Viz prototype (static)**.

## 6-stage row alias mapping

Order is `opening → new_business → interest → assumption → amortization → closing`.
For each stage the picker finds rows whose label contains *any* substring in
the patterns list, then keeps the candidate with the largest `|value|`
(avoids picking 보험계약자산 = 0 rows when 순부채/순장부금액 is the substantive
line).

| stage | patterns (subset — full list lives in script) |
|---|---|
| `opening` | 순부채(A/K) 헤더 strings, 기초 순장부금액, 기초 보험계약 순부채, 순부채(자산)(기초), 기초잔액, 기초 보험계약마진, 기초 |
| `new_business` | 당기 최초 인식, 처음/해당기간 최초 인식, 신계약 인식 variants, 당기 신계약, 최초 인식한 계약, 최초인식효과… |
| `interest` | 순보험금융손익, 보험금융손익 variants, 당기손익 인식분, 이자비용, 보험금융비용 … |
| `assumption` | 마진 조정 추정 문구, 미래서비스 관련 변동 variants, 가정 변경/예실차/추정의 변경 … |
| `amortization` | 당기손익 장문 라벨, 보험계약마진 상각(액), 보험계약마진상각 … |
| `closing` | 순부채(K), 기말 보험계약마진, 기말 순장부금액, 순부채(자산)(기말), 기말잔액, 기말 |

For `assumption` and `amortization` the row stub MUST contain
`보험계약마진` (`CSM_LABEL_REQUIRED` guard in `viz_build_csm_waterfall.py`). Other stages reuse the CSM value columns on broader netting rows where the label omits 마진 wording.

## CSM column detection

`find_csm_leaf_cols(header_rows)` returns the leaf-column indices (relative
to `row[1:]`) that correspond to CSM under the multi-row header. Handles:

- Top row contains `보험계약마진` and a sub-row breaks it into 2-4 CSM
  measurement-method columns (수정소급 / 공정가치 / 완전소급 / 소계).
  Examples: 삼성생명, 신한라이프, 흥국생명, 한화손해.
- Top row contains `보험계약마진` with no sub-row → single CSM column.
  Examples: KB손해, 한화생명, 케이비라이프, 미래에셋, 케이디비.
- 보험계약마진 appears in the second header row (sub) under a parent
  group like `보험료배분접근법 외 보험계약`. Examples: 동양생명,
  미래에셋생명, 푸본현대.

## Unit normalization

`detect_unit_scale` first scans captions/headers for "단위 : 백만원" /
"단위 : 원" annotations. When the source filing carries no inline unit
(Hanwha Sonhae, Hyundai Marine observed), a magnitude fallback infers:

- opening |v| > 1e10 → raw KRW (divide by 1e6)
- opening |v| > 1e8 → thousand KRW (divide by 1e3)
- else → assume already million KRW

All output values are normalized to **백만원 (million KRW)**.

## Status across 23 companies (built 2026-05-25)

- **ok (≥5/6 stages):** **23/23** after reading full `*_measurement.json` (not MVP-only) plus broader `STAGE_PATTERNS`.
- **partial:** 0
- **no_csm_columns:** 0

Note: some filings still put opening/closing substance in 순부채/부채 rows while the asset line is zero; the “largest |value| wins” row pick plus expanded opening/closing patterns mitigates this without per-company tables.

## Known gaps / next decisions

1. **HTML polish** is intentionally minimal. Confirm direction before investing in styling (currently dark theme + ECharts defaults + tooltip).
2. **Quarterly extension** waits for IFRS-P3 (half/quarter ingest).
3. **Library**: ECharts CDN. If a different library is preferred (Chart.js, Highcharts, D3 native) say so before further charts.

For deeper accounting reconciliation (IFRS normalize), track **TODO IFRS-NORMALIZE** — not blocking the waterfall POC.
