#!/usr/bin/env python3
"""K-ICS.html capital-securities issuance panel (stacked timeline chart + two big cells) headless check
(designer, 2026-10-12). Screens only, not deployed.

The timeline JSON (`kics_capital_securities_timeline.json`, publishing ticket 20261012T1210Z) may not exist yet.
`--synthetic` (default when the file is missing) serves a fixture built from the tier1 rows' own outstanding balances so the
chart path can be exercised; it is NOT real data and is only used for this layout check.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/shot_capsec.py [desktop|mobile|dark|legacy ...]
"""
from __future__ import annotations
import json, re, socket, subprocess, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "designer" / "capsec_issuance"
TL = ROOT / "kics_capital_securities_timeline.json"
COS = [("hanwha", "한화생명"), ("meritz", "메리츠화재해상보험"), ("hyundai", "현대해상"), ("swissre", "스위스리아시아"),
       ("samsunglife", "삼성생명보험"), ("kyobolp", "교보라이프플래닛생명보험")]
PERIODS = ["2023.4Q", "2024.2Q", "2024.4Q", "2025.2Q", "2025.4Q", "2026.2Q"]
JS = """() => {
  const q = (id) => document.getElementById(id);
  const ch = window.Chart && Chart.getChart('capsec-chart');
  const cw = q('capsec-cells');
  const nl = String.fromCharCode(10);
  const cells = cw && !cw.hidden ? Array.from(cw.querySelectorAll('.capsec-cell')).map(c => c.innerText.split(nl).join(' / ')) : null;
  const rates = cw && !cw.hidden ? Array.from(cw.querySelectorAll('.capsec-rate')).map(r => [r.scrollWidth, r.clientWidth, Math.round(r.getBoundingClientRect().height)]) : null;
  const navs = Array.from(document.querySelectorAll('.section-nav a')).map(a => a.textContent.trim() + (document.getElementById((a.getAttribute('href') || '').slice(1)) ? '' : ' (DEAD)'));
  const shares = Array.from(document.querySelectorAll('[data-share-section]')).map(e => e.getAttribute('data-share-section'));
  const wrap = q('capsec-chart-wrap');
  return { chartWrap: wrap ? wrap.style.display : null, cellsHidden: cw ? cw.hidden : null, cells, rates,
    labels: ch ? ch.data.labels : null, series: ch ? ch.data.datasets.map(d => [d.label, d.data]) : null,
    chartBox: ch ? [ch.width, ch.height] : null, navs, shares, placeholder: q('capsec-placeholder').style.display,
    leftovers: ['donut-row', 'donut-tier1', 'donut-tier2', 'sec-forward', 'forward-chart', 'donut-section-panel'].filter(i => q(i)),
    helpHidden: q('capsec-help') ? q('capsec-help').hidden : null,
    h2: q('sec-capsec') ? q('sec-capsec').querySelector('h2').textContent.trim() : null,
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth };
}"""


def synthetic_timeline() -> dict:
    d = json.loads((ROOT / "kics_tier1_utilization.json").read_text(encoding="utf-8"))
    comp = {}
    for r in d["results"]:
        h, s = r.get("hybrid_outstanding_eok") or 0, r.get("subordinated_outstanding_eok") or 0
        if not (h or s):
            continue
        ser = {}
        for i, p in enumerate(PERIODS):
            f = (i + 1) / len(PERIODS)
            ser[p] = {"hybrid": round(h * f) if h and i >= 1 else None, "subordinated": round(s * f) if s and i != 2 else None}
        comp[r["code"]] = ser
    return {"source": "SYNTHETIC layout fixture", "as_of": "2026-06-30", "companies": comp}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.3).close(); break
        except OSError:
            time.sleep(0.2)
    from playwright.sync_api import sync_playwright
    rep = {}
    synthetic = not TL.exists()
    fixture = json.dumps(synthetic_timeline(), ensure_ascii=False) if synthetic else None
    want = set(sys.argv[1:])

    def serve_fixture(route):
        route.fulfill(status=200, body=fixture, content_type="application/json")

    def strip_summary(route):  # old-version tier1 JSON simulation (no securities_summary)
        resp = route.fetch(); d = resp.json()
        for r in d["results"]:
            r.pop("securities_summary", None)
        route.fulfill(response=resp, body=json.dumps(d, ensure_ascii=False), content_type="application/json")

    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vn, w, h, scheme, legacy in [("desktop", 1280, 900, "light", False), ("mobile", 375, 812, "light", False),
                                             ("dark", 1280, 900, "dark", False), ("legacy", 1280, 900, "light", True)]:
                if want and vn not in want:
                    continue
                ctx = br.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                for pref, name in COS:
                    if legacy and pref not in ("hanwha", "swissre"):
                        continue
                    pg = ctx.new_page(); errs = []
                    pg.on("console", lambda m, e=errs: e.append(m.text) if m.type in ("error",) else None)
                    pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                    pg.set_default_timeout(60000)
                    if synthetic:
                        pg.route(re.compile(r"kics_capital_securities_timeline\.json"), serve_fixture)
                    if legacy:
                        pg.route(re.compile(r"kics_tier1_utilization\.json"), strip_summary)
                        pg.route(re.compile(r"kics_capital_securities_timeline\.json"), lambda r: r.fulfill(status=404, body=""))
                    pg.goto(f"http://127.0.0.1:{port}/K-ICS.html?company={name}&iq_internal=1", wait_until="domcontentloaded")
                    try:
                        pg.wait_for_function("() => document.getElementById('capsec-placeholder') && document.getElementById('capsec-placeholder').style.display === 'none'", timeout=60000, polling=500)
                    except Exception:
                        print('WAIT FAILED', pref, vn, errs[:3]); raise
                    pg.wait_for_timeout(2500)
                    info = pg.evaluate(JS)
                    pg.locator("#sec-capsec").scroll_into_view_if_needed(); pg.wait_for_timeout(700)
                    pg.locator("#sec-capsec").screenshot(path=str(OUT / f"{pref}_{vn}.png"))
                    if vn in ("desktop", "mobile") and pref == "hanwha":
                        pg.locator("#capsec-cells .iq-help-btn").first.hover(); pg.wait_for_timeout(500)
                        pg.screenshot(path=str(OUT / f"{pref}_{vn}_help.png"))
                        box = pg.locator("#capsec-chart").bounding_box()
                        pg.mouse.move(box["x"] + box["width"] * 0.8, box["y"] + box["height"] * 0.7); pg.wait_for_timeout(600)
                        pg.locator("#sec-capsec").screenshot(path=str(OUT / f"{pref}_{vn}_tip.png"))
                    info["errors"] = errs; info["overflow"] = info["scrollW"] > info["clientW"] + 1
                    rep[f"{pref}_{vn}"] = info; pg.close()
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (OUT / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("timeline:", "SYNTHETIC fixture" if synthetic else str(TL))
    for k, v in rep.items():
        print(k, "overflow=", v["overflow"], "err=", v["errors"][:1], "leftovers=", v["leftovers"], "chart=", v["chartWrap"], v["chartBox"])
        print("   h2:", v["h2"], "helpHidden=", v["helpHidden"], "navs=", v["navs"], "shares=", v["shares"])
        print("   series:", v["series"])
        print("   cells:", v["cells"], v["rates"], "hidden=", v["cellsHidden"])


if __name__ == "__main__":
    main()
