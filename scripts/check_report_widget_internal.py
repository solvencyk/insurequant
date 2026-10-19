#!/usr/bin/env python3
"""오류 제보 내부 방문 제외 검사 (2026-10-19 신설, designer).

report-widget.js 가 iq_internal=1(주소 또는 localStorage)일 때 수집기로 제보 행을 보내지 않고,
그 외에는 종전처럼 보내는지, 어느 경우에도 양식·검증·완료 문구가 똑같이 동작하는지를 헤드리스 브라우저로 본다.
(download-survey.js 의 같은 규칙은 scripts/check_download_survey_internal.py 가 본다.)

**실제 구글 수집기·분석으로는 아무것도 나가지 않는다** - script.google.com / script.googleusercontent.com 과
googletagmanager / google-analytics 요청은 전부 Playwright route 로 가로채 개수만 세고 로컬 응답으로 끝낸다.
POST 뿐 아니라 fetch·beacon·그 밖의 어떤 메서드든 수집기 도메인으로 가면 1건으로 센다.

실행(저장소 루트에서):
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_report_widget_internal.py
종료코드: 0 = 통과 · 1 = 실패.
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
KEYS = {"kind", "_hp", "sheet", "company", "period", "detail"}
COLLECTOR = ("script.google.com", "script.googleusercontent.com")
ANALYTICS = ("googletagmanager.com", "google-analytics.com", "analytics.google.com")
BLOCK_STORAGE = (
    "(function(){var T=function(){throw new Error('storage blocked')};"
    "try{Object.defineProperty(window,'localStorage',{get:T,configurable:true});"
    "Object.defineProperty(window,'sessionStorage',{get:T,configurable:true});}catch(e){}})();"
)
DETAIL = "점검용 문구입니다 (실제 제보 아님)"
DONE_TEXT = "제출 완료 — 감사합니다"
CO_LABEL = "삼성생명보험"
QUARTER = "2026.1Q"


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


class Ctx:
    """브라우저 컨텍스트 + 수집기/분석 가로채기 카운터."""

    def __init__(self, br, init_scripts=()):
        self.ctx = br.new_context(viewport={"width": 1280, "height": 900})
        self.ctx.add_init_script("try{localStorage.setItem('iq_notice_seen','2026-3Q')}catch(e){}")
        for s in init_scripts:
            self.ctx.add_init_script(s)
        self.collector: list[dict] = []
        self.analytics = 0
        self.errs: list[str] = []
        self.ctx.route("**/*", self._route)

    def _route(self, route, request):
        url = request.url
        if any(d in url for d in COLLECTOR):
            if request.method == "POST":
                try:
                    self.collector.append(json.loads(request.post_data or "{}"))
                except Exception:
                    self.collector.append({"_unparsed": True})
            else:
                self.collector.append({"_method": request.method})
            route.fulfill(status=200, content_type="application/json", body='{"ok":true}',
                          headers={"access-control-allow-origin": "*"})
        elif any(d in url for d in ANALYTICS):
            self.analytics += 1
            route.fulfill(status=200, content_type="text/javascript", body="")
        else:
            route.continue_()

    def page(self):
        pg = self.ctx.new_page()
        pg.on("pageerror", lambda e: self.errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: self.errs.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        return pg

    def close(self):
        self.ctx.close()


def open_page(c: Ctx, port: int, query: str):
    pg = c.page()
    pg.goto(f"http://127.0.0.1:{port}/index.html{query}", wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_selector(".iq-report-fab", timeout=60000)
    pg.wait_for_timeout(500)
    return pg


def report_flow(pg) -> dict:
    """오류 제보 양식을 열어 회사·분기·내용을 채워 제출하고, 방문자에게 보이는 것을 돌려준다."""
    pg.locator(".iq-report-fab").click()
    pg.locator("#iqrep-form").wait_for(timeout=10000)

    # 빈 내용으로 제출하면 검증 문구가 뜨고 아무것도 보내지 않는다(내부/일반 공통).
    pg.locator("#iqrep-form button[type=submit]").click()
    pg.wait_for_timeout(300)
    validation_shown = pg.locator("#iqrep-error.show").count() == 1

    pg.locator(f"label[for='iqrep-co-{CO_LABEL}']").click()
    pg.locator(f"label[for='iqrep-q-{QUARTER}']").click()
    pg.locator("#iqrep-detail").fill(DETAIL)
    sheet = pg.locator("#iqrep-sheet").input_value()
    pg.locator("#iqrep-form button[type=submit]").click()
    pg.wait_for_function(
        "t => document.querySelector('#iqrep-form button[type=submit]').textContent === t", arg=DONE_TEXT, timeout=10000)
    done_shown = True
    # 1.2초 뒤 창이 닫히고 양식이 초기화된다
    pg.wait_for_function("() => document.getElementById('iqrep-backdrop').style.display === 'none'", timeout=10000)
    reset_ok = (pg.locator("#iqrep-detail").input_value() == ""
                and pg.locator("#iqrep-form button[type=submit]").text_content() == "제보 제출"
                and pg.locator("#iqrep-form button[type=submit]").is_enabled())
    return {"validation": validation_shown, "done": done_shown, "reset": reset_ok, "sheet": sheet}


def main() -> int:
    from playwright.sync_api import sync_playwright

    port = free_port()
    srv = start_server(port)
    fails: list[str] = []
    rows: list[str] = []

    def expect(tag: str, c: Ctx, n: int, ui: dict):
        ok = (len(c.collector) == n and ui["validation"] and ui["done"] and ui["reset"] and not c.errs)
        rows.append(f"{'OK  ' if ok else 'FAIL'} {tag}: 수집기 {len(c.collector)}건(기대 {n}) / "
                    f"검증문구 {ui['validation']} 완료문구 {ui['done']} 초기화 {ui['reset']} / 분석 가로챔 {c.analytics} / 콘솔오류 {len(c.errs)}")
        if not ok:
            fails.append(f"{tag}: 수집기 {len(c.collector)}건/기대 {n}, 화면 {ui}, 오류 {c.errs}")

    def check_payload(tag: str, x: dict, sheet: str):
        want = {"kind": "report", "_hp": "", "sheet": sheet, "company": CO_LABEL, "period": QUARTER, "detail": DETAIL}
        if set(x) != KEYS or x != want:
            fails.append(f"{tag}: 페이로드 이상 {x} (기대 {want})")
        if "KR0" in json.dumps(x, ensure_ascii=False):
            fails.append(f"{tag}: 페이로드에 회사코드 {x}")

    try:
        with sync_playwright() as p:
            br = p.chromium.launch()

            # (a) 주소 플래그: 0건, 화면 동작은 그대로
            c = Ctx(br)
            pg = open_page(c, port, "?iq_internal=1")
            expect("(a) ?iq_internal=1", c, 0, report_flow(pg))
            c.close()

            # (b) localStorage 만(주소 플래그 없음)
            c = Ctx(br, ["try{localStorage.setItem('iq_internal','1')}catch(e){}"])
            pg = open_page(c, port, "")
            expect("(b) localStorage iq_internal=1", c, 0, report_flow(pg))
            c.close()

            # (c) ?iq_internal=1 로 한 번 들어온 브라우저가 ?iq_internal=0 으로 플래그를 지운 뒤에는 1건
            c = Ctx(br)
            pg = open_page(c, port, "?iq_internal=1")
            flag1 = pg.evaluate("() => localStorage.getItem('iq_internal')")
            pg.goto(f"http://127.0.0.1:{port}/index.html?iq_internal=0", wait_until="domcontentloaded", timeout=120000)
            pg.wait_for_selector(".iq-report-fab", timeout=60000)
            flag0 = pg.evaluate("() => localStorage.getItem('iq_internal')")
            if flag1 != "1" or flag0 is not None:
                fails.append(f"(c) 플래그 설정/해제 이상: 1 뒤={flag1!r}, 0 뒤={flag0!r}")
            ui = report_flow(pg)
            expect("(c) ?iq_internal=0 뒤", c, 1, ui)
            if c.collector:
                check_payload("(c)", c.collector[0], ui["sheet"])
            c.close()

            # (d) 일반 방문
            c = Ctx(br)
            pg = open_page(c, port, "")
            ui = report_flow(pg)
            expect("(d) 일반 방문", c, 1, ui)
            if c.collector:
                check_payload("(d)", c.collector[0], ui["sheet"])
            c.close()

            # (e) 저장소 차단: 일반 방문은 1건, 주소 플래그면 0건
            c = Ctx(br, [BLOCK_STORAGE])
            pg = open_page(c, port, "")
            ui = report_flow(pg)
            expect("(e1) 저장소 차단 일반 방문", c, 1, ui)
            if c.collector:
                check_payload("(e1)", c.collector[0], ui["sheet"])
            c.close()
            c = Ctx(br, [BLOCK_STORAGE])
            pg = open_page(c, port, "?iq_internal=1")
            expect("(e2) 저장소 차단 + 주소 플래그", c, 0, report_flow(pg))
            c.close()

            # (f) 1 이 아닌 다른 값은 내부가 아니다 -> 1건
            for val in ("2", "", "true"):
                c = Ctx(br)
                pg = open_page(c, port, f"?iq_internal={val}")
                stored = pg.evaluate("() => localStorage.getItem('iq_internal')")
                if stored is not None:
                    fails.append(f"(f) ?iq_internal={val!r} 인데 localStorage 에 {stored!r} 가 저장됨")
                ui = report_flow(pg)
                expect(f"(f) ?iq_internal={val}", c, 1, ui)
                if c.collector:
                    check_payload(f"(f {val})", c.collector[0], ui["sheet"])
                c.close()

            br.close()
    finally:
        stop_server(srv)

    print("\n".join(rows))
    if fails:
        print("\n실패:")
        for f in fails:
            print(" -", f)
        return 1
    print("\n통과: 수집기 요청은 전부 가로채 개수만 셌고 실제 전송은 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
