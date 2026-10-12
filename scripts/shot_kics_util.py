#!/usr/bin/env python3
"""K-ICS.html utilization donuts + forward outlook headless check (designer, 2026-10-12). Screens only, not deployed.

Reads the real kics_tier1_utilization.json / kics_tier2_utilization.json / kics_forward_capital.json and compares what the page drew
(donut dataset + aria-label, forward chart series, tooltip extra lines) against those JSON values directly.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/shot_kics_util.py [desktop|mobile|dark|legacy ...]
"""
from __future__ import annotations
import json, re, socket, subprocess, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "designer" / "kics_util_restore"
COS = ["한화생명", "메리츠화재해상보험", "DB손해보험", "하나손해보험", "하나생명보험", "교보생명보험", "코리안리재보험",
       "스위스리아시아", "교보라이프플래닛생명보험", "동양생명"]


def jl(n):
    return json.loads((ROOT / n).read_text(encoding="utf-8"))


T1 = {r["company"]: r for r in jl("kics_tier1_utilization.json")["results"]}
T2 = {r["company"]: r for r in jl("kics_tier2_utilization.json")["results"]}
FW = {r["insurer_name"]: r for r in jl("kics_forward_capital.json")}

JS = """() => {
  const q = (id) => document.getElementById(id);
  const d1 = window.Chart && Chart.getChart('donut-tier1'), d2 = Chart.getChart('donut-tier2'), fc = Chart.getChart('forward-chart');
  const nav = Array.from(document.querySelectorAll('.section-nav a')).map(a => a.textContent.trim() + (document.getElementById((a.getAttribute('href') || '').slice(1)) ? '' : ' (DEAD)'));
  const ids = ['donut-section-panel', 'sec-capsec', 'sec-sens', 'sec-dur', 'sec-forward'];
  const order = ids.map(i => [i, Math.round(q(i).getBoundingClientRect().top + scrollY)]);
  const gap = (a, b) => Math.round(q(b).getBoundingClientRect().top - q(a).getBoundingClientRect().bottom);
  return {
    d1: d1 ? d1.data.datasets[0].data : null, d2: d2 ? d2.data.datasets[0].data : null,
    a1: q('donut-tier1').getAttribute('aria-label'), a2: q('donut-tier2').getAttribute('aria-label'),
    note: q('donut-note').innerText, quarter: q('capsecQuarter').innerText,
    empty: q('donut-t1-empty') ? !q('donut-t1-empty').hidden : null,
    t1pop: q('help-capsec-t1').innerText, t2pop: q('help-capsec-t2').innerText,
    rowDisplay: q('donut-row').style.display, phDisplay: q('donut-placeholder').style.display,
    fwWrap: q('forward-chart-wrap').style.display, fwPh: q('forward-placeholder').style.display, fwPhText: q('forward-placeholder').innerText,
    fwNote: q('forward-note').innerText,
    fwLabels: fc ? fc.data.labels : null, fwRatio: fc ? fc.data.datasets[0].data : null,
    fwBasic: fc ? fc.data.datasets[1]._originalBasic : null,
    nav, order, gaps: [gap('donut-section-panel', 'sec-capsec'), gap('sec-capsec', 'sec-sens'), gap('sec-dur', 'sec-forward')],
    shares: Array.from(document.querySelectorAll('[data-share-section]')).map(e => e.getAttribute('data-share-section')),
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
    capsecWrap: q('capsec-chart-wrap').style.display, capsecCells: !q('capsec-cells').hidden };
}"""

WAIT = """() => document.getElementById('donut-placeholder').style.display === 'none'
  && (document.getElementById('forward-placeholder').style.display === 'none' || document.getElementById('forward-placeholder').innerText.length > 0)
  && window.Chart && Chart.getChart('donut-tier1') && Chart.getChart('donut-tier2')"""

TIP = """() => { const c = Chart.getChart('forward-chart'); const t = c.tooltip;
  return t && t.body ? t.body.map(b => b.lines.concat(b.after || [])) : null; }"""


