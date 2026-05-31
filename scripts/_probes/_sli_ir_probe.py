#!/usr/bin/env python3
"""Download 삼성생명 latest IR fact sheet (XLS) via Selenium click; report files."""
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")
URL = "https://www.samsunglife.com/individual/display/invest/PDK-IRIVI015220M"
DL = Path("data/ir/decks/samsung_life").resolve()
DL.mkdir(parents=True, exist_ok=True)

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,2400")
opts.add_experimental_option("prefs", {
    "download.default_directory": str(DL),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
})
d = webdriver.Chrome(options=opts)
try:
    d.get(URL)
    time.sleep(7)
    # enable downloads in headless
    d.execute_cdp_cmd("Page.setDownloadBehavior",
                      {"behavior": "allow", "downloadPath": str(DL)})
    # Dump rows: each IR item likely has a title + XLS/PDF buttons. Find XLS buttons
    # and their nearest title text.
    xls_btns = d.find_elements(By.XPATH, "//*[normalize-space(text())='XLS 다운로드']")
    print("XLS buttons found:", len(xls_btns))
    # title of first few rows
    for i, b in enumerate(xls_btns[:6]):
        try:
            row = b.find_element(By.XPATH, "./ancestor::*[self::li or self::tr or self::div][1]")
            print(f"  [{i}] row text: {row.text.strip()[:80]!r}")
        except Exception as e:
            print(f"  [{i}] (no row) {e}")
    before = {p.name for p in DL.glob('*')}
    # click the FIRST (latest) XLS button → latest fact sheet (full history)
    if xls_btns:
        d.execute_script("arguments[0].scrollIntoView({block:'center'});", xls_btns[0])
        d.execute_script("arguments[0].click();", xls_btns[0])
        # wait for a new xlsx (no .crdownload)
        for _ in range(60):
            time.sleep(1)
            files = list(DL.glob('*'))
            if any(f.name.endswith('.crdownload') for f in files):
                continue
            new = [f for f in files if f.name not in before and f.suffix.lower() in ('.xlsx', '.xls')]
            if new:
                print("DOWNLOADED:", [(f.name, f.stat().st_size) for f in new])
                break
        else:
            print("download timeout; dir now:", [p.name for p in DL.glob('*')])
finally:
    d.quit()
