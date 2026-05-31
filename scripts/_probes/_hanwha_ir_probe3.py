# -*- coding: utf-8 -*-
"""Probe Hanwha Life & Hanwha General Insurance IR earnings-release list pages.
Render the SPA, dump row text (publication quarter titles) and per-row
download anchors/buttons (xlsx / pdf) with href + onclick.
"""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.stdout.reconfigure(encoding="utf-8")

PAGES = [
    # Hanwha Life
    ("HLIFE_earnings", "https://company.hanwhalife.com/ko/investment/investor/earnings-release"),
    ("HLIFE_financial", "https://company.hanwhalife.com/ko/investment/financial"),
    ("HLIFE_invest", "https://company.hanwhalife.com/ko/investment"),
    # Hanwha General Insurance (한화손해보험 000370)
    ("HGI_finance07", "https://www.hwgeneralins.com/intro/ir/finance07.do"),
    ("HGI_irmain", "https://www.hwgeneralins.com/intro/ir/ir01.do"),
    ("HGI_main", "https://www.hwgeneralins.com/main.do"),
]


def probe(name, url):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,4000")
    opts.add_argument("--lang=ko-KR")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    d = webdriver.Chrome(options=opts)
    try:
        d.get(url)
        time.sleep(8)
        print(f"\n===== {name}  {url}")
        print("FINAL:", d.current_url, "| TITLE:", d.title, "| htmllen", len(d.page_source))
        # download-ish anchors/buttons
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
                                        "filedown", "factsheet", "fact", "excel"]):
                print(f"  {tag} | {txt[:40]!r:42} | href={href[:75]} | onclick={onclick[:80]}")
                cnt += 1
        print(f"  -> {cnt} download-ish elements")
        # row labels (publication quarters)
        rows = d.find_elements(By.XPATH, "//table//tr|//ul//li|//div[contains(@class,'list')]//*")
        labels = []
        seen = set()
        for r in rows[:120]:
            t = (r.text or "").strip().replace("\n", " ")
            if t and ("FY" in t or "분기" in t or "결산" in t or "실적" in t or "20" in t) and len(t) < 120:
                if t not in seen:
                    seen.add(t)
                    labels.append(t)
        for t in labels[:30]:
            print(f"  ROW| {t}")
    except Exception as e:
        print(f"ERROR {name}: {e}")
    finally:
        d.quit()


if __name__ == "__main__":
    for n, u in PAGES:
        probe(n, u)
