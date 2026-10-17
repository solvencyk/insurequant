#!/usr/bin/env python3
"""IFRS17.html section 9 (보험금 예실차비율) grouped-bar + table headless check (designer, 2026-10-12). Screens only, not deployed.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/shot_ae.py
"""
from __future__ import annotations
import json, socket, subprocess, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "designer" / "ae_section"
COS = [("samsung", "삼성생명보험"), ("hyundai", "현대해상"), ("koreanre", "코리안리재보험"), ("swissre", "스위스리아시아"),
       ("yebyeol", "예별손해보험"), ("seoulgtee", "서울보증보험"), ("fubon", "푸본현대생명보험")]
JS = """() => {
  const p = document.getElementById('sec-ae');
  const lr = document.getElementById('sec-lr');
  const nav = Array.from(document.querySelectorAll('.section-nav a')).map(a => a.textContent.trim() + (a.classList.contains('is-na') ? '(na)' : ''));
  const h2s = Array.from(document.querySelectorAll('#dashHost .panel h2')).map(h => h.textContent.trim());
  const canv = Array.from(document.querySelectorAll('#aeCharts canvas')).map(c => {
    const ch = window.Chart && Chart.getChart(c);
    return { aria: c.getAttribute('aria-label'), role: c.getAttribute('role'), w: c.clientWidth, h: c.clientHeight,
      labels: ch ? ch.data.labels : null,
      series: ch ? ch.data.datasets.map(d => [d.label, d.data]) : null,
      legend: ch ? ch.legend.legendItems.map(i => i.text) : null,
      legendBoxes: ch ? ch.legend.legendHitBoxes.map(b => [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]) : null,
      chartW: ch ? ch.width : null, chartH: ch ? ch.height : null,
      yTicks: ch ? ch.scales.y.ticks.map(t => t.label) : null,
      title: ch ? ch.options.plugins.title.text : null };
  });
  const q = document.getElementById('aeQ');
  const rows = Array.from(document.querySelectorAll('#aeTable tbody tr')).map(tr => Array.from(tr.cells).map(c => c.textContent.trim()).join(' | '));
  const hdr = Array.from(document.querySelectorAll('#aeTable thead th')).map(c => c.textContent.trim()).join(' | ');
  const share = p ? !!p.querySelector('.iq-sec-share') : null;
  const help = p ? p.querySelector('.iq-help-btn') : null;
  return { exists: !!p, hidden: p ? p.hidden : null, lrHasAe: lr ? /예실차|예상손해율|실제손해율/.test(lr.textContent) : null,
    nav, h2s, canv, hdr, rows, aeQ: q ? q.value : null, aeQopts: q ? Array.from(q.options).map(o => o.value) : [], aeQHidden: q ? q.closest('label').hidden : null,
    share, helpAria: help ? help.getAttribute('aria-label') : null,
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
    wrapOverflow: (() => { const w = document.getElementById('aeTable'); return w ? [w.scrollWidth, w.clientWidth] : null; })(),
    panelRect: p ? (() => { const r = p.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })() : null };
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
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vn, w, h in [("desktop", 1280, 900), ("mobile", 375, 812)]:
                ctx = br.new_context(viewport={"width": w, "height": h})
                for pref, name in COS:
                    ctx.add_init_script("try{localStorage.setItem('iq_notice_seen','2026-3Q')}catch(e){}"); pg = ctx.new_page(); errs = []
                    pg.on("console", lambda m, e=errs: e.append(m.text) if m.type in ("error",) else None)
                    pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                    pg.set_default_timeout(20000)
                    pg.goto(f"http://127.0.0.1:{port}/IFRS17.html?company={name}&iq_internal=1", wait_until="domcontentloaded")
                    pg.wait_for_timeout(6500)
                    info = pg.evaluate(JS)
                    if info["exists"] and not info["hidden"]:
                        pg.locator("#sec-ae").scroll_into_view_if_needed(); pg.wait_for_timeout(900)
                        pg.locator("#sec-ae").screenshot(path=str(OUT / f"{pref}_{vn}.png"))
                        if pref == "koreanre":
                            pg.hover("#sec-ae .iq-help-btn"); pg.wait_for_timeout(400)
                            pg.screenshot(path=str(OUT / f"{pref}_{vn}_help.png"))
                        # 공시시점 토글
                        tog = {}
                        if len(info["aeQopts"]) > 1:
                            for qv in info["aeQopts"]:
                                pg.evaluate("(v)=>{const s=document.getElementById('aeQ'); s.value=v; s.dispatchEvent(new Event('change'));}", qv)
                                pg.wait_for_timeout(700)
                                i2 = pg.evaluate(JS)
                                tog[qv] = {"hdr": i2["hdr"], "n": len(i2["rows"]), "labels": [c["labels"] for c in i2["canv"]]}
                        info["toggle"] = tog
                        # 툴팁(0번째 차트 첫 묶음)
                        try:
                            box = pg.locator("#aeCharts canvas").first.bounding_box()
                            pg.mouse.move(box["x"] + box["width"] * 0.30, box["y"] + box["height"] * 0.55); pg.wait_for_timeout(500)
                            pg.locator("#aeCharts").first.screenshot(path=str(OUT / f"{pref}_{vn}_tip.png"))
                        except Exception as ex:
                            info["tipErr"] = str(ex)
                    info["errors"] = errs; info["overflow"] = info["scrollW"] > info["clientW"] + 1
                    rep[f"{pref}_{vn}"] = info; pg.close()
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (OUT / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in rep.items():
        print(k, "exists=", v["exists"], "hidden=", v["hidden"], "lrHasAe=", v["lrHasAe"], "overflow=", v["overflow"], "err=", v["errors"][:1],
              "share=", v["share"], "charts=", len(v["canv"]), "wrap=", v["wrapOverflow"], "panel=", v["panelRect"])
        print("   h2:", v["h2s"][-4:], " nav:", v["nav"][-4:])
        for c in v["canv"]:
            print("   chart", c["w"], c["h"], c["title"], c["labels"], c["series"], c["yTicks"])
            print("   legend", c["legend"], c["legendBoxes"], "chartW", c["chartW"])
            print("   aria", c["aria"])
        if v["rows"]:
            print("   hdr", v["hdr"])
        for r in v["rows"]:
            print("    ", r)
        print("   toggle", v.get("toggle"), "aeQ", v["aeQopts"], "aeQHidden", v["aeQHidden"])


if __name__ == "__main__":
    main()
