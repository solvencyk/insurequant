# -*- coding: utf-8 -*-
"""Probe the actual earnings-release list pages for both Hanwha companies.
Dump row text + per-row download anchors/buttons (PDF vs Excel) and onclick.
"""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

PAGES = [
    ("HLIFE_earnings", "https://company.hanwhalife.com/ko/investment/investor/earnings-release"),
    ("HGI_finance07", "https://www.hwgeneralins.com/intro/ir/finance07.do"),
    ("HGI_biz02", "https://www.hwgeneralins.com/intro/ir/biz02.do"),
    ("HGI_generallist", "https://www.hwgeneralins.com/intro/ir/general-list.do"),
    ("HGI_invest", "https://www.hwgeneralins.com/intro/company/invest.do"),
]


def probe(name, url):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,3000")
    opts.add_argument("--lang=ko-KR")
    d = webdriver.Chrome(options=opts)
    try:
        d.get(url)
        time.sleep(8)
        print(f"\n===== {name} {url}")
        print("FINAL:", d.current_url, "| TITLE:", d.title)
        # any anchors / buttons with download-ish attributes
        els = d.find_elements(By.XPATH, "//a|//button")
        cnt = 0
        for e in els:
            try:
                tag = e.tag_name
                href = e.get_attribute("href") or ""
                onclick = e.get_attribute("onclick") or ""
                txt = (e.text or "").strip().replace("\n", " ")
            except Exception:
                continue
            blob = (href + " " + onclick + " " + txt).lower()
            if any(k in blob for k in [".pdf", ".xls", "download", "엑셀", "다운",
                                        "filedown", "factsheet", "fact"]):
                print(f"  {tag} | {txt[:45]!r:47} | href={href[:80]} | onclick={onclick[:90]}")
                cnt += 1
        print(f"  -> {cnt} download-ish elements")
        # Dump table/list row labels (publication quarters)
        rows = d.find_elements(By.XPATH, "//table//tr|//ul//li")
        labels = []
        for r in rows[:40]:
            t = (r.text or "").strip().replace("\n", " ")
            if t and any(c.isdigit() for c in t) and len(t) < 120:
                labels.append(t)
        for t in labels[:25]:
            print(f"  ROW| {t}")
    except Exception as e:
        print(f"ERROR {name}: {e}")
    finally:
        d.quit()


if __name__ == "__main__":
    for n, u in PAGES:
        probe(n, u)
