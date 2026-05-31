# -*- coding: utf-8 -*-
"""Probe Hanwha Life & Hanwha General Insurance IR pages with Selenium.
Render the SPA, dump nav links + any download (PDF/Excel) anchors/buttons.
"""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

CANDIDATES = [
    # Hanwha Life IR financial / earnings
    "https://company.hanwhalife.com/ko/investment/financial",
    "https://company.hanwhalife.com/ko/investment",
    # Hanwha General Insurance
    "https://www.hwgeneralins.com/main.do",
    "https://www.hwgeneralins.com/",
]


def probe(url):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,2400")
    opts.add_argument("--lang=ko-KR")
    d = webdriver.Chrome(options=opts)
    try:
        d.get(url)
        time.sleep(7)
        print(f"\n===== {url}")
        print("FINAL URL:", d.current_url)
        print("TITLE:", d.title)
        anchors = d.find_elements(By.TAG_NAME, "a")
        seen = set()
        for a in anchors:
            try:
                href = a.get_attribute("href") or ""
                txt = (a.text or "").strip().replace("\n", " ")
            except Exception:
                continue
            key = (href, txt)
            if key in seen:
                continue
            seen.add(key)
            low = (href + " " + txt).lower()
            if any(k in low for k in ["invest", "ir", "financial", "실적", "투자",
                                       "공시", "earning", ".pdf", ".xls", "자료",
                                       "discl"]):
                print(f"  A | {txt[:40]!r:42} | {href}")
        # buttons with download-ish text
        for b in d.find_elements(By.TAG_NAME, "button"):
            try:
                txt = (b.text or "").strip()
            except Exception:
                continue
            if txt and any(k in txt for k in ["다운", "엑셀", "XLS", "PDF", "자료"]):
                print(f"  BTN| {txt[:50]!r}")
    except Exception as e:
        print(f"ERROR {url}: {e}")
    finally:
        d.quit()


if __name__ == "__main__":
    for u in CANDIDATES:
        probe(u)
