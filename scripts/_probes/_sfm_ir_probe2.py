#!/usr/bin/env python3
"""Probe 삼성화재 IR: map each list row -> its title + the xlsx/pdf download
clickable element. Check for pagination (older than FY24 1Q)."""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")
URL = "https://www.samsungfire.com/vh/page/VH.REMK0044.do"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,3000")
opts.add_argument("--lang=ko-KR")
d = webdriver.Chrome(options=opts)
try:
    d.get(URL)
    time.sleep(8)

    # pagination controls?
    print("== pagination candidates ==")
    for kw in ("더보기", "다음", "이전", "페이지", "more", "next"):
        els = d.find_elements(By.XPATH, f"//*[contains(normalize-space(text()),'{kw}')]")
        for e in els[:5]:
            print(f"  '{kw}': <{e.tag_name} class={e.get_attribute('class')}> '{e.text.strip()[:40]}'")
    # year filter / select?
    sels = d.find_elements(By.TAG_NAME, "select")
    print(f"== {len(sels)} <select> ==")
    for s in sels:
        opts_t = [o.text.strip() for o in s.find_elements(By.TAG_NAME, "option")]
        print("  options:", opts_t[:20])

    # map the xlsx buttons to their containing row title via onclick / parent
    print("== xlsx button details ==")
    xls = d.find_elements(By.XPATH, "//*[normalize-space(text())='xlsx다운로드']")
    print("  count:", len(xls))
    for i, b in enumerate(xls):
        oc = b.get_attribute("onclick") or ""
        href = b.get_attribute("href") or ""
        # climb up to a row that has FY in text
        node = b
        title = ""
        for _ in range(6):
            node = node.find_element(By.XPATH, "..")
            t = node.text.strip()
            if "FY" in t:
                title = t.split("\n")[0]
                break
        # the clickable ancestor (a or button)
        anc = b.find_element(By.XPATH, "./ancestor-or-self::a[1] | ./ancestor-or-self::button[1]") \
            if b.find_elements(By.XPATH, "./ancestor-or-self::a | ./ancestor-or-self::button") else b
        print(f"  [{i}] title='{title}' onclick='{oc[:80]}' href='{href[:80]}' anc=<{anc.tag_name}> ancoc='{(anc.get_attribute('onclick') or '')[:80]}'")
finally:
    d.quit()
