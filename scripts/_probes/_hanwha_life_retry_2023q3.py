# -*- coding: utf-8 -*-
"""Retry the single missing FY2023 3분기 팩트시트 for Hanwha Life."""
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")
URL = "https://company.hanwhalife.com/ko/investment/investor/earnings-release"
STAGE = Path("data/ir/decks/hanwha_life").resolve()
IGNORE = (".crdownload", ".tmp", ".htm", ".html", ".json")

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,5000")
opts.add_argument("--lang=ko-KR")
opts.add_experimental_option("prefs", {
    "download.default_directory": str(STAGE),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "plugins.always_open_pdf_externally": True,
})
d = webdriver.Chrome(options=opts)
try:
    d.get(URL)
    time.sleep(9)
    d.execute_cdp_cmd("Page.setDownloadBehavior",
                      {"behavior": "allow", "downloadPath": str(STAGE)})
    # go to page 2
    nxt = d.find_elements(By.XPATH, "//button[normalize-space(text())='2']")
    if nxt:
        d.execute_script("arguments[0].click();", nxt[0])
        time.sleep(5)
    rows = d.find_elements(By.CSS_SELECTOR, "ul.list-outer > li")
    target_btn = None
    for r in rows:
        txt = (r.text or "").strip().replace("\n", " ")
        if "FY2023 3분기" in txt:
            for b in r.find_elements(By.TAG_NAME, "button"):
                if "팩트" in (b.text or ""):
                    target_btn = b
            break
    if target_btn is None:
        print("FY2023 3분기 팩트시트 button not found")
        sys.exit(1)
    before = {f.name for f in STAGE.glob("*")}
    d.execute_script("arguments[0].scrollIntoView({block:'center'});", target_btn)
    time.sleep(0.5)
    d.execute_script("arguments[0].click();", target_btn)
    got = None
    for _ in range(150):
        time.sleep(1)
        if any(f.name.endswith(".crdownload") for f in STAGE.glob("*")):
            continue
        new = [f for f in STAGE.glob("*")
               if f.name not in before
               and not any(f.name.lower().endswith(e) for e in IGNORE)]
        if new:
            got = max(new, key=lambda p: p.stat().st_mtime)
            break
    if got:
        target = STAGE / f"FY2023_Q3_factsheet_{got.name}"
        for _ in range(10):
            try:
                got.rename(target)
                break
            except PermissionError:
                time.sleep(1)
        print("OK", target.name, target.stat().st_size, "bytes")
    else:
        print("TIMEOUT again")
finally:
    d.quit()
