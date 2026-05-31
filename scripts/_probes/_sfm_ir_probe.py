#!/usr/bin/env python3
"""Probe 삼성화재 IR 실적자료 page: render SPA, dump candidate download rows."""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

URLS = [
    "https://www.samsungfire.com/vh/page/VH.REMK0044.do",
    "https://www.samsungfire.com/sfmi/ui/m/etcsv/market/ir/MO_IR_result_report.html",
]

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1400,3000")
opts.add_argument("--lang=ko-KR")
d = webdriver.Chrome(options=opts)
try:
    for url in URLS:
        print("=" * 70)
        print("URL:", url)
        try:
            d.get(url)
        except Exception as e:  # noqa: BLE001
            print("  get fail:", e)
            continue
        time.sleep(8)
        print("  title:", d.title)
        print("  cur_url:", d.current_url)
        # dump anything that looks like a download trigger
        for kw in ("다운로드", "엑셀", "XLS", "Excel", "PDF", "파일"):
            els = d.find_elements(By.XPATH, f"//*[contains(normalize-space(text()),'{kw}')]")
            if els:
                print(f"  -- text '{kw}': {len(els)} elements")
                for e in els[:8]:
                    try:
                        print(f"     <{e.tag_name}> '{e.text.strip()[:60]}'")
                    except Exception:  # noqa: BLE001
                        pass
        # anchors with file extensions
        anchors = d.find_elements(By.XPATH, "//a[@href]")
        fhrefs = [a.get_attribute("href") for a in anchors
                  if a.get_attribute("href") and
                  any(x in a.get_attribute("href").lower()
                      for x in (".xls", ".xlsx", ".pdf", "download", "filedown", "fileid"))]
        print(f"  -- file-like anchors: {len(fhrefs)}")
        for h in fhrefs[:15]:
            print("     ", h)
        # list-ish rows (titles)
        for sel in ("li", "tr", "div.board", "div.list"):
            rows = d.find_elements(By.CSS_SELECTOR, sel)
            titled = [r for r in rows if r.text.strip() and
                      ("FY" in r.text or "분기" in r.text or "실적" in r.text or "반기" in r.text)]
            if titled:
                print(f"  -- rows '{sel}': {len(titled)} with FY/분기/실적")
                for r in titled[:10]:
                    print("     |", r.text.strip().replace("\n", " | ")[:100])
                break
finally:
    d.quit()
