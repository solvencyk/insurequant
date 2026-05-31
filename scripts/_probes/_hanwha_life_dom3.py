# -*- coding: utf-8 -*-
"""Identify the clickable element type for 발표자료 / 팩트시트 inside a row li."""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")
URL = "https://company.hanwhalife.com/ko/investment/investor/earnings-release"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,5000")
opts.add_argument("--lang=ko-KR")
d = webdriver.Chrome(options=opts)
try:
    d.get(URL)
    time.sleep(9)
    rows = d.find_elements(By.CSS_SELECTOR, "ul.list-outer > li")
    print("rows:", len(rows))
    # take row index 1 (first data row)
    row = rows[1]
    print("ROW txt:", repr((row.text or "").replace("\n", " ")))
    # find any descendant whose text is 발표자료 or 팩트시트
    for label in ["발표자료", "팩트시트"]:
        els = row.find_elements(By.XPATH, f".//*[normalize-space(text())='{label}']")
        print(f"\n  '{label}': {len(els)} matches")
        for e in els:
            tag = e.tag_name
            cls = e.get_attribute("class") or ""
            oc = e.get_attribute("onclick") or ""
            href = e.get_attribute("href") or ""
            print(f"    <{tag} class={cls[:40]!r} onclick={oc[:40]!r} href={href[:50]!r}>")
            # also parent
            p = e.find_element(By.XPATH, "..")
            print(f"      parent <{p.tag_name} class={(p.get_attribute('class') or '')[:40]!r} "
                  f"onclick={(p.get_attribute('onclick') or '')[:40]!r}>")
finally:
    d.quit()
