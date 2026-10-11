#!/usr/bin/env python3
"""IFRS17.html section 8 claims actual-vs-expected table headless check (designer, 2026-10-12). Screens only, not deployed."""
from __future__ import annotations
import json, socket, subprocess, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "designer" / "lr_ae"
COS = [("swissre", "스위스리아시아"), ("munich", "뮌헨재보험"), ("samsung", "삼성생명보험"), ("koreanre", "코리안리재보험"),
       ("yebyeol", "예별손해보험"), ("kakaopay", "카카오페이손해보험"), ("seoulgtee", "서울보증보험"), ("mybrown", "마이브라운생명보험")]
JS = """() => {
  const box=document.getElementById('lrAeBox'); const t=document.querySelectorAll('#lrAeTable tbody tr');
  const rows=Array.from(t).map(tr=>Array.from(tr.cells).map(c=>c.textContent.trim()).join(' | '));
  const hdr=Array.from(document.querySelectorAll('#lrAeTable thead th')).map(c=>c.textContent.trim()).join(' | ');
  const q=document.getElementById('lrQ');
  return {hidden: box? box.hidden : null, hdr, rows, lrQ: q? q.value:null, qopts: q? Array.from(q.options).map(o=>o.value):[],
          scrollW:document.documentElement.scrollWidth, clientW:document.documentElement.clientWidth,
          wrapOverflow:(()=>{const w=document.getElementById('lrAeTable'); return w? [w.scrollWidth,w.clientWidth]:null})()};
}"""
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try: socket.create_connection(("127.0.0.1", port), timeout=0.3).close(); break
        except OSError: time.sleep(0.2)
    from playwright.sync_api import sync_playwright
    rep = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vn, w, h in [("desktop", 1280, 900), ("mobile", 375, 812)]:
                ctx = br.new_context(viewport={"width": w, "height": h})
                for pref, name in COS:
                    pg = ctx.new_page(); errs = []
                    pg.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" else None)
                    pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                    pg.set_default_timeout(20000); pg.goto(f"http://127.0.0.1:{port}/IFRS17.html?company={name}&iq_internal=1", wait_until="domcontentloaded")
                    pg.wait_for_timeout(6000)
                    if pg.locator("#sec-lr").count() == 0:
                        rep[f"{pref}_{vn}"] = {"missing_sec_lr": True, "hint": pg.evaluate("()=>(document.getElementById('emptyHint')||{}).textContent"), "errors": errs}
                        print(pref, vn, "NO #sec-lr", errs[:2]); pg.close(); continue
                    info = pg.evaluate(JS)
                    pg.locator("#sec-lr").scroll_into_view_if_needed(); pg.wait_for_timeout(600)
                    if info["hidden"] is False:
                        pg.locator("#lrAeBox").screenshot(path=str(OUT / f"{pref}_{vn}.png"))
                    # toggle through quarters
                    tog = {}
                    for qv in info["qopts"]:
                        pg.evaluate("(v)=>{const s=document.getElementById('lrQ'); s.value=v; s.dispatchEvent(new Event('change'));}", qv)
                        pg.wait_for_timeout(500)
                        i2 = pg.evaluate(JS); tog[qv] = {"hidden": i2["hidden"], "hdr": i2["hdr"], "n": len(i2["rows"])}
                    info["toggle"] = tog; info["errors"] = errs; info["overflow"] = info["scrollW"] > info["clientW"] + 1
                    rep[f"{pref}_{vn}"] = info; pg.close()
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (OUT / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in rep.items():
        if v.get("missing_sec_lr"): continue
        print(k, "hidden=", v["hidden"], "hdr=", v["hdr"], "overflow=", v["overflow"], "err=", v["errors"][:1], "wrap=", v["wrapOverflow"])
        for r in v["rows"]: print("   ", r)
        print("    toggle", v["toggle"])
if __name__ == "__main__":
    main()
