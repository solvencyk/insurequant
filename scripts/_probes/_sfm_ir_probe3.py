#!/usr/bin/env python3
"""Probe 삼성화재 IR pagination: enumerate every page's row titles."""
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


def page_titles():
    xls = d.find_elements(By.XPATH, "//*[normalize-space(text())='xlsx다운로드']")
    titles = []
    for b in xls:
        node = b
        t = ""
        for _ in range(6):
            node = node.find_element(By.XPATH, "..")
            if "FY" in node.text:
                t = node.text.strip().split("\n")[0]
                break
        titles.append(t)
    return titles


try:
    d.get(URL)
    time.sleep(8)
    # page number buttons?
    pager = d.find_elements(By.CSS_SELECTOR, ".pagination a, .paging a, nav button, .pagination button")
    print("pager els:", [(p.tag_name, p.text.strip(), p.get_attribute('class')) for p in pager][:30])

    seen_pages = []
    for pg in range(8):
        titles = page_titles()
        print(f"-- page {pg+1}: {titles}")
        seen_pages.append(titles)
        nxt = d.find_elements(By.CSS_SELECTOR, "button.btn-next")
        if not nxt:
            print("  no next button")
            break
        nb = nxt[0]
        if not nb.is_enabled() or nb.get_attribute("disabled"):
            print("  next disabled")
            break
        prev_first = titles[0] if titles else None
        d.execute_script("arguments[0].click();", nb)
        time.sleep(4)
        new_titles = page_titles()
        if new_titles == titles or (new_titles and new_titles[0] == prev_first):
            print("  page did not change -> end")
            break
finally:
    d.quit()
