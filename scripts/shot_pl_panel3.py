#!/usr/bin/env python3
"""IFRS17.html 패널 3(보험손익 구성) 헤드리스 렌더 점검 (designer, 2026-10-11).

회사 x 기준(연도/분기) x 뷰포트를 열어 (a) 패널 3 스크린샷 (b) ECharts 막대 라벨/값 (c) 표 라벨 (d) 콘솔 오류
(e) 가로 넘침을 JSON 으로 뽑는다. 화면 확인 전용이며 배포 대상이 아니다.

    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/shot_pl_panel3.py --out artifacts/designer/reinsurer_csm_amort --tag after
"""
from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
# (파일 접두어, 회사 표시명(코드 대신 이름으로 연다))
COMPANIES = [
    ("munich", "뮌헨재보험"), ("swissre", "스위스리아시아"), ("general", "제네럴재보험"),
    ("hannover", "하노버재보험"), ("rga", "알지에이리인슈어런스"), ("scor", "스코리재보험"),
    ("pacific", "퍼시픽라이프리"), ("lina", "라이나생명보험"), ("koreanre", "코리안리재보험"),
    ("samsung", "삼성생명보험"),
]
VIEWPORTS = [("desktop", 1280, 900), ("mobile", 375, 812)]

JS = """
() => {
  const el = document.getElementById('chartPl');
  const inst = (window.echarts && el) ? window.echarts.getInstanceByDom(el) : null;
  let xs = null, vals = null;
  if (inst) { const o = inst.getOption(); xs = o.xAxis[0].data; vals = o.series[0].data; }
  const tbl = document.querySelectorAll('#plTable table tbody tr');
  const rows = Array.from(tbl).map(tr => Array.from(tr.cells).map(c => c.textContent.trim()).join(' | '));
  const stub = document.getElementById('plStub');
  const cap = document.getElementById('plCap');
  return { xs, vals, rows, stub: stub && stub.style.display !== 'none' ? stub.textContent : null,
           cap: cap ? cap.textContent : null,
           scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth };
}
"""


def free_port() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="shot")
    ap.add_argument("--only", default="", help="comma separated file prefixes")
    ap.add_argument("--modes", default="year,quarter")
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--asof", default="", help="simulate: drop PL rows after this quarter (e.g. 2025.4Q) via request interception")
    a = ap.parse_args()
    out = ROOT / a.out; out.mkdir(parents=True, exist_ok=True)
    only = [x for x in a.only.split(",") if x]
    port = free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                           cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.3).close(); break
        except OSError:
            time.sleep(0.2)
    from playwright.sync_api import sync_playwright
    report = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vname, w, h in VIEWPORTS:
                ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1,
                                     color_scheme="dark" if a.dark else "light")
                for pref, name in COMPANIES:
                    if only and pref not in only:
                        continue
                    for mode in a.modes.split(","):
                        page = ctx.new_page()
                        if a.asof:
                            def _trim(route):
                                asof = a.asof
                                rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
                                k = lambda q: tuple(int(x) for x in q.replace("Q", "").split("."))
                                rows = [r for r in rows if k(r["공시분기"]) <= k(asof)]
                                route.fulfill(status=200, content_type="application/json; charset=utf-8", body=json.dumps(rows, ensure_ascii=False))
                            page.route("**/PL_breakdown.json", _trim)
                        errs = []
                        page.on("console", lambda m, errs=errs: errs.append(m.text) if m.type == "error" else None)
                        page.on("pageerror", lambda e, errs=errs: errs.append(str(e)))
                        page.goto(f"http://127.0.0.1:{port}/IFRS17.html?company={name}&iq_internal=1", wait_until="load")
                        page.wait_for_selector("#chartPl", state="attached", timeout=20000)
                        page.wait_for_timeout(1200)
                        page.evaluate("(m)=>{const s=document.getElementById('wfPeriod'); if(s){s.value=m; s.dispatchEvent(new Event('change'));}}", mode)
                        page.wait_for_timeout(1500)
                        el = page.locator("#sec-pl")
                        el.scroll_into_view_if_needed()
                        page.wait_for_timeout(900)
                        fn = f"{a.tag}_{pref}_{mode}_{vname}{'_dark' if a.dark else ''}.png"
                        el.screenshot(path=str(out / fn))
                        info = page.evaluate(JS)
                        info["errors"] = errs
                        info["overflow"] = info["scrollW"] > info["clientW"] + 1
                        report[fn] = info
                        page.close()
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (out / f"{a.tag}_report{'_dark' if a.dark else ''}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = {k: v["errors"] for k, v in report.items() if v["errors"]}
    ov = [k for k, v in report.items() if v["overflow"]]
    print("cases", len(report), "console-error cases", len(bad), "overflow cases", len(ov))
    for k, v in bad.items():
        print(" ERR", k, v[:2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
