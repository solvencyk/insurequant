#!/usr/bin/env python3
"""업데이트 안내 팝업 회귀 검사 (2026-10-18 신설, designer).

theme.js 의 mountNotice()(NOTICE 설정 객체)가 실제 브라우저에서 약속대로 도는지 본다.
  1. 첫 방문에 뜬다 — role=dialog · aria-modal · 제목 연결 · 네 줄 문구(공시 기한 원문 그대로) · 초점이 대화상자 안.
  2. 닫으면 localStorage iq_notice_seen=<id> 가 남고 새로고침해도 안 뜬다. 저장소를 지우면 다시 뜬다.
  3. localStorage 접근이 예외를 던져도 뜬다(방문마다 뜸). 닫기도 동작한다.
  4. Esc · 닫기 버튼 · 백드롭 클릭으로 닫힌다. 패널 안에서 눌러 백드롭에서 떼면 안 닫힌다.
  5. 닫으면 초점이 열기 전 요소로 돌아간다. Tab/Shift+Tab 은 대화상자 안에서만 돈다.
  6. 1280/375 x 라이트/다크: 가로 넘침 없음 · 패널이 뷰포트 안 · 닫기 타깃 44px 이상 · 글자 대비 4.5:1 이상 ·
     떠 있는 동안 본문 폭이 그대로(레이아웃 시프트 없음).
  7. prefers-reduced-motion 이면 애니메이션 없음. hideAfter 가 지난 날짜면 안 뜬다.
  8. jp/·privacy 에는 안 뜬다. 팝업을 열고 닫는 동안 외부로 나가는 요청이 0(분석·수집기 호출 없음).
  9. 콘솔 오류 0.

실행(저장소 루트): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_notice_popup.py [--out DIR]
종료코드 0 = 통과 · 1 = 위반 · 브라우저가 없으면 SKIP(exit 0)이며 "안 돌렸다" 로 인쇄한다.
"""
from __future__ import annotations

import argparse
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
PERIOD = "2026-3Q"
LINES = [
    "2026 3분기 DART 공시 기한 2026년 11월 13일",
    "2026 3분기 경영공시 기한 2026년 11월 30일",
    "2026년 3분기 보험개발원 매출 현황 미정",
    "공시 업로드 후 2일-3일 내외 소요 예정",
]
PAGES = ["index.html", "K-ICS.html", "IFRS17.html", "공시보고서.html", "compare.html"]
NEGATIVE = ["privacy.html", "jp/index.html"]
VIEWPORTS = [("desktop", 1280, 900), ("mobile", 375, 812)]
BLOCK = re.compile(r"google-analytics\.com|googletagmanager\.com|script\.google\.com|script\.googleusercontent\.com")

# 열기 전에 초점을 둘 요소를 만든다(theme.js 의 DOMContentLoaded 보다 먼저 등록된다)
PREV_JS = """document.addEventListener('DOMContentLoaded', function(){
  var b = document.createElement('button'); b.id = 'testPrev'; b.textContent = 'prev'; b.style.cssText = 'position:fixed;left:0;bottom:0;z-index:1';
  document.body.appendChild(b); b.focus();
});"""
THROW_JS = """(function(){
  var f = function(){ throw new Error('storage blocked'); };
  try{ Storage.prototype.getItem = f; Storage.prototype.setItem = f; Storage.prototype.removeItem = f; }catch(e){}
})();"""

