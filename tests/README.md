# Dashboard regression tests (Playwright)

Automated regression harness for the three designer-owned dashboards
(`K-ICS.html`, `IFRS17.html`, `index.html`). Encodes the cumulative owner/QA
glitches (round1~3 + DS1 design-system) as asserts so they stop being
eyeball-only.

Why Playwright: this machine's Edge/Chrome `--dump-dom` returns 0 bytes; the
Claude Preview MCP works interactively but isn't CI-able. Playwright ships its
own headless Chromium that runs here, and `with_server.py` manages the static
server lifecycle (no zombie ports).

## One-time setup

```
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe   # tree-external venv
"$PY" -m pip install playwright
"$PY" -m playwright install chromium
```

## Run

```
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
SRV=C:/Users/sangwook.cho/.claude/skills/webapp-testing/scripts/with_server.py
"$PY" "$SRV" --server "$PY -m http.server 8899" --port 8899 -- \
    "$PY" tests/regression_dashboards.py --port 8899
```

Run from the **repo root** (the http.server serves the repo root, where the HTML
+ JSON masters live). Exit 0 = all green, 1 = at least one regression.

If you hit `net::ERR_EMPTY_RESPONSE` on every page, a zombie `http.server` from a
previous run is squatting the port (Windows doesn't always reap it). Re-run on a
fresh `--port` (e.g. 8902, 8903, …).

## What it asserts (29 checks)

- **index**: common.css loaded · hero KPI strip (총 CSM 조 / K-ICS 중위값 % / 수록 N社 /
  기준 YYYY.nQ) · typeahead datalist populated + jump navigates to IFRS17 · treemap
  cells render (desktop) · 0 console errors
- **K-ICS**: common.css · company dropdown ≥40 · KB(KR0010) 2026.1Q solvency point
  present and ≈185.87 (label-variant fix) · 0 console errors
- **IFRS17**: common.css · sensitivity as-of caption (`기준: … YYYY-MM-DD`) · shock
  ↑/↓ normalization · △ samo negatives · axis windowing year `[2023,2024,2025,
  2026.1Q]` + quarter last-5 · 4Q-only company quarter-mode "분기 공시 미제공"
  message · 재보험 `.subtoggle` button shape (18px, common.css) · dotted series
  legend label "신계약 CSM 시계열 (점선)" · CSM waterfall + PL table period
  windowing (quarter=5, year=[2023,2024,2025,2026.1Q]) · 롯데 PL 투자손익
  zero-crossing bar goes below 0 (y0>0>y1) · 0 console errors

## Known gap (visual-only)

Canvas-drawn text (Chart.js donut center "100%+", ECharts waterfall labels) is not
in the DOM, so it isn't asserted here — verify those visually. To make the tier1
donut "100%+" testable, expose the pct as a `data-pct` attribute on the donut
container in a future pass.
