# -*- coding: utf-8 -*-
"""Headless verification for inbox/designer/20260921T0430Z (header toggles ticket).
Throwaway probe script per CLAUDE.md conventions (scripts/_probes/). Not a gate,
not imported anywhere. Run: full python path, PYTHONIOENCODING=utf-8.
"""
import json
import sys
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
ART = REPO / "artifacts" / "designer_shots" / "20260921_header_toggles"
ART.mkdir(parents=True, exist_ok=True)

from playwright.sync_api import sync_playwright  # noqa: E402

results = {}
console_errors = []
page_errors = []


def run():
    handler = partial(SimpleHTTPRequestHandler, directory=str(REPO))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            # ---- 1) desktop 1400px + mobile 375px screenshots, header select visible after scroll ----
            for label, vp in [("desktop_1400", {"width": 1400, "height": 900}), ("mobile_375", {"width": 375, "height": 812})]:
                page = browser.new_page(viewport=vp)
                page.on("console", lambda msg: console_errors.append(f"[{label}] {msg.type}: {msg.text}") if msg.type == "error" else None)
                page.on("pageerror", lambda exc: page_errors.append(f"[{label}] {exc}"))
                page.goto(f"{base}/K-ICS.html?iq_internal=1")
                page.wait_for_timeout(600)
                page.screenshot(path=str(ART / f"{label}_top.png"))
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(300)
                header_select_visible = page.eval_on_selector("#company", "el => { const r = el.getBoundingClientRect(); return r.top >= 0 && r.top < window.innerHeight && r.bottom > 0; }")
                page.screenshot(path=str(ART / f"{label}_scrolled.png"))
                results[f"1_{label}_company_visible_after_scroll_2000px"] = header_select_visible
                page.close()

            # ---- 2,3,4,5) functional checks on desktop ----
            page = browser.new_page(viewport={"width": 1400, "height": 900})
            page.on("console", lambda msg: console_errors.append(f"[func] {msg.type}: {msg.text}") if msg.type == "error" else None)
            page.on("pageerror", lambda exc: page_errors.append(f"[func] {exc}"))
            page.goto(f"{base}/K-ICS.html?iq_internal=1")
            page.wait_for_timeout(500)

            # 2) select company -> default toggle "분기" -> chart+table render without touching period
            page.select_option("#company", value="라이나생명보험")
            page.wait_for_timeout(500)
            period_value = page.eval_on_selector("#period", "el => el.value")
            row_count = page.eval_on_selector_all("#table-container table tbody tr", "els => els.length")
            canvas_visible = page.eval_on_selector("#chart", "el => getComputedStyle(el).display !== 'none'")
            results["2_default_period_value"] = period_value
            results["2_table_row_count"] = row_count
            results["2_chart_visible"] = canvas_visible
            page.screenshot(path=str(ART / "2_lina_default_quarter.png"))

            # 3) toggle to 연도 -> table switches to year columns
            page.click("#period-toggle .seg-btn[data-value='year']")
            page.wait_for_timeout(500)
            year_period_value = page.eval_on_selector("#period", "el => el.value")
            year_headers = page.eval_on_selector_all("#table-container table thead th", "els => els.map(e => e.textContent.trim())")
            results["3_period_value_after_year_click"] = year_period_value
            results["3_year_table_headers"] = year_headers
            page.screenshot(path=str(ART / "3_lina_year_toggle.png"))

            # back to quarter for cleanliness of next checks
            page.click("#period-toggle .seg-btn[data-value='quarter']")
            page.wait_for_timeout(400)

            # 4) 적용후 toggle changes values (한화생명 2024.4Q pre != post)
            page.select_option("#company", value="한화생명")
            page.wait_for_timeout(500)
            page.click("#transition-toggle .seg-btn[data-value='적용전']")
            page.wait_for_timeout(300)
            pre_text = page.eval_on_selector_all(
                "#table-container table tbody tr",
                "els => els.map(e => e.textContent.trim())"
            )
            page.click("#transition-toggle .seg-btn[data-value='적용후']")
            page.wait_for_timeout(400)
            post_text = page.eval_on_selector_all(
                "#table-container table tbody tr",
                "els => els.map(e => e.textContent.trim())"
            )
            transition_mode_value = page.eval_on_selector("#transition-mode", "el => el.value")
            results["4_transition_mode_value_after_post_click"] = transition_mode_value
            results["4_pre_vs_post_differ"] = pre_text != post_text
            page.screenshot(path=str(ART / "4_hanwha_life_post_toggle.png"))
            # reset transition to 적용전 for cleanliness
            page.click("#transition-toggle .seg-btn[data-value='적용전']")
            page.wait_for_timeout(300)

            # keyboard check: focus period-toggle active btn, press ArrowRight, Space/Enter behavior
            page.focus("#period-toggle .seg-btn.active")
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(300)
            kb_period_value = page.eval_on_selector("#period", "el => el.value")
            kb_active_label = page.eval_on_selector("#period-toggle .seg-btn.active", "el => el.textContent.trim()")
            results["kb_arrowright_period_value"] = kb_period_value
            results["kb_arrowright_active_label"] = kb_active_label
            # move back with ArrowLeft
            page.keyboard.press("ArrowLeft")
            page.wait_for_timeout(300)
            results["kb_arrowleft_period_value"] = page.eval_on_selector("#period", "el => el.value")

            page.close()

            # ---- 5) URL param entry ----
            page = browser.new_page(viewport={"width": 1400, "height": 900})
            page.on("console", lambda msg: console_errors.append(f"[urlparam] {msg.type}: {msg.text}") if msg.type == "error" else None)
            page.on("pageerror", lambda exc: page_errors.append(f"[urlparam] {exc}"))
            page.goto(f"{base}/K-ICS.html?company=%EB%9D%BC%EC%9D%B4%EB%82%98%EC%83%9D%EB%AA%85%EB%B3%B4%ED%97%98&period=year&iq_internal=1")
            page.wait_for_timeout(600)
            results["5_company_value"] = page.eval_on_selector("#company", "el => el.value")
            results["5_period_value"] = page.eval_on_selector("#period", "el => el.value")
            results["5_period_toggle_active_label"] = page.eval_on_selector("#period-toggle .seg-btn.active", "el => el.textContent.trim()")
            results["5_period_toggle_year_aria_checked"] = page.eval_on_selector("#period-toggle .seg-btn[data-value='year']", "el => el.getAttribute('aria-checked')")
            page.screenshot(path=str(ART / "5_url_param_year.png"))
            page.close()

            browser.close()
    finally:
        httpd.shutdown()


run()

results["console_errors"] = console_errors
results["page_errors"] = page_errors

out_path = REPO / "data" / "_derived" / "_probe_20260921_header_toggles_verify.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(json.dumps(results, ensure_ascii=False, indent=2))
