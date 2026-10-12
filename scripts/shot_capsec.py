#!/usr/bin/env python3
"""K-ICS.html capital-securities utilization panel headless check (designer, 2026-10-12). Screens only, not deployed.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/shot_capsec.py
"""
from __future__ import annotations
import json, re, socket, subprocess, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "designer" / "capsec_labels"
COS = [("hanwha", "한화생명"), ("db", "DB손해보험"), ("swissre", "스위스리아시아"), ("kyobolp", "교보라이프플래닛생명보험"),
       ("koreanre", "코리안리재보험"), ("heungkuk", "흥국생명보험"), ("dongyang", "동양생명"), ("nhfire", "NH농협손해보험")]
NEW_KEYS = ["tier1_hybrid_recognized_eok", "binding_leg", "type_unconfirmed", "no_capital_securities", "tier1_excluded_tier2_type_eok",
            "tier1_pct_if_unconfirmed_tier2", "rule", "reason", "numerator_eok_x", "lapse_excess_item49_eok"]
JS = """() => {
  const q = (id) => document.getElementById(id);
  const c1 = q('donut-tier1'), c2 = q('donut-tier2');
  const pops = Array.from(document.querySelectorAll('#donut-row .iq-help-pop')).map(p => p.textContent.trim());
  const caps = Array.from(document.querySelectorAll('#donut-row .donut-caption')).map(c => c.firstChild.textContent.trim());
  const tip = (id, i) => { const ch = Chart.getChart(id); return ch.options.plugins.tooltip.callbacks.label({ dataIndex: i }); };
  const emp = q('donut-t1-empty');
  return { aria1: c1.getAttribute('aria-label'), aria2: c2.getAttribute('aria-label'),
    note: q('donut-note').innerText, subtitle: Array.from(document.querySelectorAll('#donut-section-panel .subtitle li')).map(l => l.textContent.trim()),
    tip1: tip('donut-tier1', 0), tip2: tip('donut-tier2', 0), caps, pops, emptyVisible: emp ? emp.offsetParent !== null : null, emptyText: emp ? emp.textContent : null,
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth };
}"""


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

    def strip_new(route):  # old-version JSON simulation
        resp = route.fetch(); d = resp.json()
        for r in d["results"]:
            for k in NEW_KEYS:
                r.pop(k, None)
        route.fulfill(response=resp, body=json.dumps(d, ensure_ascii=False), content_type="application/json")

    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            want = set(sys.argv[1:])
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
                    pg.set_default_timeout(20000)
                    if legacy:
                        pg.route(re.compile(r"kics_tier[12]_utilization\.json"), strip_new)
                    pg.goto(f"http://127.0.0.1:{port}/K-ICS.html?company={name}&iq_internal=1", wait_until="domcontentloaded")
                    pg.wait_for_timeout(4500)
                    info = pg.evaluate(JS)
                    pg.locator("#donut-section-panel").scroll_into_view_if_needed(); pg.wait_for_timeout(700)
                    pg.locator("#donut-section-panel").screenshot(path=str(OUT / f"{pref}_{vn}.png"))
                    if vn in ("desktop", "mobile") and pref in ("hanwha", "koreanre", "db"):
                        pg.locator("#donut-row .iq-help-btn").first.hover(); pg.wait_for_timeout(500)
                        pg.screenshot(path=str(OUT / f"{pref}_{vn}_help1.png"))
                        pg.locator("#donut-row .iq-help-btn").nth(1).hover(); pg.wait_for_timeout(500)
                        pg.screenshot(path=str(OUT / f"{pref}_{vn}_help2.png"))
                        box = pg.locator("#donut-tier1").bounding_box()
                        pg.mouse.move(box["x"] + box["width"] * 0.5, box["y"] + 6); pg.wait_for_timeout(500)
                        pg.locator("#donut-section-panel").screenshot(path=str(OUT / f"{pref}_{vn}_tip.png"))
                    info["errors"] = errs; info["overflow"] = info["scrollW"] > info["clientW"] + 1
                    rep[f"{pref}_{vn}"] = info; pg.close()
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (OUT / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in rep.items():
        print(k, "overflow=", v["overflow"], "err=", v["errors"][:1], "emptyVisible=", v["emptyVisible"])
        print("   aria:", v["aria1"], "|", v["aria2"])
        print("   tip:", v["tip1"], "|", v["tip2"])
        print("   pops:", v["pops"])
        print("   note:", v["note"].replace("\n", " / "))


if __name__ == "__main__":
    main()
