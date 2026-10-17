#!/usr/bin/env python3
"""K-ICS.html 자본성증권 발행현황(막대 + 큼직한 셀 2개) 실데이터 점검 (2026-10-13, designer; 티켓 20261013T0030Z).

실제 `kics_capital_securities_timeline.json` 을 읽기만 한다. 단정:
  1. 모든 회사: 막대 연도별 신종·후순위 합 = JSON 의 face_eok 합, 막대 툴팁 꼬리 「추정(원장 미갱신)」은 `estimated: true` 행이 있는 해에만.
  2. DB손해보험 신종 셀: 「콜 상환 도래일 : 2030-09-01」 날짜만(금액 괄호 없음) — 제1·2회 `call_date_unconfirmed`(잔액 null).
  3. 하나손해보험 신종 셀: 최근 발행금리 「—」, 총발행액 1,999억, 막대에 2026 이 있다, 콜 상환 도래일은 기존 2029-05-14 (1,000억).
  4. 375px 도 같이(--mobile). 콘솔 오류 0, 가로 넘침 0.
Playwright·망이 없으면 SKIP(exit 0). 실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_kics_capsec_cells.py [--mobile] [--shots]
"""
from __future__ import annotations

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
OUT = ROOT / "artifacts" / "designer" / "kics_capsec_cells"

CHART = """() => { const c = Chart.getChart('capsec-chart');
  const wrap = document.getElementById('capsec-chart-wrap').style.display;
  const cell = id => document.getElementById(id).innerText;
  const out = {wrap, hy: cell('capsec-cell-hybrid'), sb: cell('capsec-cell-sub'), scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth};
  if (c) { out.labels = c.data.labels; out.h = c.data.datasets[0].data; out.s = c.data.datasets[1].data;
    out.foot = c.data.labels.map((_, i) => { c.tooltip.setActiveElements([{datasetIndex: 0, index: i}, {datasetIndex: 1, index: i}], {x: 10 + i, y: 10}); c.update('none');
      return (c.tooltip.footer || []).join('|'); });
    c.tooltip.setActiveElements([], {x: 0, y: 0}); c.update('none'); }
  return out; }"""


def main():
    ap_mobile = "--mobile" in sys.argv
    shots = "--shots" in sys.argv
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # noqa: BLE001
        print("SKIP: playwright 없음", e); return 0
    tl = json.loads((ROOT / "kics_capital_securities_timeline.json").read_text(encoding="utf-8"))["securities"]
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    bad, n = [], 0
    views = [("desktop", 1280, 900)] + ([("mobile", 375, 812)] if ap_mobile else [])
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vn, w, h in views:
                ctx = br.new_context(viewport={"width": w, "height": h}); ctx.add_init_script("try{localStorage.setItem('iq_notice_seen','2026-3Q')}catch(e){}"); pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                pg.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
                pg.goto(f"http://127.0.0.1:{port}/K-ICS.html?iq_internal=1", wait_until="domcontentloaded")
                try:
                    pg.wait_for_function("() => window.Chart && document.getElementById('company').options.length > 5", timeout=60000)
                except Exception:  # noqa: BLE001
                    print("SKIP: chart.js(망) 또는 회사 목록 실패", errs[:2]); return 0
                pg.wait_for_timeout(1500)
                code_name = pg.evaluate("() => Object.fromEntries(allData.map(x => [x['원보험사코드'], x['원수사명']]))")
                for code, name in sorted(code_name.items()):
                    pg.evaluate("(n) => { const s = document.getElementById('company'); s.value = n; s.dispatchEvent(new Event('change')); }", name)
                    pg.wait_for_timeout(200)
                    info = pg.evaluate(CHART)
                    prob = []
                    lst = tl.get(code) or []
                    if not lst:
                        if info["wrap"] == "block": prob.append("증권 없는데 차트 보임")
                    else:
                        years = sorted({int(b["issue_date"][:4]) for b in lst if b.get("issue_date")})
                        if info["labels"] != [str(y) for y in range(years[0], years[-1] + 1)]: prob.append(f"연도 {info['labels']}")
                        for i, lab in enumerate(info["labels"]):
                            hh = sum(b["face_eok"] for b in lst if b["tier"] == "hybrid" and (b.get("issue_date") or "")[:4] == lab)
                            ss = sum(b["face_eok"] for b in lst if b["tier"] == "subordinated" and (b.get("issue_date") or "")[:4] == lab)
                            if abs(info["h"][i] - hh) > 1e-6 or abs(info["s"][i] - ss) > 1e-6: prob.append(f"{lab} 막대 {info['h'][i]}/{info['s'][i]} != {hh}/{ss}")
                            est = any(b.get("estimated") is True for b in lst if (b.get("issue_date") or "")[:4] == lab)
                            if (info["foot"][i] == "추정(원장 미갱신)") != est: prob.append(f"{lab} 추정 꼬리 '{info['foot'][i]}' 기대 {est}")
                    if "하나손해" in name:
                        if "—" not in info["hy"].split("\n")[-3:][0] and "—" not in info["hy"]: prob.append("하나손해 최근 발행금리 대시 없음: " + info["hy"])
                        if "총발행액 : 1,999억" not in info["hy"]: prob.append("하나손해 총발행액 1,999억 아님: " + info["hy"])
                        if "2026" not in (info.get("labels") or []): prob.append("하나손해 2026 막대 없음")
                        if "콜 상환 도래일 : 2029-05-14 (1,000억)" not in info["hy"]: prob.append("하나손해 콜 줄: " + info["hy"])
                        if "추정(원장 미갱신)" not in (info.get("foot") or []): prob.append("하나손해 추정 꼬리 없음")
                    if "DB손해" in name:
                        if "콜 상환 도래일 : 2030-09-01" not in info["hy"] or "2030-09-01 (" in info["hy"]: prob.append("DB손해 신종 콜 줄(날짜만 아님): " + info["hy"])
                    if info["scrollW"] > info["clientW"] + 1: prob.append("가로 넘침")
                    if errs: prob.append(f"콘솔 {errs[:2]}"); errs.clear()
                    if name and any(k in name for k in ("DB손해", "하나손해")):
                        print(f"[{vn}] {name} hybrid: {info['hy'].replace(chr(10), ' / ')}")
                        print(f"[{vn}] {name} foot: {info.get('foot')}")
                        if shots:
                            OUT.mkdir(parents=True, exist_ok=True)
                            pg.locator("#sec-capsec").scroll_into_view_if_needed(); pg.wait_for_timeout(400)
                            pg.locator("#sec-capsec").screenshot(path=str(OUT / f"{name}_{vn}.png"))
                    n += 1
                    if prob: bad.append((vn, name, prob))
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"checked {n}, violations {len(bad)}")
    for b in bad:
        print("  ", b[0], b[1])
        for p in b[2]: print("      -", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
