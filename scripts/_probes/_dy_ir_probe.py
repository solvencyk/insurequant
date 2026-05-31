#!/usr/bin/env python3
"""동양생명 IR single-page probe with eager page load + network capture.
Use page_load_strategy='eager' so .get() returns before all subresources finish
(the earlier probe hung on a never-completing load)."""
import json
import re
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.myangel.co.kr/Company/Ir/CoIrMat"


def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,3000")
    opts.page_load_strategy = "eager"
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=opts)


d = driver()
d.set_page_load_timeout(40)
try:
    try:
        d.get(URL)
    except Exception as e:
        print("get() warn:", e)
    time.sleep(6)
    print(f"URL: {URL} -> {d.current_url}")
    print("TITLE:", d.title)
    # network
    try:
        logs = d.get_log("performance")
        reqs = set()
        for entry in logs:
            msg = json.loads(entry["message"])["message"]
            if msg["method"] in ("Network.requestWillBeSent", "Network.responseReceived"):
                p = msg.get("params", {})
                u = (p.get("request", {}) or {}).get("url") or \
                    (p.get("response", {}) or {}).get("url") or ""
                if u and any(k in u for k in
                             ["IrM", "irm", "List", "list", "paging", "ajax", "Json", "json",
                              "Select", ".do", ".jsp", "file", "File", "Ir/", "ir/"]):
                    reqs.add(u)
        print("-- candidate XHR/doc requests --")
        for u in sorted(reqs):
            print("   ", u[:170])
    except Exception as e:
        print("perf log err", e)
    ifr = d.find_elements(By.TAG_NAME, "iframe")
    print("iframes:", [f.get_attribute("src") for f in ifr])
    body = ""
    try:
        body = d.find_element(By.TAG_NAME, "body").text
    except Exception:
        pass
    print("-- body text (first 1800) --")
    print(body[:1800])
    # anchors / onclick
    els = d.find_elements(By.XPATH, "//a[@onclick] | //button[@onclick] | //a[@href]")
    print("-- anchors (download-ish) --")
    n = 0
    for e in els:
        txt = (e.text or "").strip().replace("\n", " ")
        oc = e.get_attribute("onclick") or ""
        href = e.get_attribute("href") or ""
        if any(k in (txt + oc + href) for k in
               ["Fact", "실적", "다운", "Down", "file", "File", "20", "fn", ".xls", ".pdf", "fileNo", "atch"]):
            if txt or oc:
                print(f"   txt={txt[:55]!r} oc={oc[:130]!r} href={href[:110]!r}")
                n += 1
        if n > 60:
            break
finally:
    d.quit()
