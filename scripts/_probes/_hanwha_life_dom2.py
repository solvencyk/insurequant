# -*- coding: utf-8 -*-
"""Find the true row container that pairs a title (FY...) with its
발표자료/팩트시트 buttons in the Hanwha Life earnings list."""
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
    # locate a button labelled 팩트시트, walk up ancestors, print each ancestor's
    # tag/class and whether it contains an 'FY' title text.
    btns = d.find_elements(By.XPATH, "//button[normalize-space(text())='팩트시트']")
    print("팩트시트 buttons:", len(btns))
    if btns:
        node = btns[0]
        for lvl in range(8):
            node = node.find_element(By.XPATH, "..")
            txt = (node.text or "").replace("\n", " ").strip()
            cls = node.get_attribute("class") or ""
            tag = node.tag_name
            has_fy = "FY" in txt
            print(f"  L{lvl} <{tag} class={cls[:35]!r}> hasFY={has_fy} txt={txt[:70]!r}")
    # Try: the whole list. Find the ancestor <ul>/<table> and dump its row children.
    print("\n=== try ul.list rows ===")
    uls = d.find_elements(By.XPATH, "//ul[contains(@class,'list')]")
    for ul in uls:
        kids = ul.find_elements(By.XPATH, "./li")
        if not kids:
            continue
        cls = ul.get_attribute("class") or ""
        print(f"UL class={cls[:40]!r} -> {len(kids)} li children")
        for k in kids[:4]:
            print("   LI:", repr((k.text or "").replace("\n", " ")[:80]))
    # Also: maybe each visual row is a div with multiple list-col li inside
    print("\n=== rows as div containing FY + buttons ===")
    cand = d.find_elements(
        By.XPATH,
        "//*[contains(., 'FY2026 1분기') and .//button[normalize-space(text())='팩트시트']]")
    # smallest such ancestor
    if cand:
        smallest = min(cand, key=lambda e: len(e.text or ""))
        print("smallest tag", smallest.tag_name, "class",
              (smallest.get_attribute('class') or '')[:40],
              "txt", repr((smallest.text or '').replace('\n',' ')[:90]))
finally:
    d.quit()