PROBE_JS = """() => {
  const d = document.getElementById('iqNotice');
  if (!d) return { shown: false };
  const p = d.querySelector('[role=dialog]');
  const lum = (c) => { const m = c.match(/[\\d.]+/g).slice(0, 3).map(Number).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]; };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const bg = getComputedStyle(p).backgroundColor;
  const q = (s) => p.querySelector(s);
  const r = p.getBoundingClientRect(), xb = q('.iq-modal-close').getBoundingClientRect(), ob = q('.iq-notice-ok').getBoundingClientRect();
  const okS = getComputedStyle(q('.iq-notice-ok'));
  return {
    shown: true, role: p.getAttribute('role'), modal: p.getAttribute('aria-modal'),
    labelled: (document.getElementById(p.getAttribute('aria-labelledby')) || {}).textContent || '',
    items: [...p.querySelectorAll('li')].map(l => l.textContent),
    inside: p.contains(document.activeElement), active: document.activeElement && (document.activeElement.className || document.activeElement.id),
    sw: document.documentElement.scrollWidth, iw: window.innerWidth, bodyW: document.body.getBoundingClientRect().width,
    rect: [r.left, r.right, r.top, r.bottom], vh: window.innerHeight,
    x: [xb.width, xb.height], ok: [ob.width, ob.height],
    cText: ratio(getComputedStyle(q('li')).color, bg), cTitle: ratio(getComputedStyle(q('h2')).color, bg),
    cClose: ratio(getComputedStyle(q('.iq-modal-close')).color, bg), cBtn: ratio(okS.color, okS.backgroundColor),
    anim: getComputedStyle(d).animationName, seen: (() => { try { return localStorage.getItem('iq_notice_seen'); } catch (e) { return 'ERR'; } })(),
  };
}"""


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start_server(port: int) -> subprocess.Popen:
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                            cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.3).close()
            return proc
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("http.server 가 시작되지 않았습니다")