def exp_aria(base, row, na=None):
    p = row.get("utilization_pct") if row else None
    if p is None:
        return f"{base} {na or '데이터 없음'}"
    if p > 100:
        return f"{base} 100% 초과 ({p:.1f}%)"
    return f"{base} {p:.1f}%"


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
    rep, bad = {}, []
    want = set(sys.argv[1:])

    def strip(route):  # old-version JSON simulation: drop every new field the page reads
        d = json.loads((ROOT / route.request.url.rsplit("/", 1)[1].split("?")[0]).read_text(encoding="utf-8"))
        rows = d["results"] if isinstance(d, dict) else d
        for r in rows:
            for k in ("type_unconfirmed", "tier1_pct_if_unconfirmed_tier2", "no_capital_securities", "binding_leg", "rule", "reason",
                      "baseline_basis_flag", "baseline_basis_note", "securities_summary", "tier1_excluded_tier2_type_eok"):
                r.pop(k, None)
            for p in r.get("projections", []) or []:
                for k in ("basic_ratio_by_type_pct", "basic_ratio_if_tier2_type_pct"):
                    p.pop(k, None)
        route.fulfill(status=200, body=json.dumps(d, ensure_ascii=False), content_type="application/json")

    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vn, w, h, scheme, legacy in [("desktop", 1280, 900, "light", False), ("mobile", 375, 812, "light", False),
                                             ("dark", 1280, 900, "dark", False), ("legacy", 1280, 900, "light", True)]:
                if want and vn not in want:
                    continue
                ctx = br.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
                for name in COS:
                    if legacy and name not in ("한화생명", "하나생명보험"):
                        continue
                    pg = ctx.new_page(); errs = []
                    pg.on("console", lambda m, e=errs: e.append(m.text) if m.type in ("error",) else None)
                    pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                    pg.set_default_timeout(60000)
                    if legacy:
                        pg.route(re.compile(r"kics_(tier[12]_utilization|forward_capital)\.json"), strip)
                    pg.goto(f"http://127.0.0.1:{port}/K-ICS.html?company={name}&iq_internal=1", wait_until="domcontentloaded")
                    try:
                        pg.wait_for_function(WAIT, timeout=60000, polling=500)
                    except Exception:
                        print("WAIT FAILED", name, vn, errs[:3]); raise
                    pg.wait_for_timeout(2500)
                    info = pg.evaluate(JS)
                    t1, t2, fw = T1.get(name), T2.get(name), FW.get(name)
                    prob = []
                    if not legacy:
                        e1 = exp_aria("기본자본 자본증권 인정한도 소진율", t1)
                        na2 = (t2.get("reason") or "경과조치 표 미공시") if (t2 and t2.get("utilization_pct") is None) else None
                        e2 = exp_aria("보완자본 한도 소진율", t2, na=na2)
                        if info["a1"] != e1: prob.append(f"aria1 {info['a1']!r} != {e1!r}")
                        if info["a2"] != e2: prob.append(f"aria2 {info['a2']!r} != {e2!r}")
                        for key, row in (("d1", t1), ("d2", t2)):
                            p = row.get("utilization_pct") if row else None
                            fill = 0 if p is None else min(max(p, 0), 100)
                            exp = [fill, 100 - fill] if p is not None else [0, 100]
                            if info[key] is None or any(abs(a - b) > 1e-6 for a, b in zip(info[key], exp)): prob.append(f"{key} {info[key]} != {exp}")
                    if fw and fw.get("status") == "ok":
                        pr = fw["projections"]
                        if info["fwLabels"] != [str(p["year"]) for p in pr]: prob.append(f"fw years {info['fwLabels']}")
                        if info["fwRatio"] != [p["ratio_pct"] for p in pr]: prob.append(f"fw ratio {info['fwRatio']}")
                        if info["fwBasic"] != [p["basic_ratio_pct"] for p in pr]: prob.append(f"fw basic {info['fwBasic']}")
                    elif fw:
                        if info["fwWrap"] != "none" or fw["exclusion_reason"] not in info["fwPhText"]: prob.append("fw excluded text")
                    if info["scrollW"] > info["clientW"] + 1: prob.append(f"overflow {info['scrollW']}>{info['clientW']}")
                    if errs: prob.append(f"errors {errs[:2]}")
                    if any("DEAD" in n for n in info["nav"]): prob.append("dead chip")
                    if not (info["capsecWrap"] == "block" and info["capsecCells"]) and not legacy and name not in ("스위스리아시아", "교보라이프플래닛생명보험"):  # no bonds on file -> capsec chart hidden by design
                        prob.append(f"capsec lost wrap={info['capsecWrap']} cells={info['capsecCells']}")
                    tag = f"{name}_{vn}"
                    for sec, nm in (("donut-section-panel", "donut"), ("sec-forward", "fw")):
                        pg.locator("#" + sec).scroll_into_view_if_needed(); pg.wait_for_timeout(500)
                        pg.locator("#" + sec).screenshot(path=str(OUT / f"{tag}_{nm}.png"))
                    if vn in ("desktop", "mobile", "legacy") and name in ("하나생명보험", "한화생명"):
                        pg.locator("#forward-chart").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                        box = pg.locator("#forward-chart").bounding_box()
                        pg.mouse.move(box["x"] + box["width"] * 0.88, box["y"] + box["height"] * 0.5); pg.wait_for_timeout(700)
                        pg.screenshot(path=str(OUT / f"{tag}_fwtip.png"))
                        info["tip"] = pg.evaluate(TIP)
                    info["problems"] = prob
                    if prob: bad.append((vn, name, prob))
                    rep[tag] = info; pg.close()
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (OUT / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in rep.items():
        print(k, "| d1", v["d1"], "d2", v["d2"], "| empty", v["empty"], "| fwWrap", v["fwWrap"], "| problems", v["problems"])
        print("    note:", v["note"].replace("\n", " / "))
        if v.get("tip"): print("    tip:", v["tip"])
    k0 = next(iter(rep.values()))
    print("nav:", k0["nav"]); print("order:", k0["order"]); print("gaps:", k0["gaps"]); print("shares:", k0["shares"]); print("quarter:", k0["quarter"])
    print("PROBLEMS:", len(bad))
    for b in bad: print("  ", b)


if __name__ == "__main__":
    main()
