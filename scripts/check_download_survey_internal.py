#!/usr/bin/env python3
"""다운로드 방명록 내부 방문 제외 검사 (2026-10-19 신설, designer).

download-survey.js 가 iq_internal=1(주소 또는 localStorage)일 때 수집기로 방명록 행을 보내지 않고,
그 외에는 종전처럼 보내는지, 어느 경우에도 다운로드 파일이 내려가는지를 헤드리스 브라우저로 본다.

**실제 구글 수집기·분석으로는 아무것도 나가지 않는다** - script.google.com / script.googleusercontent.com 과
googletagmanager / google-analytics 요청은 전부 Playwright route 로 가로채 개수만 세고 로컬 응답으로 끝낸다.

실행(저장소 루트에서):
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_download_survey_internal.py
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
KEYS = {"kind", "_hp", "affiliation", "department", "sector", "sheets", "purpose", "consent"}
COLLECTOR = ("script.google.com", "script.googleusercontent.com")
ANALYTICS = ("googletagmanager.com", "google-analytics.com", "analytics.google.com")
BLOCK_STORAGE = (
    "(function(){var T=function(){throw new Error('storage blocked')};"
    "try{Object.defineProperty(window,'localStorage',{get:T,configurable:true});"
    "Object.defineProperty(window,'sessionStorage',{get:T,configurable:true});}catch(e){}})();"
)


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
        self.ctx = br.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
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
    pg.wait_for_function("() => typeof XLSX !== 'undefined'", timeout=60000)
    pg.wait_for_timeout(800)
    return pg


def full_flow(pg) -> str:
    """처음 방문 설문(전체 양식)을 채워 제출하고 내려받은 파일명을 돌려준다."""
    pg.locator("#downloadMasterBtn").click()
    pg.locator("#iqdl-form").wait_for(timeout=10000)
    pg.locator("#iqdl-form .iq-combo input").first.fill("테스트소속")
    pg.locator("#iqdl-form input[type=checkbox][value]").first.check()
    pg.locator("#iqdl-consent").check()
    with pg.expect_download(timeout=60000) as d:
        pg.locator("#iqdl-form button[type=submit]").click()
    name = d.value.suggested_filename
    pg.wait_for_function("() => document.getElementById('iqdl-backdrop').style.display === 'none'", timeout=10000)
    return name


def slim_flow(pg) -> str:
    """재방문(방명록 생략) 창에서 시트를 고르고 내려받는다."""
    pg.locator("#downloadMasterBtn").click()
    pg.locator("#iqdl-backdrop form").wait_for(timeout=10000)
    pg.locator("#iqdl-backdrop input[type=checkbox][value]").first.check()
    with pg.expect_download(timeout=60000) as d:
        pg.locator("#iqdl-backdrop button[type=submit]").click()
    name = d.value.suggested_filename
    pg.wait_for_function("() => document.getElementById('iqdl-backdrop').style.display === 'none'", timeout=10000)
    return name


def main() -> int:
    from playwright.sync_api import sync_playwright

    port = free_port()
    srv = start_server(port)
    fails: list[str] = []
    rows: list[str] = []

    def expect(tag: str, c: Ctx, n: int, dl: str):
        ok = len(c.collector) == n and dl.endswith(".xlsx") and not c.errs
        rows.append(f"{'OK  ' if ok else 'FAIL'} {tag}: 수집기 {len(c.collector)}건(기대 {n}) / 다운로드 {dl} / 분석 가로챔 {c.analytics} / 콘솔오류 {len(c.errs)}")
        if not ok:
            fails.append(f"{tag}: 수집기 {len(c.collector)}건/기대 {n}, 다운로드 {dl!r}, 오류 {c.errs}")

    def check_payload(tag: str, x: dict, consent: str):
        if set(x) != KEYS or x.get("kind") != "download" or x.get("_hp") != "" or x.get("consent") != consent:
            fails.append(f"{tag}: 페이로드 이상 {x}")
        if "KR0" in json.dumps(x, ensure_ascii=False):
            fails.append(f"{tag}: 페이로드에 회사코드 {x}")

    try:
        with sync_playwright() as p:
            br = p.chromium.launch()

            # (a) 주소 플래그: 전체 설문 -> 재방문 창 둘 다 0건
            c = Ctx(br)
            pg = open_page(c, port, "?iq_internal=1")
            expect("(a1) ?iq_internal=1 전체 설문", c, 0, full_flow(pg))
            expect("(a2) ?iq_internal=1 재방문 창", c, 0, slim_flow(pg))
            c.close()

            # (b) localStorage 만(주소 플래그 없음)
            c = Ctx(br, ["try{localStorage.setItem('iq_internal','1')}catch(e){}"])
            pg = open_page(c, port, "")
            expect("(b1) localStorage iq_internal=1 전체 설문", c, 0, full_flow(pg))
            expect("(b2) localStorage iq_internal=1 재방문 창", c, 0, slim_flow(pg))
            c.close()

            # (c) ?iq_internal=0 이 플래그를 지운 뒤 다음 설문은 1건
            c = Ctx(br)
            pg = open_page(c, port, "?iq_internal=1")
            flag1 = pg.evaluate("() => localStorage.getItem('iq_internal')")
            pg.goto(f"http://127.0.0.1:{port}/index.html?iq_internal=0", wait_until="domcontentloaded", timeout=120000)
            pg.wait_for_function("() => typeof XLSX !== 'undefined'", timeout=60000)
            flag0 = pg.evaluate("() => localStorage.getItem('iq_internal')")
            if flag1 != "1" or flag0 is not None:
                fails.append(f"(c) 플래그 설정/해제 이상: 1 뒤={flag1!r}, 0 뒤={flag0!r}")
            expect("(c1) ?iq_internal=0 뒤 전체 설문", c, 1, full_flow(pg))
            if c.collector:
                check_payload("(c1)", c.collector[0], "동의함")
            expect("(c2) ?iq_internal=0 뒤 재방문 창", c, 2, slim_flow(pg))
            if len(c.collector) == 2:
                check_payload("(c2)", c.collector[1], "재방문(방명록 생략)")
            c.close()

            # (d) 일반 방문
            c = Ctx(br)
            pg = open_page(c, port, "")
            expect("(d1) 일반 방문 전체 설문", c, 1, full_flow(pg))
            if c.collector:
                check_payload("(d1)", c.collector[0], "동의함")
                if c.collector[0].get("affiliation") != "테스트소속":
                    fails.append(f"(d1) affiliation 이상 {c.collector[0]}")
            expect("(d2) 일반 방문 재방문 창", c, 2, slim_flow(pg))
            c.close()

            # (e) 저장소 차단
            c = Ctx(br, [BLOCK_STORAGE])
            pg = open_page(c, port, "")
            expect("(e1) 저장소 차단 일반 방문", c, 1, full_flow(pg))
            c.close()
            c = Ctx(br, [BLOCK_STORAGE])
            pg = open_page(c, port, "?iq_internal=1")
            expect("(e2) 저장소 차단 + 주소 플래그", c, 0, full_flow(pg))
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