def stop_server(proc: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        proc.terminate()


def run(args) -> int:
    from playwright.sync_api import sync_playwright

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    port = free_port()
    srv = start_server(port)
    fails: list[str] = []
    n_checks = [0]

    def check(cond: bool, msg: str) -> None:
        n_checks[0] += 1
        if not cond:
            fails.append(msg)

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                try:
                    browser = p.chromium.launch(headless=True, channel="msedge")
                except Exception as e:  # 브라우저 없음
                    print("SKIP: 브라우저를 띄울 수 없어 안 돌렸다 (" + str(e).splitlines()[0] + ")")
                    return 0

            def new(vw, vh, scheme="light", reduced=False, init=(), mobile=False):
                ctx = browser.new_context(viewport={"width": vw, "height": vh}, color_scheme=scheme,
                                          reduced_motion="reduce" if reduced else "no-preference",
                                          has_touch=mobile, is_mobile=mobile)
                for s in init:
                    ctx.add_init_script(s)
                pg = ctx.new_page()
                errs: list[str] = []
                reqs: list[str] = []
                # 우리가 막은 분석 요청(ERR_FAILED)과 회사망 전송 오류(ERR_CONNECTION_RESET 등 외부 CDN)는 페이지 오류가 아니다. 404 등 그 밖의 로드 실패는 그대로 잡는다.
                pg.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" and "net::ERR_" not in m.text else None)
                pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                pg.on("request", lambda r, q=reqs: q.append(r.url))
                pg.route(BLOCK, lambda r: r.abort())
                return ctx, pg, errs, reqs

            def url(name, extra=""):
                return f"http://127.0.0.1:{port}/{name}?iq_internal=1{extra}"

            def go(pg, name):
                pg.goto(url(name), wait_until="load", timeout=60000)
                pg.wait_for_timeout(500)

            def offsite(reqs):
                return [u for u in reqs if not u.startswith(f"http://127.0.0.1:{port}")]

            # ---- 1~2, 6: 5개 페이지 x 2 뷰포트 x 라이트/다크 -------------------------------------------
            for vname, vw, vh in VIEWPORTS:
                for scheme in ("light", "dark"):
                    for name in PAGES:
                        tag = f"{name}|{vname}|{scheme}"
                        ctx, pg, errs, reqs = new(vw, vh, scheme, init=[PREV_JS], mobile=(vname == "mobile"))
                        go(pg, name)
                        s = pg.evaluate(PROBE_JS)
                        check(s["shown"], f"[{tag}] 첫 방문인데 안 뜸")
                        if not s["shown"]:
                            ctx.close()
                            continue
                        check(s["role"] == "dialog" and s["modal"] == "true", f"[{tag}] role/aria-modal")
                        check(s["labelled"] == "2026 3분기 업데이트 안내", f"[{tag}] aria-labelledby 제목 {s['labelled']!r}")
                        check(s["items"] == LINES, f"[{tag}] 네 줄 문구가 원문과 다름 {s['items']}")
                        check(s["inside"], f"[{tag}] 초점이 대화상자 밖 {s['active']}")
                        check(s["sw"] <= s["iw"], f"[{tag}] 가로 넘침 {s['sw']}>{s['iw']}")
                        r = s["rect"]
                        check(r[0] >= 0 and r[1] <= s["iw"] and r[2] >= 0 and r[3] <= s["vh"], f"[{tag}] 패널이 뷰포트 밖 {r}")
                        check(s["x"][0] >= 44 and s["x"][1] >= 44 and s["ok"][1] >= 44, f"[{tag}] 닫기 타깃 44px 미만 {s['x']} {s['ok']}")
                        for k, lab in (("cText", "본문"), ("cTitle", "제목"), ("cClose", "닫기 X"), ("cBtn", "닫기 버튼")):
                            check(s[k] >= 4.5, f"[{tag}] 대비 {lab} {s[k]:.2f}")
                        before_w = s["bodyW"]
                        pg.screenshot(path=str(out / f"notice_{Path(name).stem}_{vname}_{scheme}.png"))
                        n_req = len(reqs)
                        pg.wait_for_timeout(300)
                        base = len(offsite(reqs))
                        pg.keyboard.press("Escape")
                        pg.wait_for_timeout(200)
                        a = pg.evaluate("() => ({ shown: !!document.getElementById('iqNotice'), bodyW: document.body.getBoundingClientRect().width, active: document.activeElement && document.activeElement.id, seen: localStorage.getItem('iq_notice_seen') })")
                        check(not a["shown"], f"[{tag}] Esc 로 안 닫힘")
                        check(abs(a["bodyW"] - before_w) < 0.5, f"[{tag}] 열림/닫힘 사이 본문 폭 변화 {before_w}->{a['bodyW']}")
                        check(a["active"] == "testPrev", f"[{tag}] 초점 복귀 실패 {a['active']!r}")
                        check(a["seen"] == PERIOD, f"[{tag}] 닫았는데 저장값 {a['seen']!r}")
                        check(len(offsite(reqs)) == base, f"[{tag}] 닫는 동안 외부 요청 발생 {offsite(reqs)[base:]}")
                        pg.reload(wait_until="load")
                        pg.wait_for_timeout(400)
                        check(not pg.evaluate("() => !!document.getElementById('iqNotice')"), f"[{tag}] 닫은 뒤 새로고침에 또 뜸")
                        pg.evaluate("() => localStorage.clear()")
                        pg.reload(wait_until="load")
                        pg.wait_for_timeout(400)
                        check(pg.evaluate("() => !!document.getElementById('iqNotice')"), f"[{tag}] 저장소를 지웠는데 안 뜸")
                        check(not errs, f"[{tag}] 콘솔 오류 {errs[:3]}")
                        ctx.close()

            # ---- 4~5: 닫는 방법 · 초점 · Tab 가둠 (데스크톱 index) -------------------------------------
            ctx, pg, errs, reqs = new(1280, 900, init=[PREV_JS])
            go(pg, "index.html")
            for _ in range(6):
                pg.keyboard.press("Tab")
                check(pg.evaluate("() => document.getElementById('iqNotice').querySelector('[role=dialog]').contains(document.activeElement)"), "[tab] Tab 이 대화상자를 벗어남")
            for _ in range(6):
                pg.keyboard.press("Shift+Tab")
                check(pg.evaluate("() => document.getElementById('iqNotice').querySelector('[role=dialog]').contains(document.activeElement)"), "[tab] Shift+Tab 이 대화상자를 벗어남")
            pg.mouse.click(5, 5)   # 백드롭
            pg.wait_for_timeout(150)
            check(not pg.evaluate("() => !!document.getElementById('iqNotice')"), "[backdrop] 백드롭 클릭으로 안 닫힘")
            check(pg.evaluate("() => document.activeElement && document.activeElement.id") == "testPrev", "[backdrop] 초점 복귀 실패")
            pg.evaluate("() => localStorage.clear()"); pg.reload(wait_until="load"); pg.wait_for_timeout(400)
            box = pg.locator(".iq-notice-panel").bounding_box()
            pg.mouse.move(box["x"] + 20, box["y"] + 20); pg.mouse.down(); pg.mouse.move(5, 5); pg.mouse.up()
            pg.wait_for_timeout(150)
            check(pg.evaluate("() => !!document.getElementById('iqNotice')"), "[drag] 패널 안에서 눌러 백드롭에서 떼면 안 닫혀야 함")
            pg.locator(".iq-notice-panel .iq-modal-close").click(); pg.wait_for_timeout(150)
            check(not pg.evaluate("() => !!document.getElementById('iqNotice')"), "[x] X 버튼으로 안 닫힘")
            pg.evaluate("() => localStorage.clear()"); pg.reload(wait_until="load"); pg.wait_for_timeout(400)
            pg.locator(".iq-notice-ok").click(); pg.wait_for_timeout(150)
            check(not pg.evaluate("() => !!document.getElementById('iqNotice')"), "[ok] 닫기 버튼으로 안 닫힘")
            check(not errs, f"[interact] 콘솔 오류 {errs[:3]}")
            ctx.close()

            # ---- 3: 저장소가 예외를 던질 때 -----------------------------------------------------------
            ctx, pg, errs, reqs = new(1280, 900, init=[THROW_JS])
            go(pg, "K-ICS.html")
            check(pg.evaluate("() => !!document.getElementById('iqNotice')"), "[blocked] 저장소 예외인데 안 뜸")
            pg.keyboard.press("Escape"); pg.wait_for_timeout(150)
            check(not pg.evaluate("() => !!document.getElementById('iqNotice')"), "[blocked] 저장소 예외일 때 닫기 실패")
            pg.reload(wait_until="load"); pg.wait_for_timeout(400)
            check(pg.evaluate("() => !!document.getElementById('iqNotice')"), "[blocked] 저장소 예외면 방문마다 떠야 함")
            check(not errs, f"[blocked] 콘솔 오류 {errs[:3]}")
            ctx.close()

            # ---- 7: reduced motion · 기한 지남 ---------------------------------------------------------
            ctx, pg, errs, reqs = new(1280, 900, reduced=True)
            go(pg, "index.html")
            check(pg.evaluate(PROBE_JS)["anim"] == "none", "[reduced] 애니메이션이 남아 있음")
            ctx.close()
            ctx, pg, errs, reqs = new(1280, 900)
            pg.clock.set_fixed_time("2027-01-02T09:00:00")
            go(pg, "index.html")
            check(not pg.evaluate("() => !!document.getElementById('iqNotice')"), "[expired] hideAfter 지났는데 뜸")
            ctx.close()
            ctx, pg, errs, reqs = new(1280, 900)
            pg.clock.set_fixed_time("2026-12-31T23:00:00")
            go(pg, "index.html")
            check(pg.evaluate("() => !!document.getElementById('iqNotice')"), "[lastday] hideAfter 당일에는 떠야 함")
            ctx.close()

            # ---- 8: 대상 아닌 페이지 --------------------------------------------------------------------
            for name in NEGATIVE:
                ctx, pg, errs, reqs = new(1280, 900)
                go(pg, name)
                check(not pg.evaluate("() => !!document.getElementById('iqNotice')"), f"[{name}] 대상 아닌 페이지에 뜸")
                ctx.close()
            browser.close()
    finally:
        stop_server(srv)

    src = (ROOT / "theme.js").read_text(encoding="utf-8")
    m = re.search(r"function mountNotice\(\)\{.*?\n  \}\n", src, re.S)
    check(bool(m) and not re.search(r"shLog|IQ_FORMS|gtag|fetch\(|sendBeacon|XMLHttpRequest", m.group(0)), "[static] mountNotice 안에 분석·전송 호출이 있음")

    print(f"checks={n_checks[0]} fails={len(fails)}")
    for f in fails:
        print("FAIL", f)
    print("OK" if not fails else "VIOLATIONS")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "artifacts" / "designer" / "notice_popup"))
    sys.exit(run(ap.parse_args()))
