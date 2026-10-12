#!/usr/bin/env python3
"""공유 버튼 사용 기록 검사 (2026-10-12 신설, designer).

theme.js 의 shLog 가 공유 동작마다 IQ_FORMS.submit('share', {...}) 를 올바른 페이로드로 한 번만 보내는지,
iq_internal=1 이면 0 건인지, 연타 디바운스, forms-config.js 가 없을 때 오류 없음을 헤드리스 브라우저로 본다.

**실제 구글 수집기로는 아무것도 보내지 않는다** — 수집기 URL(script.google.com) 요청을 Playwright route 로 가로채
본문만 캡처하고 {"ok":true} 로 응답한다. (가로채기가 실패하면 즉시 중단하도록 URL 매칭이 느슨하다.)

실행(저장소 루트에서):
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_share_log.py
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
PAGES = [("K-ICS.html", "K-ICS"), ("IFRS17.html", "IFRS17"), ("compare.html", "compare"), ("index.html", "index")]
KEYS = {"kind", "_hp", "page", "action", "section", "company", "device", "result"}


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


def main() -> int:
    from playwright.sync_api import sync_playwright

    port = free_port()
    srv = start_server(port)
    fails: list[str] = []
    try:
        with sync_playwright() as p:
            br = p.chromium.launch()
            for viewport, (w, h) in (("desktop", (1280, 900)), ("mobile", (375, 812))):
                for fname, page_key in PAGES:
                    for mode in ("normal", "internal", "noconfig"):
                        ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=(viewport == "mobile"),
                                             is_mobile=(viewport == "mobile"))
                        pg = ctx.new_page()
                        posts: list[dict] = []
                        errs: list[str] = []
                        pg.on("pageerror", lambda e, errs=errs: errs.append(str(e)))
                        pg.on("console", lambda m, errs=errs: errs.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
                        pg.on("dialog", lambda d: d.accept())

                        def collector(route, request, posts=posts):
                            if request.method == "POST":
                                posts.append(json.loads(request.post_data or "{}"))
                            route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
                        pg.route("**/script.google.com/**", collector)
                        pg.route("**/script.googleusercontent.com/**", collector)
                        if mode == "noconfig":
                            pg.route("**/forms-config.js", lambda r: r.abort())
                        q = "?iq_internal=1" if mode == "internal" else ""
                        if fname == "K-ICS.html":
                            q += ("&" if q else "?") + "company=삼성생명"
                        if fname == "IFRS17.html":
                            q += ("&" if q else "?") + "company=삼성생명"
                        if fname == "compare.html":
                            q += ("&" if q else "?") + "c=삼성생명,한화생명,교보생명"
                        pg.goto(f"http://127.0.0.1:{port}/{fname}{q}", wait_until="domcontentloaded", timeout=300000)
                        pg.wait_for_timeout(2500)
                        tag = f"{viewport}/{fname}/{mode}"
                        if fname == "K-ICS.html":
                            pg.locator("#company").select_option(label="삼성생명")
                            pg.wait_for_timeout(2500)
                        secs = pg.locator(".iq-sec-share")
                        # 1) 링크 복사 (+ 연타)
                        pg.locator("#iqShareBtn").click()
                        pg.locator("#iqShareMenu button", has_text="링크 복사").click()
                        pg.wait_for_timeout(200)
                        pg.locator("#iqShareBtn").click()
                        pg.locator("#iqShareMenu button", has_text="링크 복사").click()   # 1.5초 안 연타
                        pg.wait_for_timeout(300)
                        n_link = len([x for x in posts if x.get("action") == "link_copy"])
                        # 2) 페이지 전체 스크린샷
                        pg.locator("#iqShareBtn").click()
                        pg.locator("#iqShareMenu button", has_text="페이지 전체").click()
                        pg.wait_for_function("() => !document.getElementById('iqToast') || document.getElementById('iqToast').textContent.indexOf('만드는 중') < 0", timeout=90000)
                        pg.wait_for_timeout(1500)
                        # 3) 섹션 스크린샷(첫 버튼)
                        n_sec_btn = secs.count()
                        if n_sec_btn:
                            secs.first.scroll_into_view_if_needed()
                            secs.first.click()
                            pg.wait_for_function("() => !document.querySelector('.iq-sec-share[aria-busy]')", timeout=90000)
                            pg.wait_for_timeout(1500)
                        shots = [x for x in posts if x.get("action") in ("page_screenshot", "section_screenshot")]
                        want_internal_zero = (mode == "internal" or mode == "noconfig")
                        if mode == "normal":
                            if n_link != 1:
                                fails.append(f"{tag}: link_copy 전송 {n_link}건(기대 1, 연타 디바운스)")
                            if len([x for x in shots if x["action"] == "page_screenshot"]) != 1:
                                fails.append(f"{tag}: page_screenshot 전송 수 이상 {shots}")
                            if n_sec_btn and len([x for x in shots if x["action"] == "section_screenshot"]) != 1:
                                fails.append(f"{tag}: section_screenshot 전송 수 이상 {shots}")
                            for x in posts:
                                if set(x) != KEYS or x["kind"] != "share" or x["page"] != page_key:
                                    fails.append(f"{tag}: 페이로드 키/값 이상 {x}")
                                if x["device"] != ("touch" if viewport == "mobile" else "pointer"):
                                    fails.append(f"{tag}: device 이상 {x}")
                                if x["result"] not in ("ok", "truncated", "error"):
                                    fails.append(f"{tag}: result 이상 {x}")
                            for x in posts:
                                if x["action"] == "section_screenshot" and not x["section"]:
                                    fails.append(f"{tag}: 섹션 이름 빠짐 {x}")
                                if x["action"] != "section_screenshot" and x["section"]:
                                    fails.append(f"{tag}: 섹션이 아닌데 section 채워짐 {x}")
                            print(f"[{tag}] posts={len(posts)} sec_buttons={n_sec_btn} ->",
                                  json.dumps(posts[:3], ensure_ascii=False))
                        elif want_internal_zero and posts:
                            fails.append(f"{tag}: 전송 0 이어야 하는데 {len(posts)}건 {posts}")
                        if errs:
                            fails.append(f"{tag}: 콘솔/페이지 오류 {errs[:3]}")
                        if mode != "normal":
                            print(f"[{tag}] posts={len(posts)} errors={len(errs)}")
                        ctx.close()
            br.close()
    finally:
        stop_server(srv)
    print("FAIL" if fails else "PASS")
    for f in fails:
        print(" -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
