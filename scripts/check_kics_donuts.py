#!/usr/bin/env python3
"""K-ICS.html 소진율 도넛·숫자 줄 47사 전수 점검 (2026-10-13, designer; 티켓 20261013T0030Z).

`kics_tier1_utilization.json`·`kics_tier2_utilization.json` 을 읽기만 하고, 페이지가 그린 값을 JSON 에서 직접 계산한 기대값과 대조한다.
  - 도넛 데이터셋·aria-label (기본자본 자본증권 / 보완자본, 100%+ 표기, NA 사유)
  - 숫자 줄 「기본자본 자본증권 X억원 / 인정한도 Y억원」(Y = tier1_hybrid_limit_eok; 결속 갈래가 없는 33사는 SCR x 10%),
    「보완자본 한도 적용 전 X억원 / 보완자본 한도 Y억원」, 「경과조치 기발행 후순위 Z억원」(Z = grandfathered_subordinated_eok > 0 일 때만)
  - 콘솔 오류 0, 가로 넘침 0
Playwright·망이 없으면 SKIP(exit 0). 실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_kics_donuts.py [--mobile] [--dark]
"""
from __future__ import annotations

import json
import re
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


def jl(n):
    return json.loads((ROOT / n).read_text(encoding="utf-8"))


def eok(v):
    """fmtEokInt: 반올림(+0.5 올림) + 천단위 콤마 + 음수 △."""
    if v is None:
        return "-"
    r = int(abs(v) + 0.5)
    return ("△" if v < 0 else "") + f"{r:,}"


def aria(base, pct, na=None):
    if pct is None:
        return f"{base} {na or '데이터 없음'}"
    return f"{base} 100% 초과 ({pct:.1f}%)" if pct > 100 else f"{base} {pct:.1f}%"


PICK = """() => { const D = id => { const c = Chart.getChart(id); return c ? c.data.datasets[0].data : null; };
  return { d1: D('donut-tier1'), d2: D('donut-tier2'), a1: document.getElementById('donut-tier1').getAttribute('aria-label'),
    a2: document.getElementById('donut-tier2').getAttribute('aria-label'), note: document.getElementById('donut-note').innerText,
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth }; }"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # noqa: BLE001
        print("SKIP: playwright 없음", e); return 0
    t1 = {r["code"]: r for r in jl("kics_tier1_utilization.json")["results"]}
    t2 = {r["code"]: r for r in jl("kics_tier2_utilization.json")["results"]}
    views = [("desktop", 1280, 900, "light")] + ([("mobile", 375, 812, "light")] if "--mobile" in sys.argv else []) + ([("dark", 1280, 900, "dark")] if "--dark" in sys.argv else [])
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    bad, n, lim10 = [], 0, 0
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vn, w, h, scheme in views:
                ctx = br.new_context(viewport={"width": w, "height": h}, color_scheme=scheme); ctx.add_init_script("try{localStorage.setItem('iq_notice_seen','2026-3Q')}catch(e){}"); pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                pg.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
                pg.goto(f"http://127.0.0.1:{port}/K-ICS.html?iq_internal=1", wait_until="domcontentloaded")
                try:
                    pg.wait_for_function("() => window.Chart && document.getElementById('company').options.length > 5", timeout=60000)
                except Exception:  # noqa: BLE001
                    print("SKIP: chart.js(망) 실패", errs[:2]); return 0
                pg.wait_for_timeout(1500)
                code_name = pg.evaluate("() => Object.fromEntries(allData.map(x => [x['원보험사코드'], x['원수사명']]))")
                for code, name in sorted(code_name.items()):
                    a, b = t1.get(code), t2.get(code)
                    if a is None and b is None:
                        continue
                    pg.evaluate("(n) => { const s = document.getElementById('company'); s.value = n; s.dispatchEvent(new Event('change')); }", name)
                    pg.wait_for_timeout(200)
                    info = pg.evaluate(PICK)
                    note = re.sub(r"\s+", " ", info["note"].replace("\xa0", " "))
                    prob = []
                    for key, row, base, na in (("1", a, "기본자본 자본증권 인정한도 소진율", None), ("2", b, "보완자본 한도 소진율", None)):
                        pct = row.get("utilization_pct") if row else None
                        if key == "2" and row and pct is None:
                            na = row.get("reason") or "경과조치 표 미공시"
                        if info["a" + key] != aria(base, pct, na): prob.append(f"aria{key} {info['a' + key]!r} != {aria(base, pct, na)!r}")
                        fill = 0 if pct is None else min(max(pct, 0), 100)
                        exp = [fill, 100 - fill] if pct is not None else [0, 100]
                        if info["d" + key] is None or any(abs(x - y) > 1e-6 for x, y in zip(info["d" + key], exp)): prob.append(f"d{key} {info['d' + key]} != {exp}")
                    if a:
                        rec = a["tier1_hybrid_recognized_eok"] if a.get("tier1_hybrid_recognized_eok") is not None else a.get("tier1_hybrid_issued_eok")
                        want = f"기본자본 자본증권 {eok(rec)}억원 / 인정한도 {eok(a['tier1_hybrid_limit_eok'])}억원"
                        if want not in note: prob.append(f"기본자본 줄 없음: {want!r} in {note[:140]!r}")
                        gf = a.get("tier1_grandfathered_hybrid_eok") or 0
                        has_gf = "경과조치 기발행분" in note
                        want_gf = gf > 0 and a.get("binding_leg") in ("legacy_15", None)
                        if has_gf != want_gf: prob.append(f"기발행분 줄 has={has_gf} want={want_gf}")
                        if a.get("scr_eok") and abs(a["tier1_hybrid_limit_eok"] - a["scr_eok"] * 0.10) <= 0.06 * 1 + a["scr_eok"] * 0.0005: lim10 += 1
                    if b:
                        num = "—" if b.get("numerator_eok") is None else eok(b["numerator_eok"]) + "억원"
                        want = f"보완자본 한도 적용 전 {num} / 보완자본 한도 {eok(b['tier2_limit_eok'])}억원"
                        if want not in note: prob.append(f"보완자본 줄 없음: {want!r} in {note[:200]!r}")
                        g = b.get("grandfathered_subordinated_eok") or 0
                        has = "경과조치 기발행 후순위" in note
                        if has != (g > 0): prob.append(f"기발행 후순위 줄 has={has} want={g > 0}")
                        if g > 0 and f"경과조치 기발행 후순위 {eok(g)}억원" not in note: prob.append(f"기발행 후순위 값 {eok(g)} 불일치: {note[:260]!r}")
                    if info["scrollW"] > info["clientW"] + 1: prob.append(f"가로 넘침 {info['scrollW']}>{info['clientW']}")
                    if errs: prob.append(f"콘솔 {errs[:2]}"); errs.clear()
                    n += 1
                    if prob: bad.append((vn, name, prob))
                ctx.close()
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"checked {n} (view x company), 인정한도 = SCR x 10% 인 (view x company) {lim10}, violations {len(bad)}")
    for v in bad:
        print("  ", v[0], v[1])
        for p in v[2]: print("      -", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
